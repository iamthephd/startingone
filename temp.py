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
    
    # Initialize an empty list to store results from each column
    all_results = []
    
    # Process each column individually
    columns_list = ["Attribute", "Revenue"]  # Your list of columns to analyze
    top_n = 3  # Set your desired number for top n per column
    
    for column in columns_list:
        # SQL query to get top n differences for a single column
        query = f"""
        WITH current_data AS (
            SELECT "{column}", SUM("Amount") as current_amount
            FROM {table_name}
            WHERE "Date" = '{current_period}'
            AND "Reason_Code" = '{reason_code}'
            GROUP BY "{column}"
        ),
        previous_data AS (
            SELECT "{column}", SUM("Amount") as previous_amount
            FROM {table_name}
            WHERE "Date" = '{previous_period}'
            AND "Reason_Code" = '{reason_code}'
            GROUP BY "{column}"
        ),
        combined_data AS (
            SELECT 
                COALESCE(c."{column}", p."{column}") as value_name,
                COALESCE(c.current_amount, 0) as current_amount,
                COALESCE(p.previous_amount, 0) as previous_amount,
                COALESCE(c.current_amount, 0) - COALESCE(p.previous_amount, 0) as difference
            FROM current_data c
            FULL OUTER JOIN previous_data p ON c."{column}" = p."{column}"
        )
        SELECT 
            value_name,
            current_amount,
            previous_amount,
            difference
        FROM combined_data
        ORDER BY ABS(difference) DESC
        LIMIT {top_n}
        """
        
        # Using pd.read_sql to get structured output
        df = pd.read_sql(query, db.connection)
        
        # Convert difference to millions
        df['difference_in_millions'] = df['difference'] / 1e6
        
        # Add column identifier
        df['column_name'] = column
        
        # Add to all results
        all_results.append(df)
    
    # Combine all results into a single dataframe
    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        
        # Create a structured dataframe with the required format
        result_df = pd.DataFrame({
            'Column': combined_df['column_name'],
            'Top n names': combined_df['value_name'],
            'Top n values': combined_df['difference_in_millions']
        })
        
        # Add absolute difference for sorting
        result_df['abs_difference'] = result_df['Top n values'].abs()
        
        # Get top n rows across all columns by absolute difference
        final_top_n = top_n  # Can be the same or different from per-column top_n
        top_df = result_df.nlargest(final_top_n, 'abs_difference', keep='all')
        
        # Remove the temporary sorting column
        top_df = top_df.drop('abs_difference', axis=1)
        
        # Create a simple dictionary with value_name as keys and difference_in_millions as values
        result_dict = {}
        for _, row in top_df.iterrows():
            key = row['Top n names']
            value = row['Top n values']
            result_dict[key] = value
        
        # Store results
        result[(reason_code, comparison_type, amount)] = result_dict