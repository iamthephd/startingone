import concurrent.futures
from typing import Dict, Tuple, List, Any, Callable
import re

class CommentaryGenerator:
    """
    Generates financial commentary from structured data using an LLM.
    
    The class processes financial data in the format:
    {
        ("Category", "Type", value): {"Reason1": value1, "Reason2": value2, ...},
        ...
    }
    
    And generates commentary in sections based on the Type (Y/Y or Q/Q).
    """
    
    def __init__(self, llm_invoke_function: Callable):
        """
        Initialize the generator with an LLM invoke function.
        
        Args:
            llm_invoke_function: A function that takes a prompt string and returns an LLM response.
        """
        self.llm_invoke = llm_invoke_function
        
    def generate_reason_commentary(self, reasons: Dict[str, int]) -> str:
        """
        Generate commentary for the reasons and their contributions.
        
        Args:
            reasons: Dict of reasons and their contributions
        
        Returns:
            A sentence explaining the reasons
        """
        # Create the prompt for the LLM
        prompt = f"""
        Create a concise, professional financial statement based on these contributing factors:
        {', '.join([f"{reason} (${contribution} million)" for reason, contribution in reasons.items()])}
        
        Start with 'This is mainly due to' and focus on the key drivers. Format the response as a single paragraph.
        Don't repeat the overall impact or value, just explain the reasons clearly and professionally.
        """
        
        # Get commentary from LLM
        commentary = self.llm_invoke(prompt).strip()
        
        # Remove any prefixes the LLM might have added to ensure we get a clean start
        commentary = re.sub(r'^.*?[Mm]ainly due to', 'This is mainly due to', commentary)
        
        return commentary
    
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
                
                # Format the final output
                formatted_commentary = f"{category} ({formatted_value}): {commentary}"
                results.append(formatted_commentary)
        
        return "\n".join(results)


# Example usage
def example():
    # Mock LLM invoke function for demonstration
    def mock_llm_invoke(prompt):
        # In a real scenario, this would call your actual LLM
        return "This is mainly due to Reason1 contributing negatively (-$30 million) and Reason2 also having a negative impact (-$20 million)."
    
    # Sample data
    sample_data = {
        ("Sales", "Y/Y $", -50): {"Reason1": -30, "Reason2": -20},
        ("Revenue", "Y/Y $", 25): {"Reason3": 15, "Reason4": 10},
        ("Expenses", "Q/Q $", -15): {"Cost Reduction": -20, "New Initiative": 5}
    }
    
    # Initialize the generator with the LLM function
    generator = CommentaryGenerator(mock_llm_invoke)
    
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
    
    # Example with only Q/Q data
    qq_only_data = {
        ("Expenses", "Q/Q $", -15): {"Cost Reduction": -20, "New Initiative": 5}
    }
    print("\nQ/Q Only Example:")
    print(generator.process_data(qq_only_data))

# How to use with your actual LLM
"""
# Replace this with your actual LLM implementation
def my_llm_invoke(prompt: str) -> str:
    # Call your LLM API here
    response = my_llm.invoke(prompt)
    return response

# Your actual data
financial_data = {
    ("Sales", "Y/Y $", -50): {"Reason1": -30, "Reason2": -20},
    # Add more data here
}

# Initialize and run
generator = CommentaryGenerator(my_llm_invoke)
commentary = generator.process_data(financial_data)
print(commentary)
"""

if __name__ == "__main__":
    example()