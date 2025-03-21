import pandas as pd
from sqlalchemy import text

def get_summary_table(engine):
    """
    Generic function to fetch summary table data
    """
    # Example implementation - replace with actual logic
    try:
        query = text("""
            SELECT * FROM summary_table
            LIMIT 10
        """)
        df = pd.read_sql_query(query, engine)
        return df
    except Exception as e:
        print(f"Error fetching summary table: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error
