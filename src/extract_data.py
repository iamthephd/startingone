def cmdm_product_sql(connection, table_name, group_code_col="Reason_Code", value_col="Amount"):
    # SQL query that performs the pivot and calculations directly in the database
    query = f'''
    WITH base_data AS (
        SELECT 
            "{group_code_col}",
            "Date",
            SUM("{value_col}") / 1000000 AS "Amount_Millions"
        FROM 
            "{table_name}"
        GROUP BY 
            "{group_code_col}", "Date"
    ),
    ranked_data AS (
        SELECT 
            "{group_code_col}",
            "Date",
            "Amount_Millions",
            RANK() OVER (PARTITION BY "{group_code_col}" ORDER BY "Date") AS date_rank
        FROM 
            base_data
    ),
    max_ranks AS (
        SELECT 
            "{group_code_col}",
            MAX(date_rank) AS max_rank
        FROM 
            ranked_data
        GROUP BY 
            "{group_code_col}"
    ),
    pivot_data AS (
        SELECT 
            r."{group_code_col}",
            MAX(CASE WHEN r.date_rank = 1 THEN r."Amount_Millions" END) AS first_date_amount,
            MAX(CASE WHEN r.date_rank = 4 THEN r."Amount_Millions" END) AS q_minus_1_amount,
            MAX(CASE WHEN r.date_rank = 5 THEN r."Amount_Millions" END) AS q_current_amount,
            MAX(CASE WHEN r.date_rank = m.max_rank THEN r."Amount_Millions" END) AS last_date_amount
        FROM 
            ranked_data r
        JOIN
            max_ranks m ON r."{group_code_col}" = m."{group_code_col}"
        GROUP BY 
            r."{group_code_col}"
    ),
    final_data AS (
        SELECT 
            "{group_code_col}",
            first_date_amount,
            q_minus_1_amount,
            q_current_amount,
            last_date_amount,
            CASE 
                WHEN first_date_amount = 0 THEN NULL
                ELSE (last_date_amount - first_date_amount) / first_date_amount * 100 
            END AS "Y/Y %",
            (last_date_amount - first_date_amount) AS "Y/Y $",
            CASE 
                WHEN q_minus_1_amount = 0 THEN NULL
                ELSE (q_current_amount - q_minus_1_amount) / q_minus_1_amount * 100 
            END AS "Q/Q %",
            (q_current_amount - q_minus_1_amount) AS "Q/Q $"
        FROM 
            pivot_data
    )
    SELECT 
        *
    FROM 
        final_data
    UNION ALL
    SELECT 
        'Total' AS "{group_code_col}",
        SUM(first_date_amount) AS first_date_amount,
        SUM(q_minus_1_amount) AS q_minus_1_amount,
        SUM(q_current_amount) AS q_current_amount, 
        SUM(last_date_amount) AS last_date_amount,
        CASE 
            WHEN SUM(first_date_amount) = 0 THEN NULL
            ELSE (SUM(last_date_amount) - SUM(first_date_amount)) / SUM(first_date_amount) * 100 
        END AS "Y/Y %",
        (SUM(last_date_amount) - SUM(first_date_amount)) AS "Y/Y $",
        CASE 
            WHEN SUM(q_minus_1_amount) = 0 THEN NULL
            ELSE (SUM(q_current_amount) - SUM(q_minus_1_amount)) / SUM(q_minus_1_amount) * 100 
        END AS "Q/Q %",
        (SUM(q_current_amount) - SUM(q_minus_1_amount)) AS "Q/Q $"
    FROM 
        final_data
    ORDER BY
        "Y/Y %", "Q/Q %"
    '''
    
    # Execute the query and load results directly into a DataFrame
    result_df = pd.read_sql(query, con=connection)
    
    # Set the group_code_col as the index (like in the pandas pivot_table)
    result_df = result_df.set_index(group_code_col)
    
    return result_df