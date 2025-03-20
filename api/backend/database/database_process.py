from sqlalchemy import create_engine

def create_oracle_engine(db_config):
    """
    Create SQLAlchemy engine from config
    """
    try:
        # Default to SQLite for development if no config provided
        if not db_config:
            return create_engine('sqlite:///dev.db')
            
        connection_string = db_config.get('connection_string', 'sqlite:///dev.db')
        return create_engine(connection_string)
    except Exception as e:
        print(f"Error creating database engine: {str(e)}")
        return None
