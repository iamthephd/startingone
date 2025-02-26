def cmdm_product_sql(connection, table_name, group_code_col="Reason_Code", value_col="Amount"):
    # First, get all distinct dates to build our dynamic pivot
    date_query = f'''
    SELECT DISTINCT "Date"
    FROM "{table_name}"
    ORDER BY "Date"
    '''
    
    # Get the distinct dates from the database
    date_df = pd.read_sql(date_query, con=connection)
    date_columns = date_df["Date"].tolist()
    
    # Ensure we have enough data for comparisons
    if len(date_columns) < 2:
        raise ValueError("Need at least 2 quarters of data for comparison")
    
    # Get the current and previous quarters
    latest_quarter = date_columns[-1]
    previous_quarter = date_columns[-2]
    
    # Find the year-ago quarter (same quarter previous year)
    year_ago_quarter = None
    for date in date_columns:
        if date[-2:] == latest_quarter[-2:] and date[0:4] == str(int(latest_quarter[0:4]) - 1):
            year_ago_quarter = date
            break
    
    # Prepare the column expressions for each date
    date_columns_sql = []
    for date in date_columns:
        safe_col_name = f"d_{date.replace('Q', '_Q')}"  # Make column names SQL-safe
        date_columns_sql.append(
            f'MAX(CASE WHEN "Date" = \'{date}\' THEN amount_in_millions ELSE NULL END) AS {safe_col_name}'
        )
    
    # First part of the query - creating the base aggregation
    query = f'''
    WITH base_data AS (
        SELECT 
            "{group_code_col}",
            "Date",
            SUM("{value_col}") / 1000000 AS amount_in_millions
        FROM 
            "{table_name}"
        GROUP BY 
            "{group_code_col}", "Date"
    ),
    pivot_data AS (
        SELECT
            "{group_code_col}",
            {", ".join(date_columns_sql)}
    '''
    
    # Add QoQ calculations
    latest_safe = f"d_{latest_quarter.replace('Q', '_Q')}"
    prev_safe = f"d_{previous_quarter.replace('Q', '_Q')}"
    
    query += f'''
        ,
        (MAX(CASE WHEN "Date" = '{latest_quarter}' THEN amount_in_millions ELSE NULL END) - 
         MAX(CASE WHEN "Date" = '{previous_quarter}' THEN amount_in_millions ELSE NULL END)) AS qoq_val,
        CASE 
            WHEN MAX(CASE WHEN "Date" = '{previous_quarter}' THEN amount_in_millions ELSE NULL END) = 0 THEN NULL
            ELSE (MAX(CASE WHEN "Date" = '{latest_quarter}' THEN amount_in_millions ELSE NULL END) - 
                  MAX(CASE WHEN "Date" = '{previous_quarter}' THEN amount_in_millions ELSE NULL END)) / 
                 MAX(CASE WHEN "Date" = '{previous_quarter}' THEN amount_in_millions ELSE NULL END) * 100
        END AS qoq_pct
    '''
    
    # Add YoY calculations if we have year-ago data
    if year_ago_quarter:
        year_ago_safe = f"d_{year_ago_quarter.replace('Q', '_Q')}"
        query += f'''
        ,
        (MAX(CASE WHEN "Date" = '{latest_quarter}' THEN amount_in_millions ELSE NULL END) - 
         MAX(CASE WHEN "Date" = '{year_ago_quarter}' THEN amount_in_millions ELSE NULL END)) AS yoy_val,
        CASE 
            WHEN MAX(CASE WHEN "Date" = '{year_ago_quarter}' THEN amount_in_millions ELSE NULL END) = 0 THEN NULL
            ELSE (MAX(CASE WHEN "Date" = '{latest_quarter}' THEN amount_in_millions ELSE NULL END) - 
                  MAX(CASE WHEN "Date" = '{year_ago_quarter}' THEN amount_in_millions ELSE NULL END)) / 
                 MAX(CASE WHEN "Date" = '{year_ago_quarter}' THEN amount_in_millions ELSE NULL END) * 100
        END AS yoy_pct
        '''
    
    # Complete the pivot_data CTE
    query += f'''
        FROM 
            base_data
        GROUP BY 
            "{group_code_col}"
    )
    '''
    
    # Select statement for the main results
    query += '''
    SELECT * FROM pivot_data
    '''
    
    # Add total row in a separate query and UNION
    total_sums = []
    for date in date_columns:
        safe_col_name = f"d_{date.replace('Q', '_Q')}"
        total_sums.append(f'SUM({safe_col_name}) AS {safe_col_name}')
    
    query += f'''
    UNION ALL
    SELECT 
        'Total' AS "{group_code_col}",
        {", ".join(total_sums)},
        SUM(qoq_val) AS qoq_val,
        CASE 
            WHEN SUM({prev_safe}) = 0 THEN NULL
            ELSE SUM(qoq_val) / SUM({prev_safe}) * 100
        END AS qoq_pct
    '''
    
    # Add YoY totals if applicable
    if year_ago_quarter:
        query += f'''
        ,
        SUM(yoy_val) AS yoy_val,
        CASE 
            WHEN SUM({year_ago_safe}) = 0 THEN NULL
            ELSE SUM(yoy_val) / SUM({year_ago_safe}) * 100
        END AS yoy_pct
        '''
    
    # Complete the total row query
    query += '''
    FROM 
        pivot_data
    '''
    
    # Add ORDER BY clause
    query += '''
    ORDER BY
        qoq_pct
    '''
    
    try:
        # Execute the query and load results into a DataFrame
        result_df = pd.read_sql(query, con=connection)
        
        # Set the group_code_col as the index
        result_df = result_df.set_index(group_code_col)
        
        # Create a mapping from the SQL-safe column names back to the original dates
        rename_dict = {}
        for date in date_columns:
            safe_col_name = f"d_{date.replace('Q', '_Q')}"
            rename_dict[safe_col_name] = date
        
        # Add the YoY and QoQ renames
        rename_dict.update({
            'qoq_val': 'Q/Q $',
            'qoq_pct': 'Q/Q %',
        })
        
        if year_ago_quarter:
            rename_dict.update({
                'yoy_val': 'Y/Y $',
                'yoy_pct': 'Y/Y %',
            })
        else:
            # Add empty YoY columns if we don't have year-ago data
            result_df['Y/Y $'] = None
            result_df['Y/Y %'] = None
        
        # Rename the columns
        result_df = result_df.rename(columns=rename_dict)
        
        # Reorder columns to put quarters first, followed by YoY and QoQ metrics
        date_columns_in_df = [col for col in result_df.columns if col in date_columns]
        final_columns = date_columns_in_df + ['Y/Y $', 'Y/Y %', 'Q/Q $', 'Q/Q %']
        result_df = result_df[final_columns]
        
        return result_df
    
    except Exception as e:
        print(f"Error executing SQL: {e}")
        print(f"Query: {query}")
        raise