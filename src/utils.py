import yaml
import os
import glob
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_config(config_path: str) -> Dict[str, Any]:
    """
    Read and parse the YAML configuration file.
    
    Args:
        config_path (str): Path to the YAML config file
        
    Returns:
        dict: Parsed configuration dictionary
    """
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        logger.info(f"Successfully loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error reading config file {config_path}: {str(e)}")
        raise

def get_excel_files(data_dir: str, file_pattern: str = "*.xlsx") -> List[str]:
    """
    Get a list of Excel files in the specified directory.
    
    Args:
        data_dir (str): Directory containing Excel files
        file_pattern (str): Glob pattern to match Excel files
        
    Returns:
        list: List of file paths matching the pattern
    """
    file_pattern_path = os.path.join(data_dir, file_pattern)
    excel_files = glob.glob(file_pattern_path)
    
    if not excel_files:
        logger.warning(f"No Excel files found matching pattern {file_pattern_path}")
    else:
        logger.info(f"Found {len(excel_files)} Excel files in {data_dir}")
    
    return excel_files

def get_file_config_by_path(config: Dict[str, Any], file_path: str) -> Optional[Dict[str, Any]]:
    """
    Find the configuration for a specific Excel file based on its path.
    
    Args:
        config (dict): Full configuration dictionary
        file_path (str): Path to the Excel file
        
    Returns:
        dict: Configuration for the specific file or None if not found
    """
    file_name = os.path.basename(file_path)
    excel_files_config = config.get('excel_files', {})
    
    # Try to find an exact match first
    for file_key, file_config in excel_files_config.items():
        if os.path.basename(file_config.get('file_path', '')) == file_name:
            return file_config
    
    # If no exact match, try to match by file name without extension
    file_name_no_ext = os.path.splitext(file_name)[0]
    for file_key, file_config in excel_files_config.items():
        config_file_name = os.path.basename(file_config.get('file_path', ''))
        config_file_name_no_ext = os.path.splitext(config_file_name)[0]
        
        if file_name_no_ext.lower() == config_file_name_no_ext.lower():
            return file_config
    
    logger.warning(f"No configuration found for file {file_path}")
    return None

def ensure_directory_exists(directory: str) -> None:
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory (str): Directory path to check/create
        
    Returns:
        None
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")