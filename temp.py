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


# Use a lightweight Python image
FROM python:3.8-slim

# Set the working directory
WORKDIR /app

# Copy the dependency file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files into the container
COPY . .

# Set the default command to run the data ingestion script
CMD ["python", "excel_to_db.py"]


# Use the same lightweight Python image
FROM python:3.8-slim

# Set the working directory
WORKDIR /app

# Copy the dependency file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files into the container
COPY . .

# Set the default command to run the main web application
CMD ["python", "main.py"]


version: '3.8'
services:
  data_ingestion:
    build:
      context: .
      dockerfile: Dockerfile.ingestion
    env_file:
      - .env
    volumes:
      - ./:/app
    # This service will run the ingestion script and then exit.
    # It can be run as a one-off job or scheduled via external orchestration.
  
  web_app:
    build:
      context: .
      dockerfile: Dockerfile.web
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./:/app
    depends_on:
      - data_ingestion
    # Optionally, you can include a wait mechanism to ensure data ingestion is complete
