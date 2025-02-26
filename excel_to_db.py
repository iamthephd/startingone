import os
import time
from typing import Dict, Optional
from dotenv import load_dotenv
import pandas as pd
import oracledb
from sqlalchemy import create_engine



# STEP 0 : Setting up the DB engine
EXCEL_DATA_PATH = "data"
db_client_path = r"C:\\instantclient_23_7"

# Loading the env variables
load_dotenv()

db_username = os.getenv('ORACLE_DB_USERNAME')
db_password = os.getenv('ORACLE_DB_PASSWORD')
db_host = os.getenv('ORACLE_DB_HOSTNAME')
db_port = os.getenv('ORACLE_DB_PORTNO')
db_service_name = os.getenv('ORACLE_DB_SERVICENAME')

oracledb.init_oracle_client(lib_dir=db_client_path)

engine = create_engine(f"oracle+oracledb://{db_username}:{db_password}@{db_host}:{db_port}/?service_name={db_service_name}")


def upload_dataframe_to_oracle(
    df: pd.DataFrame,
    table_name: str,
    engine: create_engine,
    schema: Optional[str] = None,
    if_exists: str = 'append',
    dtype_dict: Optional[Dict] = None,
    chunksize: int = 10000,
    max_retries: int = 3,
    retry_delay: int = 5
) -> None:
    """
    Upload a large DataFrame to Oracle database in chunks with retry mechanism.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The DataFrame to upload
    table_name : str
        Name of the target table
    engine : sqlalchemy.engine.Engine
        SQLAlchemy engine instance
    schema : str, optional
        Database schema name
    if_exists : str, default 'append'
        How to behave if the table exists:
        - 'fail': Raise a ValueError
        - 'replace': Drop the table before inserting new values
        - 'append': Insert new values to the existing table
    dtype_dict : dict, optional
        Dictionary of column name to SQL type mapping
    chunksize : int, default 10000
        Number of rows to insert at once
    max_retries : int, default 3
        Maximum number of retry attempts for failed chunks
    retry_delay : int, default 5
        Delay in seconds between retry attempts
    """
    total_rows = len(df)
    rows_processed = 0
    
    # Calculate number of chunks
    num_chunks = (total_rows + chunksize - 1) // chunksize
    
    print(f"Starting upload of {total_rows} rows in {num_chunks} chunks...")
    
    for i in range(0, total_rows, chunksize):
        chunk = df.iloc[i:i + chunksize]
        chunk_num = i // chunksize + 1
        retries = 0
        
        while retries < max_retries:
            try:
                # For the first chunk, handle table creation/replacement
                if i == 0:
                    current_if_exists = if_exists
                else:
                    current_if_exists = 'append'
                
                # Upload the chunk without using method='multi'
                chunk.to_sql(
                    name=table_name,
                    con=engine,
                    schema=schema,
                    if_exists=current_if_exists,
                    index=False,
                    dtype=dtype_dict,
                    chunksize=None  # Upload this chunk as a single transaction
                )
                
                rows_processed += len(chunk)
                print(f"Chunk {chunk_num}/{num_chunks} uploaded successfully. "
                      f"Progress: {rows_processed}/{total_rows} rows ({(rows_processed/total_rows*100):.1f}%)")
                break
                
            except Exception as e:
                retries += 1
                if retries < max_retries:
                    print(f"Error uploading chunk {chunk_num}: {str(e)}")
                    print(f"Retrying in {retry_delay} seconds... (Attempt {retries + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    raise Exception(f"Failed to upload chunk {chunk_num} after {max_retries} attempts. "
                                  f"Last error: {str(e)}")
    
    print(f"Upload completed successfully. {rows_processed} total rows uploaded.")