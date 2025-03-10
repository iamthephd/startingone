from sql_chain import SQLChain
from logger_config import logger

# llm = 
# db = 

def main():
    try:
        # Example usage assuming llm and db instances are provided
        user_question = "What are the top 3 Attribute based on total of Amount? Also include the Amount value"
        
        # Initialize the chain
        chain = SQLChain(llm=llm, db=db)  # llm and db should be provided
        
        # Run the chain
        result = chain.run(user_question)
        
        # Print results
        print("\nProcessing Results:")
        print("-" * 50)
        print(f"User Question: {result['user_question']}")
        print(f"\nGenerated SQL: {result['sql_query']}")
        print(f"\nSQL Result: {result['sql_result']}")
        print(f"\nFormatted Response: {result['formatted_response']}")
        print(f"\nNumber of retries needed: {result['retry_count']}")
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
