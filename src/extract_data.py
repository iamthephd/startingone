import pandas as pd
import traceback

def efficient_pivot_from_oracle(engine, table_name, group_code_col="reason_code", value_col="amount", date_col="date"):
    """
    Generate a pivot table directly from Oracle database using SQL.
    
    Parameters:
    engine: SQLAlchemy engine or database connection
    table_name (str): Name of the database table
    group_code_col (str): Column name for rows in pivot table (default: "reason_code")
    value_col (str): Column containing values to aggregate (default: "amount")
    date_col (str): Column containing date values (default: "date")
    
    Returns:
    pd.DataFrame: Pivot table with group_code_col as rows and date columns
    """
    try:
        # First, get all distinct date values to build dynamic SQL
        date_query = f"""
        SELECT DISTINCT {date_col} FROM {table_name}
        ORDER BY {date_col}
        """
        
        # Execute the query using pandas
        date_df = pd.read_sql(date_query, con=engine)
        
        if date_df.empty:
            raise ValueError(f"No date values found in {date_col} column")
        
        date_values = date_df[date_col].tolist()
        
        # Construct the pivot column expressions
        pivot_columns = []
        for date_val in date_values:
            # Create safe column name
            safe_date = f"date_{date_val.replace('Q', 'q')}"
            pivot_columns.append(f"SUM(CASE WHEN {date_col} = '{date_val}' THEN {value_col} ELSE 0 END) / 1000000 AS {safe_date}")
        
        # Build the full pivot query
        pivot_query = f"""
        SELECT 
            {group_code_col},
            {', '.join(pivot_columns)}
        FROM {table_name}
        GROUP BY {group_code_col}
        ORDER BY {group_code_col}
        """
        
        print("Executing SQL query:")
        print(pivot_query)
        
        # Execute the query using pandas
        df = pd.read_sql(pivot_query, con=engine)
        
        # Rename columns back to original date format
        rename_dict = {f"date_{date_val.replace('Q', 'q')}": date_val for date_val in date_values}
        rename_dict[group_code_col] = group_code_col.title() if group_code_col.lower() == "reason_code" else group_code_col
        df = df.rename(columns=rename_dict)
        
        # Set group_code_col as index
        df = df.set_index(rename_dict[group_code_col])
        
        return df
        
    except Exception as e:
        print(f"Error executing Oracle query: {e}")
        print("SQL query that failed:")
        print(pivot_query if 'pivot_query' in locals() else "Query not built yet")
        print(traceback.format_exc())
        raise

def complete_pivot_analysis(engine, table_name, group_code_col="reason_code", value_col="amount", date_col="date"):
    """
    Generate a complete pivot table with YoY and QoQ calculations.
    
    Parameters:
    engine: SQLAlchemy engine or database connection
    table_name (str): Name of the database table
    group_code_col (str): Column name for rows in pivot table (default: "reason_code")
    value_col (str): Column containing values to aggregate (default: "amount")
    date_col (str): Column containing date values (default: "date")
    
    Returns:
    pd.DataFrame: Complete pivot table with all calculations
    """
    # Get the base pivot table from Oracle
    pivot_table = efficient_pivot_from_oracle(engine, table_name, group_code_col, value_col, date_col)
    
    # Compute Year-over-Year (Y/Y) and Quarter-over-Quarter (Q/Q) percentage changes
    pivot_table["Y/Y %"] = (pivot_table.iloc[:, -1] - pivot_table.iloc[:, 0]) / pivot_table.iloc[:, 0] * 100
    pivot_table["Y/Y $"] = pivot_table.iloc[:, -1] - pivot_table.iloc[:, 0]
    pivot_table["Q/Q %"] = (pivot_table.iloc[:, 4] - pivot_table.iloc[:, 3]) / pivot_table.iloc[:, 3] * 100
    pivot_table["Q/Q $"] = pivot_table.iloc[:, 4] - pivot_table.iloc[:, 3]
    
    # Sort by Y/Y % and Q/Q %
    pivot_table = pivot_table.sort_values(by=["Y/Y %", "Q/Q %"], ascending=True)
    
    # Add a Total row at the bottom
    pivot_table.loc["Total"] = pivot_table.sum()
    
    # Compute total percentage changes
    pivot_table.loc["Total", "Y/Y %"] = ((pivot_table.iloc[-1, -5] - pivot_table.iloc[-1, 0]) / pivot_table.iloc[-1, 0]) * 100
    pivot_table.loc["Total", "Q/Q %"] = ((pivot_table.iloc[-1, -4] - pivot_table.iloc[-1, 3]) / pivot_table.iloc[-1, 3]) * 100
    
    return pivot_table