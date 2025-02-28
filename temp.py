from typing import List, Tuple, Dict, Any
from decimal import Decimal
import ast
import re

def process_query_results(rows_str: str) -> List[Tuple[str, float]]:
    """
    Process the string output from database query into a list of tuples with Python data types.
    
    Args:
        rows_str: String representation of query results in format "[('Attribute_Value', Decimal('-21434123.234231'), ...]"
    
    Returns:
        List of tuples with attribute and difference value as (attribute, difference)
    """
    # Check if rows_str is empty
    if not rows_str or rows_str.strip() == "[]":
        return []
    
    try:
        # Method 1: Try to convert string to Python object using ast.literal_eval
        # This works if the string is a valid Python literal representation
        processed_rows = []
        
        # Clean the string to make it compatible with literal_eval
        # Replace Decimal objects with their string representation
        rows_cleaned = re.sub(r'Decimal\([\'"](-?\d+\.?\d*?)[\'"]\)', r"'\1'", rows_str)
        
        # Parse the string as a Python literal
        rows_list = ast.literal_eval(rows_cleaned)
        
        # Extract attribute and difference values
        for row in rows_list:
            if len(row) >= 2:
                attribute = row[0]
                # Convert string or Decimal to float
                difference = float(row[1]) if isinstance(row[1], (str, Decimal)) else row[1]
                processed_rows.append((attribute, difference))
        
        return processed_rows
        
    except (SyntaxError, ValueError):
        # Method 2: Parse the string manually if literal_eval fails
        processed_rows = []
        
        # Regular expression to extract tuples
        pattern = r"\('([^']+)',\s*(?:Decimal\(['\"])?(-?\d+\.?\d*?)(?:['\"])?\)"
        matches = re.findall(pattern, rows_str)
        
        for attribute, difference in matches:
            processed_rows.append((attribute, float(difference)))
        
        return processed_rows

def get_top_attributes_by_difference(
    db: Any,
    comparison_tuples: List[Tuple[str, str]],
    table_name: str
) -> Dict[Tuple[str, str], Dict[str, float]]:
    """
    Get top 3 attributes by difference (Y/Y $ or Q/Q $) for specified reason codes.
    
    Args:
        db: SQLDatabase instance connected to Oracle
        comparison_tuples: List of tuples with (reason_code, comparison_type)
                          where comparison_type is either "Y/Y $" or "Q/Q $"
        table_name: Name of the table containing the data
    
    Returns:
        Dictionary with (reason_code, comparison_type) as keys and
        dictionary of top 3 attributes with their differences as values
    """
    result = {}
    
    for reason_code, comparison_type in comparison_tuples:
        # Determine comparison quarters based on type
        if comparison_type == "Y/Y $":
            current_period = "2025Q1"
            previous_period = "2024Q1"
        elif comparison_type == "Q/Q $":
            current_period = "2025Q1"
            previous_period = "2024Q4"
        else:
            raise ValueError(f"Unsupported comparison type: {comparison_type}")
        
        # Construct and execute SQL query to get attribute differences
        query = f"""
        WITH current_data AS (
            SELECT "Attribute", SUM("Amount") as current_amount
            FROM {table_name}
            WHERE "Date" = '{current_period}'
            AND "Reason_Code" = '{reason_code}'
            GROUP BY "Attribute"
        ),
        previous_data AS (
            SELECT "Attribute", SUM("Amount") as previous_amount
            FROM {table_name}
            WHERE "Date" = '{previous_period}'
            AND "Reason_Code" = '{reason_code}'
            GROUP BY "Attribute"
        )
        SELECT 
            COALESCE(c."Attribute", p."Attribute") as attribute,
            COALESCE(c.current_amount, 0) - COALESCE(p.previous_amount, 0) as difference
        FROM current_data c
        FULL OUTER JOIN previous_data p ON c."Attribute" = p."Attribute"
        ORDER BY ABS(COALESCE(c.current_amount, 0) - COALESCE(p.previous_amount, 0)) DESC
        FETCH FIRST 3 ROWS ONLY
        """
        
        # Execute query
        rows = db.run(query)
        
        # Process the query results
        processed_rows = process_query_results(rows)
        
        # Convert to required dictionary format
        attributes_diff = {attr: diff for attr, diff in processed_rows}
        
        # Store results
        result[(reason_code, comparison_type)] = attributes_diff
    
    return result