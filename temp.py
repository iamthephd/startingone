table_name = "<YOUR_TABLE_NAME>"

query = f"""
SELECT 
    (SELECT COUNT(*) 
     FROM {table_name}) AS num_samples,
    (SELECT COUNT(*) 
     FROM all_tab_columns 
     WHERE table_name = UPPER('{table_name}')) AS num_columns,
    MIN("Amount") AS min_amount,
    AVG("Amount") AS avg_amount,
    MAX("Amount") AS max_amount
FROM {table_name}
"""
