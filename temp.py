from tenacity import retry, stop_after_attempt, retry_if_exception_raised
import logging

class MaxExceptionExceed(Exception):
    """Custom exception to indicate maximum retries have been exhausted."""
    pass

def test_llm_with_retries(llm, test_prompt="Hello"):
    """
    Test if an LLM is working by sending a simple prompt and retrying on failure.
    
    Args:
        llm: The language model to test
        test_prompt: A simple prompt to test the LLM (default: "Hello")
        
    Returns:
        bool: True if LLM responds successfully, False if it fails after retries
        
    Raises:
        MaxExceptionExceed: If all retry attempts fail
    """
    logger = logging.getLogger(__name__)
    
    @retry(stop=stop_after_attempt(3), retry=retry_if_exception_raised(Exception))
    def _attempt_llm_invocation():
        logger.info(f"Attempting to invoke LLM with prompt: '{test_prompt}'")
        try:
            response = llm.invoke(test_prompt)
            logger.info("LLM invocation successful")
            return response
        except Exception as e:
            logger.error(f"LLM invocation failed: {str(e)}")
            raise
    
    try:
        response = _attempt_llm_invocation()
        return True
    except Exception:
        logger.critical("Maximum retry attempts reached. LLM is not working.")
        raise MaxExceptionExceed("Failed to get response from LLM after 3 attempts")

# Example usage
if __name__ == "__main__":
    try:
        # Assuming you have your llm instance already loaded
        llm_working = test_llm_with_retries(llm)
        if llm_working:
            print("LLM is working correctly!")
    except MaxExceptionExceed:
        print("LLM is not working after multiple attempts")