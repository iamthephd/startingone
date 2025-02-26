import pandas as pd


def cmdm_product_sql(engine, table_name, group_code_col="Reason_Code", value_col="Amount"):
    """
    Generate a pivot table directly using Oracle SQL to improve performance.
    
    Parameters:
    -----------
    engine : sqlalchemy.engine.Engine
        The SQLAlchemy engine or connection to use
    table_name : str
        The name of the table to query
    group_code_col : str, default="Reason_Code"
        The column to use as row index
    value_col : str, default="Amount"
        The column containing values to aggregate
        
    Returns:
    --------
    pd.DataFrame
        Pivot table with initial aggregation done in SQL
    """
    # First, get the unique dates to build the dynamic pivot query
    date_query = f"""
    SELECT DISTINCT "Date" 
    FROM {table_name}
    ORDER BY "Date"
    """
    
    with engine.connect() as conn:
        # Get unique dates to build the pivot columns
        dates = pd.read_sql(date_query, conn)
        date_list = dates["Date"].tolist()
        
        # Build the pivot query with dynamic columns
        pivot_cols = ", ".join([f"'{date}' AS \"{date}\"" for date in date_list])
        
        # The main pivot query
        pivot_query = f"""
        SELECT *
        FROM (
            SELECT 
                "{group_code_col}",
                "Date",
                SUM("{value_col}") / 1000000 AS amount_in_millions
            FROM {table_name}
            GROUP BY "{group_code_col}", "Date"
        )
        PIVOT (
            SUM(amount_in_millions)
            FOR "Date" IN ({pivot_cols})
        )
        ORDER BY "{group_code_col}"
        """
        
        # Execute the query and load results into pandas
        pivot_df = pd.read_sql(pivot_query, conn)
        
        # Calculate Y/Y and Q/Q metrics in pandas
        if len(date_list) >= 5:  # Ensure we have enough data points
            pivot_df["Y/Y $"] = pivot_df[date_list[-1]] - pivot_df[date_list[0]]
            pivot_df["Y/Y %"] = (pivot_df[date_list[-1]] - pivot_df[date_list[0]]) / pivot_df[date_list[0]] * 100
            pivot_df["Q/Q $"] = pivot_df[date_list[-2]] - pivot_df[date_list[-3]]
            pivot_df["Q/Q %"] = (pivot_df[date_list[-2]] - pivot_df[date_list[-3]]) / pivot_df[date_list[-3]] * 100
            
            # Sort by Y/Y % and Q/Q %
            pivot_df = pivot_df.sort_values(by=["Y/Y %", "Q/Q %"], ascending=True)
        
        # Add a Total row
        pivot_df.loc["Total"] = pivot_df.sum(numeric_only=True)
        
        # Compute total percentage changes for the Total row
        if len(date_list) >= 5:
            pivot_df.loc["Total", "Y/Y %"] = ((pivot_df.loc["Total", date_list[-1]] - 
                                              pivot_df.loc["Total", date_list[0]]) / 
                                              pivot_df.loc["Total", date_list[0]]) * 100
            
            pivot_df.loc["Total", "Q/Q %"] = ((pivot_df.loc["Total", date_list[-2]] - 
                                              pivot_df.loc["Total", date_list[-3]]) / 
                                              pivot_df.loc["Total", date_list[-3]]) * 100
        
        return pivot_df