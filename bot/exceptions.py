class SQLGenerationError(Exception):
    """Exception raised for errors in SQL generation."""
    pass

class SQLExecutionError(Exception):
    """Exception raised for errors in SQL execution."""
    pass

class MaxRetriesExceededError(Exception):
    """Exception raised when max retries are exceeded."""
    pass
