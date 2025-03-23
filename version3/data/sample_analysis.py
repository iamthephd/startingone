"""
Sample data provider for the Data Analysis Dashboard.
In a real application, this would connect to actual data sources or APIs.
"""

def get_sample_data():
    """
    Returns a sample dataset for display in the data analysis dashboard.
    """
    return {
        "quarters": ["Q1 2023", "Q2 2023", "Q3 2023", "Q4 2023"],
        "metrics": [
            "Revenue ($M)",
            "Profit ($M)",
            "Expenses ($M)",
            "Customer Count (K)",
            "Conversion Rate (%)",
            "Avg. Order Value ($)",
            "Customer Retention (%)"
        ],
        "values": [
            ["142.5", "156.2", "168.9", "183.4"],  # Revenue
            ["32.8", "37.5", "42.2", "48.9"],      # Profit
            ["109.7", "118.7", "126.7", "134.5"],  # Expenses
            ["86.3", "92.7", "98.1", "105.6"],     # Customer Count
            ["3.2", "3.4", "3.6", "3.9"],          # Conversion Rate
            ["82", "84", "86", "87"],              # AOV
            ["76.8", "78.2", "79.4", "81.6"]       # Retention
        ]
    }

def get_commentary(row, col):
    """
    Returns detailed commentary for a specific data point in the table.
    In a real application, this would fetch actual analysis from a database or API.
    
    Args:
        row (int): The row index
        col (int): The column index
    
    Returns:
        str: HTML formatted commentary
    """
    # Sample data to determine what we're looking at
    metrics = [
        "Revenue ($M)",
        "Profit ($M)",
        "Expenses ($M)",
        "Customer Count (K)",
        "Conversion Rate (%)",
        "Avg. Order Value ($)",
        "Customer Retention (%)"
    ]
    quarters = ["Q1 2023", "Q2 2023", "Q3 2023", "Q4 2023"]
    
    # Get metric and quarter
    metric = metrics[row] if row < len(metrics) else "Unknown"
    quarter = quarters[col] if col < len(quarters) else "Unknown"
    
    # Sample commentaries for different cells
    commentaries = {
        # Revenue commentaries
        (0, 0): f"""<strong>{metric} for {quarter}</strong> was $142.5M, representing a 12% year-over-year growth.
                    <br><br>
                    This growth was primarily driven by:
                    <ul>
                        <li>Expansion into new markets (+5%)</li>
                        <li>Increased product adoption in existing markets (+4%)</li>
                        <li>Price adjustments on premium offerings (+3%)</li>
                    </ul>
                    <br>
                    Note that this correlates with an increase in <span class="cell-reference" data-row="3" data-col="0">Customer Count</span> during the same period.
                    """,
        (0, 1): f"""<strong>{metric} for {quarter}</strong> reached $156.2M, showing a 9.6% quarter-over-quarter increase.
                    <br><br>
                    Key factors:
                    <ul>
                        <li>Seasonal boost from summer promotions</li>
                        <li>Launch of two new product lines</li>
                        <li>Successful marketing campaign (+$3.8M attributed impact)</li>
                    </ul>
                    <br>
                    This growth outpaced market expectations by approximately 2.3%.
                    """,
        (0, 2): f"""<strong>{metric} for {quarter}</strong> was $168.9M, continuing the positive trend with an 8.1% increase over Q2.
                    <br><br>
                    Contributing factors include:
                    <ul>
                        <li>Back-to-school season performance (+$5.2M)</li>
                        <li>International expansion efforts (+$4.1M)</li>
                        <li>Improved <span class="cell-reference" data-row="4" data-col="2">Conversion Rate</span> from website optimization</li>
                    </ul>
                    <br>
                    Revenue growth is expected to continue into Q4 based on current trends.
                    """,
        (0, 3): f"""<strong>{metric} for {quarter}</strong> reached $183.4M, representing the strongest quarter of the year with 8.6% growth over Q3.
                    <br><br>
                    This exceptional performance was driven by:
                    <ul>
                        <li>Holiday season sales (+$8.7M)</li>
                        <li>Year-end corporate client contracts (+$4.2M)</li>
                        <li>Successful loyalty program impact (+$2.5M)</li>
                    </ul>
                    <br>
                    The annual revenue totaled $651M, exceeding the annual target by 4.2%.
                    """,
                
        # Profit commentaries
        (1, 0): f"""<strong>{metric} for {quarter}</strong> was $32.8M, representing a profit margin of 23%.
                    <br><br>
                    Analysis:
                    <ul>
                        <li>Gross margin improvement of 2.1% year-over-year</li>
                        <li>Cost optimization initiatives saved $1.2M</li>
                        <li>New supplier agreements improved COGS by 1.5%</li>
                    </ul>
                    <br>
                    There is a direct correlation between profit increase and the reduction in <span class="cell-reference" data-row="2" data-col="0">Expenses</span>.
                    """,
        (1, 1): f"""<strong>{metric} for {quarter}</strong> reached $37.5M with a profit margin of 24%, showing improvement over Q1.
                    <br><br>
                    Key factors:
                    <ul>
                        <li>Economies of scale from higher <span class="cell-reference" data-row="0" data-col="1">Revenue</span></li>
                        <li>Operational efficiencies (+$1.8M impact)</li>
                        <li>Pricing strategy adjustments (+$1.2M impact)</li>
                    </ul>
                    <br>
                    The profit growth outpaced revenue growth, indicating improved operational efficiency.
                    """,
        
        # Default commentary for other cells
        (-1, -1): f"""<strong>{metric} for {quarter}</strong>
                    <br><br>
                    This data point shows the performance for the selected metric during the specified time period.
                    <br><br>
                    For further analysis, compare this with other quarters or related metrics in the table.
                    <br><br>
                    You can also ask the chatbot assistant for more insights about this data.
                    """
    }
    
    # Return the specific commentary if available, otherwise return the default
    return commentaries.get((row, col), commentaries.get((-1, -1)))
