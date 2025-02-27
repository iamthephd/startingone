from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnablePassthrough
from langgraph.graph import END, StateGraph
from typing import TypedDict, List, Dict, Any, Optional
from langchain_community.utilities.sql_database import SQLDatabase

# Custom LLM wrapper for your model that only supports invoke
class CustomLLM:
    def __init__(self, model_id: str):
        self.model_id = model_id
        
    def invoke(self, prompt: str) -> str:
        # This is a placeholder for your actual custom LLM
        # In a real implementation, you would call your LLM here
        print(f"Calling LLM {self.model_id} with prompt: {prompt[:50]}...")
        return f"Response from {self.model_id}"

# Initialize the three LLMs
sql_generator_llm = CustomLLM("sql-generator")
sql_validator_llm = CustomLLM("sql-validator")
response_generator_llm = CustomLLM("response-generator")

# Connect to Oracle DB (placeholder)
db = SQLDatabase()  # In reality, this would be your Oracle DB connection

# Define the state for our graph
class ChatbotState(TypedDict):
    chat_history: List[Dict[str, Any]]
    current_query: str
    sql_query: Optional[str]
    sql_validation: Optional[bool]
    db_results: Optional[Dict[str, Any]]
    attempt_count: int

# Define the nodes for our graph
def generate_sql(state: ChatbotState) -> ChatbotState:
    """Generate SQL query from user question"""
    # Format prompt with user query and chat history for context
    history_str = format_chat_history(state["chat_history"])
    
    # Prompt template for SQL generation
    prompt = f"""
    Given the following chat history:
    {history_str}
    
    And the user's current query: {state["current_query"]}
    
    Generate a SQL query for Oracle DB that will answer the user's question.
    Return only the SQL query without any explanations.
    """
    
    # Generate SQL query
    sql_query = sql_generator_llm.invoke(prompt)
    
    # Update state
    return {**state, "sql_query": sql_query, "attempt_count": state["attempt_count"] + 1}

def validate_sql(state: ChatbotState) -> ChatbotState:
    """Validate the generated SQL query"""
    # Prompt template for SQL validation
    prompt = f"""
    Validate the following SQL query for Oracle DB:
    
    {state["sql_query"]}
    
    This query is meant to answer the user question: {state["current_query"]}
    
    Return 'VALID' if the query is correct, 'INVALID' otherwise.
    If invalid, explain the issue briefly.
    """
    
    # Validate SQL query
    validation_result = sql_validator_llm.invoke(prompt)
    
    # Check if query is valid
    is_valid = "VALID" in validation_result.upper()
    
    # Update state
    return {**state, "sql_validation": is_valid, "validation_message": validation_result}

def execute_query(state: ChatbotState) -> ChatbotState:
    """Execute the SQL query on the database"""
    try:
        # Execute query
        db_results = db.run(state["sql_query"])
        
        # Update state
        return {**state, "db_results": db_results}
    except Exception as e:
        # Handle query execution error
        return {**state, "sql_validation": False, "validation_message": f"Error executing query: {str(e)}"}

def generate_response(state: ChatbotState) -> ChatbotState:
    """Generate natural language response based on DB results"""
    # Format prompt with user query, chat history, and DB results
    history_str = format_chat_history(state["chat_history"])
    
    # Prompt template for response generation
    prompt = f"""
    Given the following chat history:
    {history_str}
    
    User's current query: {state["current_query"]}
    
    Database results: {state["db_results"]}
    
    Generate a natural language response that answers the user's question based on the database results.
    Be conversational and concise.
    """
    
    # Generate response
    response = response_generator_llm.invoke(prompt)
    
    # Add new message to chat history
    new_history = state["chat_history"] + [
        {"role": "human", "content": state["current_query"]},
        {"role": "ai", "content": response}
    ]
    
    # Update state
    return {**state, "chat_history": new_history, "response": response}

def format_chat_history(history: List[Dict[str, Any]]) -> str:
    """Format chat history into a string for prompt context"""
    if not history:
        return "No previous conversation."
        
    formatted = []
    for msg in history:
        role = "User" if msg["role"] == "human" else "Assistant"
        formatted.append(f"{role}: {msg['content']}")
    
    return "\n".join(formatted)

# Decision-making functions for routing
def should_regenerate_sql(state: ChatbotState) -> str:
    """Decide whether to regenerate SQL or continue"""
    if not state["sql_validation"] and state["attempt_count"] < 3:
        return "regenerate_sql"
    elif not state["sql_validation"]:
        return "max_attempts"
    else:
        return "execute_query"

def handle_max_attempts(state: ChatbotState) -> ChatbotState:
    """Handle case when max SQL generation attempts reached"""
    error_response = "I'm having trouble generating a valid SQL query for your question. Could you please rephrase or provide more details?"
    
    # Add new message to chat history
    new_history = state["chat_history"] + [
        {"role": "human", "content": state["current_query"]},
        {"role": "ai", "content": error_response}
    ]
    
    # Update state
    return {**state, "chat_history": new_history, "response": error_response}

# Build the graph
def build_graph() -> StateGraph:
    """Build the LangGraph workflow"""
    # Initialize graph
    graph = StateGraph(ChatbotState)
    
    # Add nodes
    graph.add_node("generate_sql", generate_sql)
    graph.add_node("validate_sql", validate_sql)
    graph.add_node("execute_query", execute_query)
    graph.add_node("generate_response", generate_response)
    graph.add_node("handle_max_attempts", handle_max_attempts)
    
    # Set entry point
    graph.set_entry_point("generate_sql")
    
    # Add edges
    graph.add_edge("generate_sql", "validate_sql")
    
    # Add conditional edges from validate_sql
    graph.add_conditional_edges(
        "validate_sql",
        should_regenerate_sql,
        {
            "regenerate_sql": "generate_sql",
            "execute_query": "execute_query",
            "max_attempts": "handle_max_attempts"
        }
    )
    
    graph.add_edge("execute_query", "generate_response")
    
    # Set exit points
    graph.add_edge("generate_response", END)
    graph.add_edge("handle_max_attempts", END)
    
    return graph

# Create the chatbot class
class OracleChatbot:
    def __init__(self):
        self.graph = build_graph().compile()
        self.state = {
            "chat_history": [],
            "current_query": "",
            "sql_query": None,
            "sql_validation": None,
            "db_results": None,
            "attempt_count": 0,
            "response": ""
        }
    
    def query(self, user_input: str) -> str:
        """Process a user query and return a response"""
        # Update current query
        self.state["current_query"] = user_input
        self.state["attempt_count"] = 0
        
        # Run the graph
        result = self.graph.invoke(self.state)
        
        # Update state with result
        self.state = result
        
        # Return the response
        return self.state["response"]

# Example usage
if __name__ == "__main__":
    chatbot = OracleChatbot()
    
    # Example conversation
    queries = [
        "How many customers do we have in California?",
        "What about in New York?",
        "Which one had the highest sales last month?"
    ]
    
    for query in queries:
        print(f"\nUser: {query}")
        response = chatbot.query(query)
        print(f"Assistant: {response}")