from typing import Dict, List, Any, Annotated, Literal, TypedDict, Union, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
import operator
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the state schema
class QueryState(TypedDict):
    user_question: str
    sql_query: Optional[str]
    sql_result: Optional[str]
    error: Optional[str]
    retry_count: int
    status: Literal["GENERATING_SQL", "EXECUTING_SQL", "FORMATTING_RESPONSE", "ERROR", "COMPLETE"]

# Define the nodes of the graph
def generate_sql(state: QueryState, llm, sql_prompt) -> QueryState:
    """Generate SQL from natural language query"""
    logger.info("Generating SQL query")
    
    # Format the prompt with the user question
    formatted_prompt = sql_prompt.format(query=state["user_question"])
    
    # If there was an error, include it in the prompt for retry
    if state.get("error"):
        # Extract the specific error message for the LLM
        error_prompt = f"""
The previous SQL query failed with the following error:
{state["error"]}

Please fix the SQL query. Remember to:
1. Use proper Oracle SQL syntax
2. Use FETCH FIRST N ROWS ONLY instead of LIMIT
3. Use SYSTIMESTAMP instead of NOW()
4. Ensure all column names are properly quoted as "COL_NAME"
5. Only generate the SQL query and nothing else
"""
        # Add error information to the prompt
        formatted_prompt = formatted_prompt.replace("User Question: {query}", f"User Question: {state['user_question']}\n\n{error_prompt}")
    
    # Create the message and invoke the LLM
    sql_messages = [HumanMessage(content=formatted_prompt)]
    sql_response = llm.invoke(sql_messages)
    
    # Extract the SQL query from the response
    sql_query = sql_response.content.strip(";")
    
    logger.info(f"Generated SQL query: {sql_query}")
    
    return {
        **state,
        "sql_query": sql_query,
        "status": "EXECUTING_SQL"
    }

def execute_sql(state: QueryState, db) -> QueryState:
    """Execute SQL query"""
    logger.info(f"Executing SQL: {state['sql_query']}")
    
    try:
        # Execute the query
        sql_result = db.run(state["sql_query"])
        
        return {
            **state,
            "sql_result": sql_result,
            "error": None,
            "status": "FORMATTING_RESPONSE"
        }
    except Exception as e:
        error_message = str(e)
        logger.warning(f"SQL execution error: {error_message}")
        
        return {
            **state,
            "error": error_message,
            "retry_count": state["retry_count"] + 1,
            "status": "ERROR"
        }

def format_response(state: QueryState, llm, response_prompt) -> QueryState:
    """Format the final response"""
    logger.info("Formatting response")
    
    # For successful queries
    if state["status"] == "FORMATTING_RESPONSE":
        # Format the prompt with all the information
        formatted_prompt = response_prompt.format(
            question=state["user_question"],
            sql_query=state["sql_query"],
            sql_result=state["sql_result"]
        )
    else:
        # For queries that failed after max retries
        formatted_prompt = f"""
You are an AI assistant that helps users understand data from an Oracle database.

User Question: {state["user_question"]}
SQL Query: {state["sql_query"]}
SQL Result: Error after {state["retry_count"]} attempts: {state["error"]}

Your Response:
"""
    
    # Create the message and invoke the LLM
    response_messages = [HumanMessage(content=formatted_prompt)]
    final_response = llm.invoke(response_messages)
    
    return {
        **state,
        "sql_result": final_response.content,
        "status": "COMPLETE"
    }

# Create the LangGraph
def create_nl_to_sql_graph(llm, db, sql_prompt, response_prompt, max_retries=10):
    """Create a LangGraph for natural language to SQL processing"""
    
    # Define the graph
    workflow = StateGraph(QueryState)
    
    # Add nodes
    workflow.add_node("generate_sql", lambda state: generate_sql(state, llm, sql_prompt))
    workflow.add_node("execute_sql", lambda state: execute_sql(state, db))
    workflow.add_node("format_response", lambda state: format_response(state, llm, response_prompt))
    
    # Define edges
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_edge("execute_sql", "format_response")
    workflow.add_edge("format_response", END)
    
    # Define conditional edges for retry logic
    def should_retry(state):
        # If error occurred and we haven't exceeded max retries
        if state["status"] == "ERROR" and state["retry_count"] < max_retries:
            return "generate_sql"
        # If error occurred but we've reached max retries
        elif state["status"] == "ERROR":
            return "format_response"
    
    workflow.add_conditional_edges(
        "execute_sql",
        should_retry,
        {
            "generate_sql": "generate_sql",
            "format_response": "format_response"
        }
    )
    
    # Compile the graph
    app = workflow.compile()
    
    # Create a wrapper for easier use
    class NLToSQLGraph:
        def __init__(self, graph):
            self.graph = graph
        
        def process_query(self, query: str) -> str:
            """Process a natural language query from start to finish"""
            # Initialize state
            initial_state = {
                "user_question": query,
                "sql_query": None,
                "sql_result": None,
                "error": None,
                "retry_count": 0,
                "status": "GENERATING_SQL"
            }
            
            # Execute the graph
            for event in self.graph.stream(initial_state):
                pass
            
            # Return the final state (which contains the formatted response)
            final_state = event["state"]
            return final_state["sql_result"]
    
    return NLToSQLGraph(app)

# Example usage with your existing code:
"""
# SQL prompt template (from your code)
sql_prompt = """
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

# Response prompt template (from your code)
response_prompt = """
You are an AI assistant that helps users understand data from an Oracle database.
Given the user's question, SQL query and its results, provide a clear, concise answer.

User Question: {question}
SQL Query: {sql_query}
SQL Result: {sql_result}

Your Response:
"""

# Initialize your database and LLM
# db = Your database instance
# llm = Your LLM instance

# Create and use the graph
nl_to_sql_graph = create_nl_to_sql_graph(
    llm=llm, 
    db=db,
    sql_prompt=sql_prompt,
    response_prompt=response_prompt,
    max_retries=10
)

# Process a query
user_question = "What are the top 3 Attribute based on total of Amount? Also include the Amount value"
result = nl_to_sql_graph.process_query(user_question)
print(result)
"""