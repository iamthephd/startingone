import functools
import signal
import time

def retry_with_timeout(max_retries=3, timeout=5):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            for attempt in range(max_retries):
                # Set up a signal handler for timeout
                def handler(signum, frame):
                    raise TimeoutError(f"Function call timed out after {timeout} seconds")
                
                # Set the signal alarm
                signal.signal(signal.SIGALRM, handler)
                signal.alarm(timeout)
                
                try:
                    # Try to execute the function
                    result = func(self, *args, **kwargs)
                    # Cancel the alarm if successful
                    signal.alarm(0)
                    return result
                
                except TimeoutError:
                    print(f"Attempt {attempt + 1} timed out")
                    if attempt == max_retries - 1:
                        return "Try Again"
                
                except Exception as e:
                    print(f"Error in attempt {attempt + 1}: {str(e)}")
                    if attempt == max_retries - 1:
                        return "Try Again"
                
                # Add a small delay between retries
                time.sleep(1)
        
        return wrapper
    return decorator

class YourClass:
    @retry_with_timeout(max_retries=3, timeout=5)
    def format_response(self, user_question: str, sql_query: str, sql_result: str) -> str:
        """
        Format the final response using LLM with timeout and retry mechanism.
        
        :param user_question: The user's original question
        :param sql_query: The SQL query executed
        :param sql_result: The result of the SQL query
        :return: Formatted response or "Try Again" if failed
        """
        try:
            response_messages = [
                HumanMessage(content=self.response_prompt_template.format(
                    question=user_question,
                    sql_query=sql_query,
                    sql_result=sql_result
                ))
            ]
            
            final_response = self.llm.invoke(response_messages)
            return final_response.content
        
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            raise Exception(f"Failed to format response: {str(e)}")