import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_excel_file(file_config, file_path=None):
    """
    Generic function to process an Excel file based on its configuration.
    
    Args:
        file_config (dict): Configuration for the specific Excel file
        file_path (str, optional): Override the file path in config
        
    Returns:
        DataFrame: Processed pandas DataFrame ready for database loading
    """
    try:
        # Get file path from config or override
        path = file_path if file_path else file_config['file_path']
        sheet_name = file_config.get('sheet_name', 0)  # Default to first sheet if not specified
        
        logger.info(f"Reading Excel file: {path}, sheet: {sheet_name}")
        
        # Read the Excel file
        df = pd.read_excel(path, sheet_name=sheet_name)
        
        # Check for required columns
        required_cols = file_config.get('required_columns', [])
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in {path}: {missing_cols}")
        
        # Get the appropriate processing function based on config
        processing_func_name = file_config.get('processing_function')
        if not processing_func_name or processing_func_name not in globals():
            logger.warning(f"Processing function {processing_func_name} not found. Using basic processing.")
            return basic_processing(df, file_config)
        
        # Call the specific processing function
        processing_func = globals()[processing_func_name]
        return processing_func(df, file_config)
    
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        raise

def basic_processing(df, file_config):
    """
    Basic processing that applies to all files:
    - Selecting only required columns
    - Renaming columns based on mapping
    - Handling basic data cleaning
    
    Args:
        df (DataFrame): Raw pandas DataFrame
        file_config (dict): Configuration for the specific Excel file
        
    Returns:
        DataFrame: Processed pandas DataFrame
    """
    # Select only the columns we need
    columns_mapping = file_config.get('columns_mapping', {})
    if columns_mapping:
        # Select only mapped columns
        df = df[list(columns_mapping.keys())].copy()
        
        # Rename columns according to mapping
        df.rename(columns=columns_mapping, inplace=True)
    
    # Drop rows where all values are NaN
    df.dropna(how='all', inplace=True)
    
    return df

def process_sales_data(df, file_config):
    """
    Process sales data with specific requirements.
    
    Args:
        df (DataFrame): Raw sales data
        file_config (dict): Configuration for the sales file
        
    Returns:
        DataFrame: Processed sales DataFrame
    """
    # Apply basic processing first
    df = basic_processing(df, file_config)
    
    # Convert date columns to proper datetime format
    if 'sale_date' in df.columns:
        df['sale_date'] = pd.to_datetime(df['sale_date'], errors='coerce')
    
    # Calculate total sales amount
    if 'quantity' in df.columns and 'unit_price' in df.columns:
        df['total_amount'] = df['quantity'] * df['unit_price']
    
    # Handle missing values
    if 'quantity' in df.columns:
        df['quantity'] = df['quantity'].fillna(0)
    
    if 'unit_price' in df.columns:
        df['unit_price'] = df['unit_price'].fillna(0)
        
    # Ensure data types are correct
    if 'product_id' in df.columns:
        df['product_id'] = df['product_id'].astype(str)
    
    if 'customer_id' in df.columns:
        df['customer_id'] = df['customer_id'].astype(str)
        
    logger.info(f"Processed sales data: {len(df)} rows")
    return df

def process_inventory_data(df, file_config):
    """
    Process inventory data with specific requirements.
    
    Args:
        df (DataFrame): Raw inventory data
        file_config (dict): Configuration for the inventory file
        
    Returns:
        DataFrame: Processed inventory DataFrame
    """
    # Apply basic processing first
    df = basic_processing(df, file_config)
    
    # Convert product_id to string
    if 'product_id' in df.columns:
        df['product_id'] = df['product_id'].astype(str)
    
    # Fill missing values for numeric columns
    numeric_cols = ['quantity_in_stock', 'reorder_point', 'unit_cost']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    # Calculate stock value
    if 'quantity_in_stock' in df.columns and 'unit_cost' in df.columns:
        df['stock_value'] = df['quantity_in_stock'] * df['unit_cost']
    
    # Add a flag for items that need reordering
    if 'quantity_in_stock' in df.columns and 'reorder_point' in df.columns:
        df['needs_reorder'] = np.where(df['quantity_in_stock'] <= df['reorder_point'], 'Yes', 'No')
    
    logger.info(f"Processed inventory data: {len(df)} rows")
    return df

def process_customer_data(df, file_config):
    """
    Process customer data with specific requirements.
    
    Args:
        df (DataFrame): Raw customer data
        file_config (dict): Configuration for the customer file
        
    Returns:
        DataFrame: Processed customer DataFrame
    """
    # Apply basic processing first
    df = basic_processing(df, file_config)
    
    # Convert customer_id to string
    if 'customer_id' in df.columns:
        df['customer_id'] = df['customer_id'].astype(str)
    
    # Clean and standardize email addresses
    if 'email' in df.columns:
        df['email'] = df['email'].str.lower().str.strip()
        
    # Clean and standardize phone numbers - remove non-numeric characters
    if 'phone' in df.columns:
        df['phone'] = df['phone'].str.replace(r'[^\d+]', '', regex=True)
    
    # Standardize status values
    if 'status' in df.columns:
        df['status'] = df['status'].str.upper().str.strip()
        # Map various status values to standardized ones
        status_mapping = {
            'ACTV': 'ACTIVE',
            'ACT': 'ACTIVE',
            'A': 'ACTIVE',
            'INACT': 'INACTIVE',
            'INACTIVE': 'INACTIVE',
            'I': 'INACTIVE',
            'NEW': 'NEW',
            'N': 'NEW'
        }
        df['status'] = df['status'].map(lambda x: status_mapping.get(x, x))
    
    # Add a creation timestamp
    df['created_at'] = datetime.now()
    
    logger.info(f"Processed customer data: {len(df)} rows")
    return df