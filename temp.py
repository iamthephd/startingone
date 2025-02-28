from langchain_community.utilities.sql_database import SQLDatabase
from typing import List, Tuple, Dict, Any
import re

def get_top_attributes_by_difference(
    db: SQLDatabase,
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
        
        # Parse results and format into dictionary
        attributes_diff = {}
        
        # Oracle's SQLPlus output format typically includes headers and formatting
        # We need to parse this properly
        row_pattern = re.compile(r'(\S+)\s+(-?\d+\.?\d*)')
        for line in rows.strip().split('\n'):
            if line and not line.startswith('----') and 'ATTRIBUTE' not in line:
                match = row_pattern.search(line)
                if match:
                    attribute = match.group(1)
                    difference = float(match.group(2))
                    attributes_diff[attribute] = difference
        
        # Alternative parsing if the above doesn't work (depends on how db.run returns data)
        if not attributes_diff:
            lines = rows.strip().split('\n')
            if len(lines) > 1:  # Skip header row
                for line in lines[1:]:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        attribute = parts[0]
                        try:
                            difference = float(parts[-1])
                            attributes_diff[attribute] = difference
                        except ValueError:
                            pass
        
        # Store results
        result[(reason_code, comparison_type)] = attributes_diff
    
    return result