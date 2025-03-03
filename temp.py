import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Assuming `db` is your database connection object

# Query for Line Chart
query1 = '''
    SELECT "Date", SUM(Amount) AS total_amount
    FROM your_table
    GROUP BY "Date"
    ORDER BY "Date";
'''
df_line = pd.DataFrame(db.run(query1))
df_line["total_amount"] = df_line["total_amount"].astype(float) / 1e6  # Convert to millions

# Query for Stacked Bar Chart
query2 = '''
    SELECT "Date", "Reason_Code", SUM(Amount) AS total_amount
    FROM your_table
    GROUP BY "Date", "Reason_Code"
    ORDER BY "Date", "Reason_Code";
'''
df_bar = pd.DataFrame(db.run(query2))
df_bar["total_amount"] = df_bar["total_amount"].astype(float) / 1e6  # Convert to millions

# Set up figure
fig, ax = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

# Line Chart
sns.lineplot(data=df_line, x="Date", y="total_amount", marker="o", ax=ax[0], color="b")
ax[0].set_title("Total Amount Over Time", fontsize=14)
ax[0].set_ylabel("Total Amount ($M)")
ax[0].grid(True)

# Stacked Bar Chart
sns.barplot(data=df_bar, x="Date", y="total_amount", hue="Reason_Code", ax=ax[1])
ax[1].set_title("Total Amount Over Time by Reason Code", fontsize=14)
ax[1].set_xlabel("Date")
ax[1].set_ylabel("Total Amount ($M)")
ax[1].legend(title="Reason Code", bbox_to_anchor=(1.05, 1), loc="upper left")
ax[1].grid(True)

plt.xticks(rotation=45)
plt.tight_layout()
plt.show()