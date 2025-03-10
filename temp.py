import os
from typing import List, Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import re

# Define the state of our graph
class GraphState(TypedDict):
    user_query: str
    sql_query: str
    sql_result: Any
    final_answer: str
    retry_count: int
    error: str

# Function to convert natural language to SQL
def nl_to_sql(state: GraphState, llm1, prompt_template1):
    """Convert natural language to SQL using LLM1"""
    user_query = state["user_query"]
    
    # Format the prompt with the user query
    prompt = prompt_template1.format(question=user_query)
    
    # Get SQL from LLM1
    response = llm1.invoke(prompt)
    
    # Extract SQL query from response (assuming the SQL is returned directly)
    # You might need to adjust this depending on your LLM1's output format
    sql_query = response.strip()
    
    # Basic SQL validation/extraction (you might need to adjust based on your LLM output)
    if "SELECT" not in sql_query.upper():
        # If no SQL found, try to extract it using regex
        sql_match = re.search(r'```sql\s*(.*?)\s*```', sql_query, re.DOTALL)
        if sql_match:
            sql_query = sql_match.group(1).strip()
    
    return {"sql_query": sql_query, "retry_count": state.get("retry_count", 0)}

# Function to execute SQL
def execute_sql(state: GraphState, db):
    """Execute SQL query using the database"""
    sql_query = state["sql_query"]
    
    try:
        # Execute SQL
        result = db.run(sql_query)
        return {"sql_result": result, "error": ""}
    except Exception as e:
        # If execution fails, return the error
        return {"sql_result": None, "error": str(e)}

# Function to format the final answer
def format_answer(state: GraphState, llm2, prompt_template2):
    """Format the result using LLM2"""
    user_query = state["user_query"]
    sql_result = state["sql_result"]
    
    # Format the prompt with user query and SQL result
    prompt = prompt_template2.format(
        question=user_query,
        sql_result=sql_result
    )
    
    # Get formatted answer from LLM2
    response = llm2.invoke(prompt)
    
    return {"final_answer": response}

# Decision function to determine next steps
def should_retry(state: GraphState) -> str:
    """Decide whether to retry SQL generation or move forward"""
    # If there's an error and we haven't exceeded max retries
    if state.get("error") and state.get("retry_count", 0) < 10:
        return "retry"
    elif state.get("error"):
        # If we've exceeded max retries, end with an error message
        return "max_retries_exceeded"
    else:
        # If there's no error, proceed to format answer
        return "format_answer"

# Function to increment retry counter
def increment_retry(state: GraphState):
    """Increment the retry counter"""
    return {"retry_count": state.get("retry_count", 0) + 1, 
            "error": f"Previous error: {state.get('error', 'Unknown error')}"}

# Function to handle max retries exceeded
def handle_max_retries(state: GraphState):
    """Handle case when max retries are exceeded"""
    return {
        "final_answer": f"Sorry, I couldn't generate a valid SQL query after multiple attempts. The last error was: {state.get('error', 'Unknown error')}"
    }

# Main function to build and run the graph
def build_sql_query_graph(llm1, llm2, db, prompt_template1, prompt_template2):
    """Build the SQL query graph"""
    # Create the graph
    graph = StateGraph(GraphState)
    
    # Define nodes
    graph.add_node("nl_to_sql", lambda state: nl_to_sql(state, llm1, prompt_template1))
    graph.add_node("execute_sql", lambda state: execute_sql(state, db))
    graph.add_node("format_answer", lambda state: format_answer(state, llm2, prompt_template2))
    graph.add_node("increment_retry", increment_retry)
    graph.add_node("handle_max_retries", handle_max_retries)
    
    # Define edges
    graph.add_edge("nl_to_sql", "execute_sql")
    graph.add_edge("execute_sql", should_retry)
    graph.add_conditional_edges(
        "should_retry",
        {
            "retry": "increment_retry",
            "format_answer": "format_answer",
            "max_retries_exceeded": "handle_max_retries"
        }
    )
    graph.add_edge("increment_retry", "nl_to_sql")
    graph.add_edge("format_answer", END)
    graph.add_edge("handle_max_retries", END)
    
    # Set the entry point
    graph.set_entry_point("nl_to_sql")
    
    # Compile the graph
    return graph.compile()

# Function to run the entire process
def process_query(user_query, llm1, llm2, db, prompt_template1, prompt_template2):
    """Process a natural language query and return the answer"""
    # Build the graph
    graph = build_sql_query_graph(llm1, llm2, db, prompt_template1, prompt_template2)
    
    # Run the graph
    result = graph.invoke({"user_query": user_query, "retry_count": 0})
    
    return result["final_answer"]

# Example usage
if __name__ == "__main__":
    # These would be your actual implementations
    class MockLLM:
        def invoke(self, prompt):
            # Mock implementation
            return "SELECT * FROM users LIMIT 10"
    
    class MockDB:
        def run(self, query):
            # Mock implementation
            return [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
    
    # Create mock objects for demonstration
    llm1 = MockLLM()
    llm2 = MockLLM()
    db = MockDB()
    
    # Mock prompt templates
    class MockPromptTemplate:
        def format(self, **kwargs):
            return f"Prompt with {kwargs}"
    
    prompt_template1 = MockPromptTemplate()
    prompt_template2 = MockPromptTemplate()
    
    # Process a query
    result = process_query(
        "Show me all users", 
        llm1, 
        llm2, 
        db, 
        prompt_template1, 
        prompt_template2
    )
    
    print(result)