from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import List, Tuple, Dict, Any

class InsightsManager:
    def __init__(self, llm, dataframe):
        self.llm = llm
        self.df = dataframe
        self.current_insights = ""
        
        # Chain for modifying existing insights
        self.modifier_prompt = PromptTemplate(
            input_variables=["current_insights", "modification_request"],
            template="Current insights:\n{current_insights}\n\nUser request: {modification_request}\n\nModified insights:"
        )
        self.modifier_chain = LLMChain(llm=llm, prompt=self.modifier_prompt)
        
        # Chain for parsing user requests
        self.parser_prompt = PromptTemplate(
            input_variables=["user_message"],
            template="""Analyze the following user message and classify what the user wants to do:
User message: {user_message}

If the user wants to add new insights for specific row and column names, extract:
1. Row names mentioned
2. Column names mentioned
3. The number of top contributors (default to 3 if not specified)

Output in this format:
REQUEST_TYPE: [ADD_INSIGHTS or MODIFY_INSIGHTS]
ROW_NAMES: [comma-separated list of row names]
COLUMN_NAMES: [comma-separated list of column names]
TOP_N: [number]

Example 1:
User: "Add insights for Sales department and Q3 revenue for top 5 contributors"
Response:
REQUEST_TYPE: ADD_INSIGHTS
ROW_NAMES: Sales
COLUMN_NAMES: Q3 revenue
TOP_N: 5

Example 2:
User: "Change 'declining revenue' to 'decreasing income'"
Response:
REQUEST_TYPE: MODIFY_INSIGHTS
"""
        )
        self.parser_chain = LLMChain(llm=llm, prompt=self.parser_prompt)
    
    def get_commentary(self, row_col_tuples: List[Tuple[str, str, float]], top_n: int) -> str:
        # This is your existing function
        # Assuming it's implemented elsewhere
        pass
    
    def process_message(self, user_message: str) -> str:
        # Parse the user request
        parser_response = self.parser_chain.invoke({"user_message": user_message})
        
        # Extract the parsed information
        parsed_info = self._extract_parsed_info(parser_response['text'])
        
        if parsed_info['request_type'] == 'ADD_INSIGHTS':
            # Handle request to add insights
            row_names = parsed_info['row_names']
            col_names = parsed_info['column_names']
            top_n = parsed_info['top_n']
            
            # Create row-col tuples with values from the dataframe
            tuples = []
            for row in row_names:
                for col in col_names:
                    if row in self.df.index and col in self.df.columns:
                        value = self.df.loc[row, col]
                        tuples.append((row, col, value))
            
            # Get new insights
            new_insights = self.get_commentary(tuples, top_n)
            
            # Append to current insights
            if self.current_insights:
                self.current_insights += "\n\n" + new_insights
            else:
                self.current_insights = new_insights
                
            return f"Added insights for {', '.join(row_names)} and {', '.join(col_names)}."
            
        elif parsed_info['request_type'] == 'MODIFY_INSIGHTS':
            # Handle request to modify insights
            modified_insights = self.modifier_chain.invoke({
                "current_insights": self.current_insights,
                "modification_request": user_message
            })
            
            self.current_insights = modified_insights['text']
            return "Insights updated successfully."
            
        else:
            return "I'm not sure what you're asking. You can request to add insights for specific rows and columns, or modify existing insights."
    
    def _extract_parsed_info(self, parser_output: str) -> Dict[str, Any]:
        """Extract structured information from the parser output"""
        lines = parser_output.strip().split('\n')
        result = {
            'request_type': 'UNKNOWN',
            'row_names': [],
            'column_names': [],
            'top_n': 3  # Default value
        }
        
        for line in lines:
            if line.startswith('REQUEST_TYPE:'):
                result['request_type'] = line.replace('REQUEST_TYPE:', '').strip()
            elif line.startswith('ROW_NAMES:'):
                row_names = line.replace('ROW_NAMES:', '').strip()
                result['row_names'] = [name.strip() for name in row_names.split(',') if name.strip()]
            elif line.startswith('COLUMN_NAMES:'):
                col_names = line.replace('COLUMN_NAMES:', '').strip()
                result['column_names'] = [name.strip() for name in col_names.split(',') if name.strip()]
            elif line.startswith('TOP_N:'):
                try:
                    result['top_n'] = int(line.replace('TOP_N:', '').strip())
                except ValueError:
                    pass  # Keep default value
                    
        return result