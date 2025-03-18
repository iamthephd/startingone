for reason_code, comparison_type, amount in comparison_tuples:
    # comparison quarters based on type (to be modified)
    if comparison_type == "Y/Y $":
        current_period = dates[-1]
        previous_period = dates[0]
    elif comparison_type == "Q/Q $":
        current_period = dates[-1]
        previous_period = dates[-2]
    else:
        raise ValueError(f"Unsupported comparison type: {comparison_type}")
    
    # SQL query to get differences for multiple attributes
    columns_list = ["Attribute", "Sales", "Revenue"]  # Your list of columns to analyze
    # Handle case where columns_list has a single element
    columns_str = ", ".join([f'"{col}"' for col in columns_list])
    
    query = f"""
    WITH current_data AS (
        SELECT {columns_str}, SUM("Amount") as current_amount
        FROM {table_name}
        WHERE "Date" = '{current_period}'
        AND "Reason_Code" = '{reason_code}'
        GROUP BY {columns_str}
    ),
    previous_data AS (
        SELECT {columns_str}, SUM("Amount") as previous_amount
        FROM {table_name}
        WHERE "Date" = '{previous_period}'
        AND "Reason_Code" = '{reason_code}'
        GROUP BY {columns_str}
    )
    SELECT 
        {', '.join([f'COALESCE(c."{col}", p."{col}") as "{col}"' for col in columns_list])},
        COALESCE(c.current_amount, 0) as current_amount,
        COALESCE(p.previous_amount, 0) as previous_amount,
        COALESCE(c.current_amount, 0) - COALESCE(p.previous_amount, 0) as difference
    FROM current_data c
    FULL OUTER JOIN previous_data p ON {' AND '.join([f'c."{col}" = p."{col}"' for col in columns_list])}
    """
    
    # Using pd.read_sql to get structured output
    df = pd.read_sql(query, db.connection)
    
    # Convert difference to millions for display purposes
    df['difference_in_millions'] = df['difference'] / 1e6
    
    # Create a new column to identify the column value to use as the key
    # For each row, find the non-null value from the columns_list
    def get_key_value(row):
        for col in columns_list:
            if pd.notna(row[col]):
                return row[col]
        return None
    
    df['key_value'] = df.apply(get_key_value, axis=1)
    
    # Add absolute difference for sorting
    df['abs_difference'] = df['difference'].abs()
    
    # Get top n rows by absolute difference
    top_n = 3  # Set your desired number
    top_df = df.nlargest(top_n, 'abs_difference', keep='all')
    
    # Create a simple dictionary with key_value as keys and difference_in_millions as values
    result_dict = {}
    for _, row in top_df.iterrows():
        key = row['key_value']
        value = row['difference_in_millions']  # Already in millions
        result_dict[key] = value
    
    # Store results
    result[(reason_code, comparison_type, amount)] = result_dict