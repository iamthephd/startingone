import logging
import os
from datetime import datetime
import inspect

class CustomLogger:
    """
    A custom logger class that can be imported and used across multiple files in a project.
    Provides consistent logging format and multiple output options.
    """
    
    def __init__(self, log_level=logging.INFO, log_file=None, console_output=True):
        """
        Initialize the logger with configurable options.
        
        Args:
            log_level: The minimum log level to record (default: INFO)
            log_file: Path to log file (default: None, meaning no file logging)
            console_output: Whether to output logs to console (default: True)
        """
        # Create a unique logger name based on the calling module
        frame = inspect.stack()[1]
        self.logger_name = os.path.basename(frame.filename).split('.')[0]
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(log_level)
        self.logger.handlers = []  # Clear any existing handlers
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add console handler if requested
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Add file handler if a log file is specified
        if log_file:
            # Create log directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message):
        """Log a debug message."""
        self.logger.debug(message)
    
    def info(self, message):
        """Log an info message."""
        self.logger.info(message)
    
    def warning(self, message):
        """Log a warning message."""
        self.logger.warning(message)
    
    def error(self, message):
        """Log an error message."""
        self.logger.error(message)
    
    def critical(self, message):
        """Log a critical message."""
        self.logger.critical(message)

# Singleton pattern implementation for a project-wide logger
class ProjectLogger:
    _instance = None
    
    @staticmethod
    def get_logger(log_level=logging.INFO, log_file=None, console_output=True):
        """
        Get or create the singleton project logger instance.
        
        Args:
            log_level: The minimum log level to record
            log_file: Path to log file
            console_output: Whether to output logs to console
            
        Returns:
            A CustomLogger instance
        """
        if ProjectLogger._instance is None:
            ProjectLogger._instance = CustomLogger(log_level, log_file, console_output)
        return ProjectLogger._instance