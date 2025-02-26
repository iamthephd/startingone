import os
import argparse
import logging
from dotenv import load_dotenv
from src.utils import read_config, get_excel_files, get_file_config_by_path, ensure_directory_exists
from src.processing import process_excel_file
from src.db_operations import create_engine, load_dataframe_to_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main function to orchestrate the Excel-to-Database loading process.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Load Excel files into Oracle database")
    parser.add_argument("--config", default="config/config.yaml", help="Path to config file")
    parser.add_argument("--data-dir", default="data", help="Directory containing Excel files")
    parser.add_argument("--env-file", default=".env", help="Path to .env file with database credentials")
    args = parser.parse_args()
    
    try:
        # Ensure directories exist
        ensure_directory_exists(args.data_dir)
        ensure_directory_exists(os.path.dirname(args.config))
        
        # Load environment variables
        if os.path.exists(args.env_file):
            load_dotenv(args.env_file)
            logger.info(f"Loaded environment variables from {args.env_file}")
        else:
            logger.warning(f"Environment file {args.env_file} not found. Using system environment variables.")
        
        # Read configuration
        config = read_config(args.config)
        
        # Get database configuration
        db_config = config.get('database', {})
        
        # Create database engine
        engine = create_engine(db_config)
        
        # Get all Excel files in the data directory
        excel_files = get_excel_files(args.data_dir)
        
        if not excel_files:
            logger.warning(f"No Excel files found in {args.data_dir}")
            return
        
        # Process and load each Excel file
        for file_path in excel_files:
            logger.info(f"Processing file: {file_path}")
            
            # Get configuration for this file
            file_config = get_file_config_by_path(config, file_path)
            
            if not file_config:
                logger.warning(f"Skipping file {file_path} - no configuration found")
                continue
            
            try:
                # Process the Excel file
                df = process_excel_file(file_config, file_path)
                
                # Load the processed data into the database
                table_name = file_config.get('table_name')
                dtype_dict = file_config.get('dtype_dict', {})
                
                load_dataframe_to_db(
                    df=df,
                    table_name=table_name,
                    engine=engine,
                    dtypes_dict=dtype_dict
                )
                
                logger.info(f"Successfully processed and loaded {file_path} into {table_name}")
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
                # Continue with next file instead of stopping
                continue
        
        logger.info("Excel-to-Database loading process completed")
        
    except Exception as e:
        logger.error(f"Error in Excel-to-Database loading process: {str(e)}")
        raise

if __name__ == "__main__":
    main()