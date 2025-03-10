from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from typing import Dict, Any, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SQLQueryExecutor:
    def __init__(self, llm1, llm2, db, sql_prompt_template, response_prompt_template, max_retries=10):
        """
        Initialize the SQL Query Executor.
        
        Args:
            llm1: LLM for converting natural language to SQL
            llm2: LLM for formatting the final response
            db: Database instance with run() method
            sql_prompt_template: Template for generating SQL from natural language
            response_prompt_template: Template for formatting the final response
            max_retries: Maximum number of retries for SQL execution
        """
        self.llm1 = llm1
        self.llm2 = llm2
        self.db = db
        self.sql_prompt_template = sql_prompt_template
        self.response_prompt_template = response_prompt_template
        self.max_retries = max_retries
        
        # Create the SQL generation chain
        self.sql_chain = LLMChain(
            llm=self.llm1,
            prompt=self.sql_prompt_template,
            output_parser=StrOutputParser()
        )
        
        # Create the response formatting chain
        self.response_chain = LLMChain(
            llm=self.llm2,
            prompt=self.response_prompt_template,
            output_parser=StrOutputParser()
        )
    
    def _execute_sql_with_retry(self, sql_query: str, retry_count: int = 0) -> Dict[str, Any]:
        """
        Execute SQL query with retry logic.
        
        Args:
            sql_query: SQL query to execute
            retry_count: Current retry count
            
        Returns:
            Dictionary with SQL query and results (or error)
        """
        if retry_count >= self.max_retries:
            return {
                "sql_query": sql_query,
                "result": f"Failed after {self.max_retries} attempts. Last error: Query execution failed.",
                "success": False
            }
        
        try:
            logger.info(f"Executing SQL query: {sql_query}")
            result = self.db.run(sql_query)
            return {
                "sql_query": sql_query,
                "result": result,
                "success": True
            }
        except Exception as e:
            logger.warning(f"Error executing SQL (attempt {retry_count + 1}/{self.max_retries}): {str(e)}")
            
            # Generate improved SQL query
            improved_query = self.sql_chain.invoke({
                "query": f"The following SQL query failed: {sql_query}. Error: {str(e)}. Please fix the SQL query."
            })
            
            # Retry with improved query
            return self._execute_sql_with_retry(improved_query, retry_count + 1)
    
    def process_query(self, query: str) -> str:
        """
        Process a natural language query from start to finish.
        
        Args:
            query: Natural language query
            
        Returns:
            Formatted response
        """
        # Step 1: Generate SQL from natural language
        sql_query = self.sql_chain.invoke({"query": query})
        
        # Step 2: Execute SQL with retry logic
        execution_result = self._execute_sql_with_retry(sql_query)
        
        # Step 3: Format response
        response_input = {
            "query": query,
            "sql_query": execution_result["sql_query"],
            "result": execution_result["result"]
        }
        
        formatted_response = self.response_chain.invoke(response_input)
        return formatted_response

# Create the chain as a unified class
def create_nl_to_sql_chain(llm1, llm2, db, sql_prompt_template, response_prompt_template, max_retries=10):
    """
    Create a Natural Language to SQL chain.
    
    Args:
        llm1: LLM for converting natural language to SQL
        llm2: LLM for formatting the final response
        db: Database instance with run() method
        sql_prompt_template: Template for generating SQL from natural language
        response_prompt_template: Template for formatting the final response
        max_retries: Maximum number of retries for SQL execution
        
    Returns:
        SQLQueryExecutor instance
    """
    return SQLQueryExecutor(
        llm1=llm1,
        llm2=llm2,
        db=db,
        sql_prompt_template=sql_prompt_template,
        response_prompt_template=response_prompt_template,
        max_retries=max_retries
    )

# Example usage:
"""
# Assuming you have these components:
from langchain_openai import ChatOpenAI
import os

# Initialize LLMs
llm1 = ChatOpenAI(api_key=os.environ["OPENAI_API_KEY"], model="gpt-4")
llm2 = ChatOpenAI(api_key=os.environ["OPENAI_API_KEY"], model="gpt-3.5-turbo")

# Define prompt templates
sql_prompt_template = PromptTemplate(
    input_variables=["query"],
    template="Convert the following natural language query to SQL: {query}"
)

response_prompt_template = PromptTemplate(
    input_variables=["query", "sql_query", "result"],
    template="User query: {query}\nSQL query: {sql_query}\nQuery result: {result}\n\nProvide a well-formatted response to the user's question."
)

# Initialize database (placeholder)
class Database:
    def run(self, query):
        # This would be your actual database connection
        return "Sample result from database"

db = Database()

# Create the chain
nl_to_sql_chain = create_nl_to_sql_chain(
    llm1=llm1,
    llm2=llm2,
    db=db,
    sql_prompt_template=sql_prompt_template,
    response_prompt_template=response_prompt_template,
    max_retries=10
)

# Use the chain
result = nl_to_sql_chain.process_query("How many users registered last month?")
print(result)
"""