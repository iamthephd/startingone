from typing import Optional, Tuple
from langchain.schema import HumanMessage
from logger_config import logger
from exceptions import SQLGenerationError, SQLExecutionError, MaxRetriesExceededError

class SQLChain:
    def __init__(self, llm, db, max_retries: int = 10):
        self.llm = llm
        self.db = db
        self.max_retries = max_retries
        
        self.sql_prompt_template = """
You are an AI assistant that helps users query an Oracle database from CMDM_Product table.
Based on the user's question, generate the appropriate SQL query.

**Note : Only provide the SQL query and nothing else. Also provide the column/s name is "**
**IMP : Generate SQL queries for an Oracle database. Avoid unsupported keywords like
LIMIT, OFFSET, AUTO_INCREMENT, BOOLEAN, TEXT, DATETIME, and IF EXISTS. Use FETCH FIRST N ROWS ONLY
instead of LIMIT, SEQUENCE instead of AUTO_INCREMENT, and SYSTIMESTAMP instead of NOW().
Ensure proper Oracle SQL syntax**
**Note : Only provide the SQL query and nothing else. **
**Note : Also provide the column name as is "COL_NAME" i.e. in quotation mark**

User Question: {query}

SQL Query:"""

        self.response_prompt_template = """
You are an AI assistant that helps users understand data from an Oracle database.
Given the user's question, SQL query and its results, provide a clear, concise answer.

User Question: {question}
SQL Query: {sql_query}
SQL Result: {sql_result}

Your Response:
"""

    def generate_sql(self, user_question: str) -> str:
        """Generate SQL query from natural language question."""
        try:
            sql_messages = [HumanMessage(content=self.sql_prompt_template.format(query=user_question))]
            sql_response = self.llm.invoke(sql_messages)
            sql_query = sql_response.content.strip(";")
            logger.info(f"Generated SQL query: {sql_query}")
            return sql_query
        except Exception as e:
            logger.error(f"Error generating SQL query: {str(e)}")
            raise SQLGenerationError(f"Failed to generate SQL query: {str(e)}")

    def execute_sql_with_retry(self, sql_query: str) -> Tuple[str, int]:
        """Execute SQL query with retry logic."""
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                result = self.db.run(sql_query)
                logger.info(f"SQL query executed successfully after {retries} retries")
                return result, retries
            except Exception as e:
                last_error = str(e)
                retries += 1
                logger.warning(f"SQL execution failed (attempt {retries}): {last_error}")
                
                # Generate new SQL query for retry
                try:
                    sql_query = self.generate_sql(f"Fix this SQL query that gave error '{last_error}': {sql_query}")
                except Exception as gen_error:
                    logger.error(f"Failed to generate new SQL query: {str(gen_error)}")
                    raise SQLGenerationError(f"Failed to generate new SQL query: {str(gen_error)}")
        
        raise MaxRetriesExceededError(f"Max retries ({self.max_retries}) exceeded. Last error: {last_error}")

    def format_response(self, user_question: str, sql_query: str, sql_result: str) -> str:
        """Format the final response using LLM."""
        try:
            response_messages = [
                HumanMessage(content=self.response_prompt_template.format(
                    question=user_question,
                    sql_result=sql_result,
                    sql_query=sql_query
                ))
            ]
            final_response = self.llm.invoke(response_messages)
            return final_response.content
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            raise Exception(f"Failed to format response: {str(e)}")

    def run(self, user_question: str) -> dict:
        """Execute the complete chain."""
        try:
            logger.info(f"Processing user question: {user_question}")
            
            # Generate SQL
            sql_query = self.generate_sql(user_question)
            
            # Execute SQL with retry
            sql_result, retry_count = self.execute_sql_with_retry(sql_query)
            
            # Format response
            formatted_response = self.format_response(user_question, sql_query, sql_result)
            
            return {
                "user_question": user_question,
                "sql_query": sql_query,
                "sql_result": sql_result,
                "formatted_response": formatted_response,
                "retry_count": retry_count
            }
            
        except Exception as e:
            logger.error(f"Chain execution failed: {str(e)}")
            raise
