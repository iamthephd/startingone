def analyze_variance_contributors(db, reason_code_tuples, table_name="transactions"):
    """
    Analyze top contributors to variance across quarters for specified reason codes.
    
    Args:
        db: Database connection object with run method for executing SQL
        reason_code_tuples: List of tuples (reason_code, comparison_type)
        table_name: Name of the transactions table (default: 'transactions')
        
    Returns:
        Dictionary with (reason_code, comparison_type) keys mapping to top 3 attribute differences
    """
    results = {}
    
    # Fetch distinct sorted quarters from database
    query_quarters = f"""
        SELECT DISTINCT Date FROM {table_name} ORDER BY Date ASC
    """
    quarter_rows = db.run(query_quarters)
    sorted_quarters = [row[0] for row in quarter_rows]
    
    if len(sorted_quarters) < 2:
        raise ValueError("Not enough quarters available for comparison.")
    
    # Define base and compare quarters dynamically
    yy_compare_quarter = sorted_quarters[-1]
    yy_base_quarter = sorted_quarters[0]
    
    qq_compare_quarter = sorted_quarters[-1]
    qq_base_quarter = sorted_quarters[-2] if len(sorted_quarters) >= 2 else None
    
    # Process each Reason_Code and comparison type
    for reason_code, comparison_type in reason_code_tuples:
        if comparison_type not in ["Y/Y $", "Q/Q $"]:
            raise ValueError(f"Invalid comparison type: {comparison_type}")
        
        # Assign correct quarters based on comparison type
        if comparison_type == "Y/Y $":
            base_quarter, compare_quarter = yy_base_quarter, yy_compare_quarter
        else:  # "Q/Q $"
            if qq_base_quarter is None:
                raise ValueError("Not enough quarters available for Q/Q comparison.")
            base_quarter, compare_quarter = qq_base_quarter, qq_compare_quarter
        
        # Fetch top 3 attribute differences directly in SQL with sanitized inputs
        query_attribute_diffs = f"""
            WITH base_data AS (
                SELECT Attribute, SUM(Amount) AS base_amount
                FROM {table_name}
                WHERE Reason_Code = :reason_code_1 AND Date = :base_quarter
                GROUP BY Attribute
            ),
            compare_data AS (
                SELECT Attribute, SUM(Amount) AS compare_amount
                FROM {table_name}
                WHERE Reason_Code = :reason_code_2 AND Date = :compare_quarter
                GROUP BY Attribute
            ),
            differences AS (
                SELECT 
                    COALESCE(b.Attribute, c.Attribute) AS Attribute,
                    COALESCE(c.compare_amount, 0) - COALESCE(b.base_amount, 0) AS diff
                FROM base_data b
                FULL OUTER JOIN compare_data c ON b.Attribute = c.Attribute
            )
            SELECT Attribute, diff
            FROM differences
            WHERE diff <> 0
            ORDER BY ABS(diff) DESC
            FETCH FIRST 3 ROWS ONLY
        """
        
        # Execute query with bind parameters to prevent SQL injection
        params = {
            'reason_code_1': reason_code,
            'reason_code_2': reason_code,
            'base_quarter': base_quarter,
            'compare_quarter': compare_quarter
        }
        
        contributor_rows = db.run(query_attribute_diffs, params)
        
        # Convert result to dictionary
        top_contributors = {row[0]: row[1] for row in contributor_rows}
        results[(reason_code, comparison_type)] = top_contributors
    
    return results