import concurrent.futures
from typing import Any, List, Tuple, Dict
import pandas as pd
import sqlalchemy

def process_column(
    engine: Any, 
    reason_code: str, 
    comparison_type: str, 
    current_period: str, 
    previous_period: str, 
    column: str, 
    top_n: int, 
    table_name: str
) -> pd.DataFrame:
    """
    Process a single column for difference analysis in parallel.
    
    Args:
        engine: Database engine
        reason_code: Specific reason code to filter
        comparison_type: Type of comparison (Y/Y $ or Q/Q $)
        current_period: Current time period
        previous_period: Previous time period
        column: Column to analyze
        top_n: Number of top results to return
        table_name: Name of the table
    
    Returns:
        DataFrame with column analysis results
    """
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
    FETCH FIRST {top_n} ROWS ONLY
    """

    try:
        # Use a separate connection for each thread
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
            
        # Convert difference to millions and add column identifier
        df['difference_in_millions'] = df['difference'] / 1e6
        df['column_name'] = column
        
        return df
    
    except Exception as e:
        print(f"Error processing column {column}: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error

def get_top_attributes_by_difference_parallel(
    engine: Any,
    comparison_tuples: List[Tuple[str, str, int]],
    table_name: str,
    contributing_columns: List[str],
    top_n: int,
    max_workers: int = None  # Optional: control number of parallel workers
) -> Dict[Tuple[str, str, int], Dict[str, int]]:
    """
    Parallel version of top attributes difference analysis.
    
    Args:
        engine: SQLDatabase engine connected to Oracle
        comparison_tuples: List of tuples with (reason_code, comparison_type, amount)
        table_name: Name of the table containing the data
        contributing_columns: Names of the columns to consider
        top_n: Top n contributors
        max_workers: Maximum number of parallel workers (None uses default)
    
    Returns:
        Dictionary with analysis results
    """
    result = {}

    # Get distinct dates
    date_query = f"""SELECT DISTINCT "Date" FROM {table_name} ORDER BY "Date" """
    
    with engine.connect() as conn:
        dates = pd.read_sql(date_query, conn)
        dates = list(dates['Date'].values)

    # Validate quarters
    if len(dates) < 3:
        raise ValueError("The number of quarters can't be less than 3")

    for reason_code, comparison_type, amount in comparison_tuples:
        # Determine current and previous periods based on comparison type
        if comparison_type == "Y/Y $":
            current_period = dates[-1]
            previous_period = dates[0]
        elif comparison_type == "Q/Q $":
            current_period = dates[-1]
            previous_period = dates[-2]
        else:
            raise ValueError(f"Unsupported comparison type: {comparison_type}")

        # Parallel processing of columns
        all_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create futures for each column
            futures = {
                executor.submit(
                    process_column, 
                    engine, 
                    reason_code, 
                    comparison_type, 
                    current_period, 
                    previous_period, 
                    column, 
                    top_n, 
                    table_name
                ): column for column in contributing_columns
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(futures):
                df = future.result()
                if not df.empty:
                    all_results.append(df)

        # Combine and process results
        if all_results:
            combined_df = pd.concat(all_results, ignore_index=True)
            
            # Create result dictionary
            result_dict = {}
            for _, row in combined_df.iterrows():
                key = row['value_name']
                value = row['difference_in_millions']
                result_dict[key] = int(value)  # Convert to int

            # Store results for this comparison tuple
            result[(reason_code, comparison_type, amount)] = result_dict

    return result

# Example usage
def main():
    # Assume 'engine' is your SQLAlchemy database engine
    engine = sqlalchemy.create_engine('your_database_connection_string')
    
    comparison_tuples = [
        ('REASON1', 'Y/Y $', 1000),
        ('REASON2', 'Q/Q $', 500)
    ]
    
    contributing_columns = ['Column1', 'Column2', 'Column3']
    
    try:
        # Parallel processing with optional max_workers
        results = get_top_attributes_by_difference_parallel(
            engine, 
            comparison_tuples, 
            'your_table_name', 
            contributing_columns, 
            top_n=5,
            max_workers=None  # None uses default, or specify a number
        )
        
        # Process results
        for key, value in results.items():
            print(f"Analysis for {key}:")
            for attr, diff in value.items():
                print(f"  {attr}: {diff}")
    
    except Exception as e:
        print(f"Error in parallel processing: {e}")

if __name__ == '__main__':
    main()