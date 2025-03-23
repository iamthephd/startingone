table_name = "<YOUR_TABLE_NAME>"

query1 = f"""
SELECT 
    COUNT(*) AS num_samples,
    MIN("Amount") AS min_amount,
    AVG("Amount") AS avg_amount,
    MAX("Amount") AS max_amount
FROM {table_name}
"""

query2 = f"""
SELECT 
    COUNT(*) AS num_columns
FROM all_tab_columns
WHERE table_name = UPPER('{table_name}')
"""
