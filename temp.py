import streamlit as st
import pandas as pd
import altair as alt

# Assuming `db` is your database connection object

# Query for Line Chart
query1 = '''
    SELECT "Date", SUM(Amount) AS total_amount
    FROM your_table
    GROUP BY "Date"
    ORDER BY "Date";
'''
df_line = pd.DataFrame(db.run(query1))

# Query for Stacked Bar Chart
query2 = '''
    SELECT "Date", "Reason_Code", SUM(Amount) AS total_amount
    FROM your_table
    GROUP BY "Date", "Reason_Code"
    ORDER BY "Date", "Reason_Code";
'''
df_bar = pd.DataFrame(db.run(query2))

# Line Chart
st.subheader("Total Amount Over Time")
chart_line = alt.Chart(df_line).mark_line().encode(
    x="Date:T",
    y="total_amount:Q"
)
st.altair_chart(chart_line, use_container_width=True)

# Stacked Bar Chart
st.subheader("Total Amount Over Time by Reason Code")
chart_bar = alt.Chart(df_bar).mark_bar().encode(
    x="Date:T",
    y="total_amount:Q",
    color="Reason_Code:N"
)
st.altair_chart(chart_bar, use_container_width=True)
