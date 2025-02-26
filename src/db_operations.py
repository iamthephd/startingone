import pandas as pd
import sqlalchemy as sa
from sqlalchemy import text
import logging
import cx_Oracle
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_engine(db_config):
    """
    Create a SQLAlchemy engine for Oracle database connection.
    Uses environment variables for sensitive information.
    
    Args:
        db_config (dict): Database configuration parameters (connection string template)
        
    Returns:
        Engine: SQLAlchemy engine object
    """
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment variables
    username = os.getenv('DB_USERNAME')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    service_name = os.getenv('DB_SERVICE_NAME')
    
    # Validate that all required environment variables are set
    if not all([username, password, host, port, service_name]):
        missing_vars = []
        for var_name, var_value in [
            ('DB_USERNAME', username),
            ('DB_PASSWORD', password),
            ('DB_HOST', host),
            ('DB_PORT', port),
            ('DB_SERVICE_NAME', service_name)
        ]:
            if not var_value:
                missing_vars.append(var_name)
        
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Format the connection string with values from environment variables
    connection_string = db_config['connection_string'].format(
        username=username,
        password=password,
        host=host,
        port=port,
        service_name=service_name
    )
    
    logger.info(f"Creating database connection to {host}:{port}")
    
    try:
        engine = sa.create_engine(connection_string)
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 FROM DUAL"))
            result.fetchone()
        logger.info("Database connection successful")
        return engine
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def load_dataframe_to_db(df: pd.DataFrame, 
                        table_name: str, 
                        engine: sa.engine.Engine, 
                        dtypes_dict: Dict[str, str],
                        if_exists: str = 'replace',
                        chunk_size: int = 1000) -> None:
    """
    Load a pandas DataFrame into an Oracle database table.
    
    Args:
        df (DataFrame): Processed DataFrame to load
        table_name (str): Target table name
        engine (Engine): SQLAlchemy engine
        dtypes_dict (dict): Dictionary mapping column names to Oracle data types
        if_exists (str): How to behave if the table exists ('fail', 'replace', or 'append')
        chunk_size (int): Number of rows to insert at once
        
    Returns:
        None
    """
    if df.empty:
        logger.warning(f"DataFrame is empty. No data loaded to {table_name}.")
        return
    
    try:
        # Create table if needed
        if if_exists == 'replace':
            create_table_from_dataframe(engine, table_name, df, dtypes_dict)
        
        # Insert data
        logger.info(f"Loading {len(df)} rows into {table_name}")
        
        # Convert DataFrame to database-compatible types
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Load data in chunks
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists='append' if if_exists == 'replace' else if_exists,
            index=False,
            chunksize=chunk_size,
            method='multi'
        )
        
        logger.info(f"Successfully loaded data into {table_name}")
    
    except Exception as e:
        logger.error(f"Error loading data into {table_name}: {str(e)}")
        raise

def create_table_from_dataframe(engine: sa.engine.Engine, 
                               table_name: str, 
                               df: pd.DataFrame, 
                               dtypes_dict: Dict[str, str]) -> None:
    """
    Create a table in Oracle based on DataFrame columns and specified data types.
    
    Args:
        engine (Engine): SQLAlchemy engine
        table_name (str): Target table name
        df (DataFrame): DataFrame containing the columns for the table
        dtypes_dict (dict): Dictionary mapping column names to Oracle data types
        
    Returns:
        None
    """
    # Drop table if it exists
    drop_statement = f"DROP TABLE {table_name}"
    
    # Build create table statement
    columns_definitions = []
    for col in df.columns:
        dtype = dtypes_dict.get(col, "VARCHAR(255)")
        columns_definitions.append(f"{col} {dtype}")
    
    create_statement = f"""
    CREATE TABLE {table_name} (
        {', '.join(columns_definitions)}
    )
    """
    
    with engine.connect() as conn:
        try:
            # Try to drop the table if it exists
            conn.execute(text(drop_statement))
            logger.info(f"Dropped existing table {table_name}")
        except Exception:
            # Table might not exist, which is fine
            logger.info(f"Table {table_name} does not exist yet")
        
        try:
            # Create the new table
            conn.execute(text(create_statement))
            conn.commit()
            logger.info(f"Created table {table_name}")
        except Exception as e:
            logger.error(f"Error creating table {table_name}: {str(e)}")
            raise