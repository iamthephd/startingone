from sqlalchemy import create_engine, text

# Database connection setup
engine = create_engine('oracle+cx_oracle://username:password@hostname:port/service_name')

# SQL query to fetch only column names and their comments/metadata
SQL_QUERY = """
SELECT column_name, comments as metadata
FROM all_col_comments
WHERE table_name = 'YOUR_TABLE_NAME'
AND owner = 'YOUR_SCHEMA'
ORDER BY column_id
"""

# Execute query and fetch results
with engine.connect() as conn:
    results = conn.execute(text(SQL_QUERY))
    columns_metadata = results.fetchall()

# Format as requested in prompt template
formatted_metadata = ""
for col_name, metadata in columns_metadata:
    formatted_metadata += f"{col_name} : {metadata}\n"

# Create system prompt with the metadata
system_prompt = f"""
Table Column Details:
{formatted_metadata}
"""

print(system_prompt)