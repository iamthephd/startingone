import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def perform_comprehensive_eda(df):
    """
    Perform comprehensive Exploratory Data Analysis on the given DataFrame
    
    Parameters:
    df (pandas.DataFrame): Input DataFrame with transaction data
    
    Returns:
    dict: A dictionary containing summary statistics and plot information
    """
    # Set up the plot style
    plt.style.use('seaborn')
    plt.figure(figsize=(20, 15))
    
    # 1. Summary Statistics
    def generate_column_summary(df):
        summary = {}
        for column in df.columns:
            if df[column].dtype == 'object':
                summary[column] = {
                    'type': 'categorical',
                    'unique_values': df[column].unique().tolist(),
                    'value_counts': df[column].value_counts().to_dict()
                }
            else:
                summary[column] = {
                    'type': 'numeric',
                    'total': df[column].sum(),
                    'mean': df[column].mean(),
                    'min': df[column].min(),
                    'max': df[column].max()
                }
        return summary
    
    column_summary = generate_column_summary(df)
    
    # 2. Create subplots
    fig, axs = plt.subplots(2, 3, figsize=(25, 15))
    fig.suptitle('Comprehensive Transaction Analysis', fontsize=16, fontweight='bold')
    
    # Plot 1: Transaction Amount by Quarter and Transaction Type
    plt1 = sns.boxplot(x='Date', y='Amount', hue='Transaction Type', 
                       data=df, ax=axs[0, 0], palette='viridis')
    plt1.set_title('Transaction Amount by Quarter and Type', fontsize=12)
    plt1.set_xlabel('Quarter', fontsize=10)
    plt1.set_ylabel('Amount ($)', fontsize=10)
    plt1.tick_params(axis='x', rotation=45)
    
    # Plot 2: Total Transaction Amount by Region
    region_totals = df.groupby('Region')['Amount'].sum().sort_values(ascending=False)
    plt2 = region_totals.plot(kind='bar', ax=axs[0, 1], color='skyblue', edgecolor='black')
    plt2.set_title('Total Transaction Amount by Region', fontsize=12)
    plt2.set_xlabel('Region', fontsize=10)
    plt2.set_ylabel('Total Amount ($)', fontsize=10)
    plt2.tick_params(axis='x', rotation=45)
    
    # Plot 3: Transaction Type Distribution
    plt3 = df['Transaction Type'].value_counts().plot(
        kind='pie', ax=axs[0, 2], autopct='%1.1f%%', 
        colors=['lightgreen', 'lightcoral'], 
        wedgeprops={'edgecolor': 'black', 'linewidth': 1}
    )
    plt3.set_title('Distribution of Transaction Types', fontsize=12)
    
    # Plot 4: Reason Code Distribution
    reason_counts = df['Reason Code'].value_counts()
    plt4 = reason_counts.plot(
        kind='bar', ax=axs[1, 0], 
        color='salmon', edgecolor='black'
    )
    plt4.set_title('Distribution of Reason Codes', fontsize=12)
    plt4.set_xlabel('Reason Code', fontsize=10)
    plt4.set_ylabel('Count', fontsize=10)
    plt4.tick_params(axis='x', rotation=45)
    
    # Plot 5: Heatmap of Transaction Amounts
    pivot_data = df.pivot_table(
        values='Amount', 
        index='Region', 
        columns='Transaction Type', 
        aggfunc='sum'
    )
    plt5 = sns.heatmap(
        pivot_data, 
        ax=axs[1, 1], 
        annot=True, 
        fmt='.0f', 
        cmap='YlGnBu',
        linewidths=0.5
    )
    plt5.set_title('Transaction Amounts Heatmap', fontsize=12)
    
    # Plot 6: End User Transaction Volumes
    top_10_users = df.groupby('End User')['Amount'].sum().nlargest(10)
    plt6 = top_10_users.plot(
        kind='bar', 
        ax=axs[1, 2], 
        color='lightblue', 
        edgecolor='black'
    )
    plt6.set_title('Top 10 End Users by Transaction Volume', fontsize=12)
    plt6.set_xlabel('End User', fontsize=10)
    plt6.set_ylabel('Total Transaction Amount ($)', fontsize=10)
    plt6.tick_params(axis='x', rotation=45)
    
    # Adjust layout and save
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('transaction_analysis.png', dpi=300, bbox_inches='tight')
    
    return {
        'column_summary': column_summary,
        'plots_generated': [
            'Transaction Amount by Quarter and Type',
            'Total Transaction Amount by Region',
            'Transaction Type Distribution',
            'Reason Code Distribution',
            'Transaction Amounts Heatmap',
            'Top 10 End Users by Transaction Volume'
        ]
    }

# Example usage (commented out)
# df = pd.read_csv('your_data.csv')
# eda_results = perform_comprehensive_eda(df)
# print(eda_results['column_summary'])


import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Assuming your DataFrame is named df
# Example summary information:
summary = {
    'Date': df['Date'].unique(),
    'Transaction Type': df['Transaction Type'].unique(),
    'End User Count': df['End User'].nunique(),
    'Region': df['Region'].unique(),
    'Reason Code': df['Reason Code'].unique(),
    'Total Amount': df['Amount'].sum()
}
print("Summary Information:")
print(summary)

# Create a figure with multiple subplots
fig, axes = plt.subplots(3, 2, figsize=(16, 18))
plt.subplots_adjust(hspace=0.4, wspace=0.3)

# Plot 1: Transaction Type Count
sns.countplot(data=df, x='Transaction Type', palette='Set2', ax=axes[0, 0])
axes[0, 0].set_title('Transaction Type Frequency', fontsize=14)
axes[0, 0].set_xlabel('Transaction Type', fontsize=12)
axes[0, 0].set_ylabel('Count', fontsize=12)

# Plot 2: Amount Distribution by Quarter
sns.boxplot(data=df, x='Date', y='Amount', palette='Set3', ax=axes[0, 1])
axes[0, 1].set_title('Amount Distribution per Quarter', fontsize=14)
axes[0, 1].set_xlabel('Quarter', fontsize=12)
axes[0, 1].set_ylabel('Amount ($)', fontsize=12)

# Plot 3: Total Amount by Region
# First aggregate the data
region_amount = df.groupby('Region')['Amount'].sum().reset_index()
sns.barplot(data=region_amount, x='Region', y='Amount', palette='viridis', ax=axes[1, 0])
axes[1, 0].set_title('Total Amount by Region', fontsize=14)
axes[1, 0].set_xlabel('Region', fontsize=12)
axes[1, 0].set_ylabel('Total Amount ($)', fontsize=12)
for p in axes[1, 0].patches:
    height = p.get_height()
    axes[1, 0].annotate(f'{height:,.0f}', (p.get_x() + p.get_width() / 2, height),
                        ha='center', va='bottom', fontsize=10)

# Plot 4: Reason Code Frequency
sns.countplot(data=df, x='Reason Code', palette='pastel', ax=axes[1, 1])
axes[1, 1].set_title('Reason Code Frequency', fontsize=14)
axes[1, 1].set_xlabel('Reason Code', fontsize=12)
axes[1, 1].set_ylabel('Count', fontsize=12)
axes[1, 1].tick_params(axis='x', rotation=45)

# Plot 5: Trend Over Time by Transaction Type
# Aggregate total amount by Date and Transaction Type
trend = df.groupby(['Date', 'Transaction Type'])['Amount'].sum().reset_index()
sns.lineplot(data=trend, x='Date', y='Amount', hue='Transaction Type', marker='o', ax=axes[2, 0])
axes[2, 0].set_title('Total Amount Trend by Transaction Type', fontsize=14)
axes[2, 0].set_xlabel('Quarter', fontsize=12)
axes[2, 0].set_ylabel('Total Amount ($)', fontsize=12)
axes[2, 0].tick_params(axis='x', rotation=45)

# Plot 6: (Optional) Distribution of End Users (if needed)
# Here we show the count of transactions per End User (top 10 for clarity)
top_end_users = df['End User'].value_counts().nlargest(10).index
sns.countplot(data=df[df['End User'].isin(top_end_users)], y='End User', palette='coolwarm', ax=axes[2, 1])
axes[2, 1].set_title('Top 10 End Users by Transaction Count', fontsize=14)
axes[2, 1].set_xlabel('Count', fontsize=12)
axes[2, 1].set_ylabel('End User', fontsize=12)

plt.tight_layout()
plt.show()