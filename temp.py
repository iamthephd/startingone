import os
from typing import List, Dict, Any, Optional
from langchain.chains import SQLDatabaseChain
from langchain.sql_database import SQLDatabase
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationChain
from langchain.schema import BaseMessage, HumanMessage, AIMessage

# Setup Oracle DB connection
def get_oracle_db():
    # Replace with your Oracle connection details
    oracle_connection_string = "oracle+cx_oracle://username:password@hostname:port/service_name"
    return SQLDatabase.from_uri(oracle_connection_string)

# Method 1: Simple one-shot query without follow-up capability
def create_simple_oracle_chatbot(llm):
    db = get_oracle_db()
    
    # Create a prompt template for SQL generation
    sql_prompt = """
    You are an AI assistant that helps users query an Oracle database.
    Based on the user's question, generate the appropriate SQL query.
    The database has tables for customers, sales, products, and more.
    
    User Question: {question}
    
    SQL Query:
    """
    
    # Create a prompt template for generating the final response
    response_prompt = """
    You are an AI assistant that helps users understand data from an Oracle database.
    Given the user's question and the SQL query results, provide a clear, concise answer.
    
    User Question: {question}
    SQL Query: {query}
    SQL Result: {result}
    
    Your Response:
    """
    
    def query_database(user_question):
        # Step 1: Generate SQL query
        sql_messages = [HumanMessage(content=sql_prompt.format(question=user_question))]
        sql_response = llm.invoke(sql_messages)
        sql_query = sql_response.content.strip()
        
        # Step 2: Execute the query
        try:
            result = db.run(sql_query)
        except Exception as e:
            return f"Error executing query: {str(e)}"
        
        # Step 3: Generate the final response
        response_messages = [
            HumanMessage(content=response_prompt.format(
                question=user_question,
                query=sql_query,
                result=result
            ))
        ]
        final_response = llm.invoke(response_messages)
        return final_response.content
    
    return query_database

# Method 2: Conversational bot with follow-up capability
def create_conversational_oracle_chatbot(llm):
    db = get_oracle_db()
    
    # Create memory to store conversation history
    memory = []
    
    # Create a prompt template for SQL generation with context
    sql_context_prompt = """
    You are an AI assistant that helps users query an Oracle database.
    Based on the user's question and the conversation history, generate the appropriate SQL query.
    The database has tables for customers, sales, products, and more.
    
    Conversation History:
    {history}
    
    Current User Question: {question}
    
    SQL Query:
    """
    
    # Create a prompt template for generating the final response
    response_context_prompt = """
    You are an AI assistant that helps users understand data from an Oracle database.
    Given the conversation history, the user's question, and the SQL query results, provide a clear, concise answer.
    
    Conversation History:
    {history}
    
    Current User Question: {question}
    SQL Query: {query}
    SQL Result: {result}
    
    Your Response:
    """
    
    def format_history(memory_list):
        formatted = ""
        for i, message in enumerate(memory_list):
            role = "User" if i % 2 == 0 else "Assistant"
            formatted += f"{role}: {message}\n"
        return formatted
    
    def chat(user_question):
        # Add user question to memory
        if len(memory) > 0:  # Not the first question
            memory.append(user_question)
            history = format_history(memory[:-1])  # Exclude current question from history
        else:
            memory.append(user_question)
            history = ""
        
        # Step 1: Generate SQL query based on conversation context
        sql_messages = [
            HumanMessage(content=sql_context_prompt.format(
                history=history,
                question=user_question
            ))
        ]
        sql_response = llm.invoke(sql_messages)
        sql_query = sql_response.content.strip()
        
        # Step 2: Execute the query
        try:
            result = db.run(sql_query)
        except Exception as e:
            response = f"Error executing query: {str(e)}"
            memory.append(response)
            return response
        
        # Step 3: Generate the final response
        response_messages = [
            HumanMessage(content=response_context_prompt.format(
                history=history,
                question=user_question,
                query=sql_query,
                result=result
            ))
        ]
        final_response = llm.invoke(response_messages)
        
        # Add response to memory
        memory.append(final_response.content)
        
        return final_response.content
    
    return chat

# Example usage
def main():
    # Import your LLM with invoke method
    from your_llm_module import YourBaseChatModel
    
    # Initialize your LLM
    llm = YourBaseChatModel()
    
    # Method 1: Simple one-shot chatbot
    simple_bot = create_simple_oracle_chatbot(llm)
    response = simple_bot("What is the average sales amount?")
    print("Simple Bot Response:", response)
    
    # Method 2: Conversational chatbot
    chat_bot = create_conversational_oracle_chatbot(llm)
    
    # Example conversation
    print("\nConversational Bot:")
    response1 = chat_bot("What is the average sales amount?")
    print("User: What is the average sales amount?")
    print("Bot:", response1)
    
    response2 = chat_bot("What are the top 3 highest sales values?")
    print("User: What are the top 3 highest sales values?")
    print("Bot:", response2)
    
    response3 = chat_bot("What is name of the customers which contributed to these sales?")
    print("User: What is name of the customers which contributed to these sales?")
    print("Bot:", response3)

if __name__ == "__main__":
    main()