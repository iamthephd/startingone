from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

def check_and_drop_table(engine, table_name):
    """
    Check if a table exists and drop it if it does.
    
    Args:
        engine: SQLAlchemy engine
        table_name (str): Name of the table to check and potentially drop
    
    Returns:
        bool: True if table was dropped, False if table didn't exist
    """
    try:
        # Create an inspector
        inspector = inspect(engine)
        
        # Check if table exists
        if inspector.has_table(table_name):
            # If table exists, drop it
            with engine.connect() as conn:
                conn.execute(f'DROP TABLE "{table_name}"')
                conn.commit()
            print(f"Table {table_name} dropped successfully.")
            return True
        else:
            print(f"Table {table_name} does not exist.")
            return False
    
    except SQLAlchemyError as e:
        print(f"An error occurred while checking/dropping table: {e}")
        return False