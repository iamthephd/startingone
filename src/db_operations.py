import pandas as pd
import sqlalchemy as sa
from sqlalchemy import text
import logging
import cx_Oracle
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
    
    Args:
        db_config (dict): Database configuration parameters
        
    Returns:
        Engine: SQLAlchemy engine object
    """
    connection_string = db_config['connection_string'].format(
        username=db_config['username'],
        password=db_config['password'],
        host=db_config['host'],
        port=db_config['port'],
        service_name=db_config['service_name']
    )
    
    logger.info(f"Creating database connection to {db_config['host']}:{db_config['port']}")
    
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