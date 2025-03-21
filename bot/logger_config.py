import logging
import sys
import os

def setup_logger():
    """Configure logging for the application."""
    logger = logging.getLogger('sql_chain')
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Updated formatter to include filename and line number
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler('sql_chain.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Initialize the logger
logger = setup_logger()
