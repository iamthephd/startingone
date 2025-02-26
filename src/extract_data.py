def cmdm_product_sql(connection, table_name, group_code_col="Reason_Code", value_col="Amount"):
    # This SQL query will create a dynamic pivot based on the unique date values in your table
    # First, get all the distinct date values to use in our dynamic pivot
    date_query = f'''
    SELECT DISTINCT "Date"
    FROM "{table_name}"
    ORDER BY "Date"
    '''
    
    date_df = pd.read_sql(date_query, con=connection)
    date_columns = date_df["Date"].tolist()
    
    # Make sure we have enough quarters for calculations
    if len(date_columns) < 2:
        raise ValueError("Need at least 2 quarters of data for comparison")
    
    # Get the specific quarters for Y/Y and Q/Q comparisons
    latest_quarter = date_columns[-1]
    previous_quarter = date_columns[-2]
    
    # Try to find the year-ago quarter (same quarter last year)
    year_ago_quarter = None
    for date in date_columns:
        if date[-2:] == latest_quarter[-2:] and date[0:4] == str(int(latest_quarter[0:4]) - 1):
            year_ago_quarter = date
            break
    
    # Build a dynamic SQL query to create the pivot table
    pivot_columns = ", ".join([f'MAX(CASE WHEN "Date" = \'{date}\' THEN amount_in_millions ELSE NULL END) AS "{date}"' 
                              for date in date_columns])
    
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
            {pivot_columns},
            (MAX(CASE WHEN "Date" = '{latest_quarter}' THEN amount_in_millions ELSE NULL END) - 
             MAX(CASE WHEN "Date" = '{previous_quarter}' THEN amount_in_millions ELSE NULL END)) AS QoQ_val,
            CASE 
                WHEN MAX(CASE WHEN "Date" = '{previous_quarter}' THEN amount_in_millions ELSE NULL END) = 0 THEN NULL
                ELSE (MAX(CASE WHEN "Date" = '{latest_quarter}' THEN amount_in_millions ELSE NULL END) - 
                      MAX(CASE WHEN "Date" = '{previous_quarter}' THEN amount_in_millions ELSE NULL END)) / 
                     MAX(CASE WHEN "Date" = '{previous_quarter}' THEN amount_in_millions ELSE NULL END) * 100
            END AS QoQ_pct
    '''
    
    # Add Y/Y calculations if we have year-ago data
    if year_ago_quarter:
        query += f''',
            (MAX(CASE WHEN "Date" = '{latest_quarter}' THEN amount_in_millions ELSE NULL END) - 
             MAX(CASE WHEN "Date" = '{year_ago_quarter}' THEN amount_in_millions ELSE NULL END)) AS YoY_val,
            CASE 
                WHEN MAX(CASE WHEN "Date" = '{year_ago_quarter}' THEN amount_in_millions ELSE NULL END) = 0 THEN NULL
                ELSE (MAX(CASE WHEN "Date" = '{latest_quarter}' THEN amount_in_millions ELSE NULL END) - 
                      MAX(CASE WHEN "Date" = '{year_ago_quarter}' THEN amount_in_millions ELSE NULL END)) / 
                     MAX(CASE WHEN "Date" = '{year_ago_quarter}' THEN amount_in_millions ELSE NULL END) * 100
            END AS YoY_pct
        '''
    
    query += f'''
        FROM 
            base_data
        GROUP BY 
            "{group_code_col}"
    )
    SELECT 
        *
    FROM 
        pivot_data
    UNION ALL
    SELECT 
        'Total' AS "{group_code_col}",
    '''
    
    # Add the SUM for each date column
    for date in date_columns:
        query += f'SUM("{date}") AS "{date}", '
    
    # Add the SUM for QoQ calculations
    query += '''
        SUM(QoQ_val) AS QoQ_val,
        CASE 
            WHEN SUM("{previous_quarter}") = 0 THEN NULL
            ELSE SUM(QoQ_val) / SUM("{previous_quarter}") * 100
        END AS QoQ_pct
    '''.format(previous_quarter=previous_quarter)
    
    # Add the SUM for YoY calculations if applicable
    if year_ago_quarter:
        query += ''',
        SUM(YoY_val) AS YoY_val,
        CASE 
            WHEN SUM("{year_ago_quarter}") = 0 THEN NULL
            ELSE SUM(YoY_val) / SUM("{year_ago_quarter}") * 100
        END AS YoY_pct
        '''.format(year_ago_quarter=year_ago_quarter)
    
    query += f'''
    FROM 
        pivot_data
    ORDER BY
        QoQ_pct
    '''
    
    # If we don't have year-ago data, we'll add empty YoY columns to the DataFrame after
    has_yoy = year_ago_quarter is not None
    
    # Execute the query and load results directly into a DataFrame
    result_df = pd.read_sql(query, con=connection)
    
    # Set the group_code_col as the index (like in the pandas pivot_table)
    result_df = result_df.set_index(group_code_col)
    
    # Add empty YoY columns if needed
    if not has_yoy:
        result_df['YoY_val'] = None
        result_df['YoY_pct'] = None
    
    # Rename only the specified columns
    result_df = result_df.rename(columns={
        'YoY_pct': 'Y/Y %',
        'YoY_val': 'Y/Y $',
        'QoQ_pct': 'Q/Q %',
        'QoQ_val': 'Q/Q $'
    })
    
    # Reorder columns to put quarters first, followed by YoY and QoQ metrics
    date_columns_in_df = [col for col in result_df.columns if col not in ['Y/Y %', 'Y/Y $', 'Q/Q %', 'Q/Q $']]
    final_columns = date_columns_in_df + ['Y/Y $', 'Y/Y %', 'Q/Q $', 'Q/Q %']
    result_df = result_df[final_columns]
    
    return result_df