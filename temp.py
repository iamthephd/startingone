import concurrent.futures
from typing import Dict, Tuple, List
from langchain.prompts import PromptTemplate

class CommentaryGenerator:
    """
    Generates financial commentary from structured data using a simple LLM.
    
    The class processes financial data in the format:
    {
        ("Category", "Type", value): {"Reason1": value1, "Reason2": value2, ...},
        ...
    }
    
    And generates commentary in sections based on the Type (Y/Y or Q/Q).
    """
    
    def __init__(self, llm):
        """
        Initialize the generator with an LLM that has an invoke method.
        
        Args:
            llm: A language model instance with an invoke method
        """
        self.llm = llm
        
        # Define the prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["reasons"],
            template="""
            Create a professional financial commentary based on these contributing factors:
            {reasons}
            
            Write a clear and concise sentence explaining these factors and their contributions.
            Focus on how they affected the financial outcome without repeating the overall value.
            """
        )
        
    def generate_reason_commentary(self, reasons: Dict[str, int]) -> str:
        """
        Generate commentary for the reasons and their contributions.
        
        Args:
            reasons: Dict of reasons and their contributions
        
        Returns:
            A sentence explaining the reasons
        """
        # Format the reasons for the prompt
        reasons_text = ', '.join([f"{reason} (${contribution} million)" for reason, contribution in reasons.items()])
        
        # Generate the prompt using the template
        prompt = self.prompt_template.format(reasons=reasons_text)
        
        # Invoke the LLM and get the content
        output = self.llm.invoke(prompt)
        
        # Extract the content from the output
        return output.content
    
    def process_data(self, data: Dict[Tuple[str, str, int], Dict[str, int]]) -> str:
        """
        Process the entire financial dataset and generate a complete commentary.
        
        Args:
            data: The financial data dictionary
        
        Returns:
            Complete formatted commentary with Y/Y and Q/Q sections
        """
        # Separate data into Y/Y and Q/Q categories
        yy_data = {key: value for key, value in data.items() if "Y/Y" in key[1]}
        qq_data = {key: value for key, value in data.items() if "Q/Q" in key[1]}
        
        result = []
        
        # Process Y/Y data if present
        if yy_data:
            result.append("Year on Year Commentary (Y/Y):")
            result.append(self._process_section(yy_data))
        
        # Process Q/Q data if present
        if qq_data:
            result.append("\nQuarter on Quarter Commentary (Q/Q):")
            result.append(self._process_section(qq_data))
        
        # Handle case where there might be only Y/Y or only Q/Q data
        if not result:
            return "No Y/Y or Q/Q data found in the input."
        
        return "\n".join(result)
    
    def _process_section(self, section_data: Dict[Tuple[str, str, int], Dict[str, int]]) -> str:
        """
        Process a section of data (Y/Y or Q/Q) in parallel.
        
        Args:
            section_data: The section data to process
            
        Returns:
            Formatted commentary for the section
        """
        # Sort the data by absolute value (descending)
        sorted_data = sorted(
            section_data.items(), 
            key=lambda item: abs(item[0][2]), 
            reverse=True
        )
        
        results = []
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Create a future -> original data mapping
            futures_to_data = {}
            
            for (category, metric_type, value), reasons in sorted_data:
                # Submit each task to the executor
                future = executor.submit(self.generate_reason_commentary, reasons)
                futures_to_data[future] = (category, metric_type, value)
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(futures_to_data):
                category, metric_type, value = futures_to_data[future]
                commentary = future.result()
                
                # Format the value with sign and "million"
                sign = "+" if value > 0 else ""
                formatted_value = f"{sign}${value} million" if value != 0 else "$0 million"
                
                # Format the final output - hardcoding the left part
                formatted_commentary = f"{category} ({formatted_value}): {commentary}"
                results.append(formatted_commentary)
        
        return "\n".join(results)


# Example usage
def example():
    # Mock LLM class for demonstration
    class MockLLM:
        def invoke(self, prompt):
            # Mock response object with content attribute
            class MockResponse:
                def __init__(self, text):
                    self.content = text
            
            # In a real scenario, this would call the actual LLM API
            return MockResponse("Decrease in product demand (-$30 million) and increased competition (-$20 million).")
    
    # Sample data
    sample_data = {
        ("Sales", "Y/Y $", -50): {"Reason1": -30, "Reason2": -20},
        ("Revenue", "Y/Y $", 25): {"Reason3": 15, "Reason4": 10},
        ("Expenses", "Q/Q $", -15): {"Cost Reduction": -20, "New Initiative": 5}
    }
    
    # Initialize the generator with the LLM
    llm = MockLLM()
    generator = CommentaryGenerator(llm)
    
    # Generate and print the commentary
    commentary = generator.process_data(sample_data)
    print(commentary)
    
    # Example with only Y/Y data
    yy_only_data = {
        ("Sales", "Y/Y $", -50): {"Reason1": -30, "Reason2": -20},
        ("Revenue", "Y/Y $", 25): {"Reason3": 15, "Reason4": 10},
    }
    print("\nY/Y Only Example:")
    print(generator.process_data(yy_only_data))

# How to use with your actual LLM
"""
from langchain.llms import YourLLMImplementation

# Initialize your LLM
llm = YourLLMImplementation()

# Your actual data
financial_data = {
    ("Sales", "Y/Y $", -50): {"Reason1": -30, "Reason2": -20},
    # Add more data here
}

# Initialize and run
generator = CommentaryGenerator(llm)
commentary = generator.process_data(financial_data)
print(commentary)
"""

if __name__ == "__main__":
    example()