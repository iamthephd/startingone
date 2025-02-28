from typing import List, Tuple, Dict

def get_comparison_quarters(db) -> Dict[str, Tuple[str, str]]:
    """Fetches distinct Date values, sorts them, and determines base and compare quarters."""
    query = 'SELECT DISTINCT "Date" FROM your_table ORDER BY "Date" ASC'
    sorted_dates = [row[0] for row in db.run(query)]  # Extract dates from query result

    if len(sorted_dates) < 2:
        raise ValueError("Not enough dates for comparison.")

    return {
        "Y/Y $": (sorted_dates[0], sorted_dates[-1]),  # Oldest and newest quarters
        "Q/Q $": (sorted_dates[-2], sorted_dates[-1])  # Last two quarters
    }

def fetch_reason_data(db, reason_code: str, base_quarter: str, compare_quarter: str):
    """Fetches data for the specified reason_code and quarters."""
    query = f"""
        SELECT "Date", "Attribute", SUM("Amount") as total_amount
        FROM your_table
        WHERE "Reason_Code" = '{reason_code}' 
          AND "Date" IN ('{base_quarter}', '{compare_quarter}')
        GROUP BY "Date", "Attribute"
    """
    return db.run(query)  # Returns list of tuples (Date, Attribute, Amount)

def calculate_attribute_differences(data, base_quarter: str, compare_quarter: str) -> Dict[str, float]:
    """Calculates differences in attributes between base and compare quarters."""
    base_values = {row[1]: row[2] for row in data if row[0] == base_quarter}  # {Attribute: Amount}
    compare_values = {row[1]: row[2] for row in data if row[0] == compare_quarter}

    differences = {attr: compare_values.get(attr, 0) - base_values.get(attr, 0) 
                   for attr in set(base_values) | set(compare_values)}

    return {attr: diff for attr, diff in differences.items() if diff != 0}  # Remove zero differences

def get_top_contributors(differences: Dict[str, float]) -> Dict[str, float]:
    """Sorts by absolute value and returns the top 3 contributors."""
    sorted_diffs = sorted(differences.items(), key=lambda x: abs(x[1]), reverse=True)
    return dict(sorted_diffs[:3])

def analyze_variance_contributors(db, reason_code_tuples: List[Tuple[str, str]]):
    """Main function to analyze variance contributors for different reason codes."""
    results = {}
    quarters = get_comparison_quarters(db)  # Fetch base and compare quarters

    for reason_code, comparison_type in reason_code_tuples:
        if comparison_type not in quarters:
            raise ValueError(f"Invalid comparison type: {comparison_type}")

        base_quarter, compare_quarter = quarters[comparison_type]
        reason_data = fetch_reason_data(db, reason_code, base_quarter, compare_quarter)

        attribute_diffs = calculate_attribute_differences(reason_data, base_quarter, compare_quarter)
        top_contributors = get_top_contributors(attribute_diffs)

        results[(reason_code, comparison_type)] = top_contributors

    return results



def analyze_variance_contributors(db, reason_code_tuples):
    results = {}

    # Fetch distinct sorted quarters from database
    query_quarters = """
        SELECT DISTINCT Date FROM transactions ORDER BY Date ASC
    """
    sorted_quarters = [row[0] for row in db.run(query_quarters)]

    if len(sorted_quarters) < 2:
        raise ValueError("Not enough quarters available for comparison.")

    # Define base and compare quarters dynamically
    yy_base_quarter, yy_compare_quarter = sorted_quarters[0], sorted_quarters[-1]
    qq_base_quarter, qq_compare_quarter = sorted_quarters[-2], sorted_quarters[-1]

    # Process each Reason_Code and comparison type
    for reason_code, comparison_type in reason_code_tuples:
        if comparison_type not in ["Y/Y $", "Q/Q $"]:
            raise ValueError(f"Invalid comparison type: {comparison_type}")

        # Assign correct quarters
        if comparison_type == "Y/Y $":
            base_quarter, compare_quarter = yy_base_quarter, yy_compare_quarter
        else:  # "Q/Q $"
            base_quarter, compare_quarter = qq_base_quarter, qq_compare_quarter

        # Fetch top 3 attribute differences directly in SQL
        query_attribute_diffs = f"""
            WITH base_data AS (
                SELECT Attribute, SUM(Amount) AS base_amount
                FROM transactions
                WHERE Reason_Code = '{reason_code}' AND Date = '{base_quarter}'
                GROUP BY Attribute
            ),
            compare_data AS (
                SELECT Attribute, SUM(Amount) AS compare_amount
                FROM transactions
                WHERE Reason_Code = '{reason_code}' AND Date = '{compare_quarter}'
                GROUP BY Attribute
            ),
            differences AS (
                SELECT 
                    COALESCE(b.Attribute, c.Attribute) AS Attribute,
                    COALESCE(c.compare_amount, 0) - COALESCE(b.base_amount, 0) AS diff
                FROM base_data b
                FULL OUTER JOIN compare_data c ON b.Attribute = c.Attribute
            )
            SELECT Attribute, diff
            FROM differences
            WHERE diff <> 0
            ORDER BY ABS(diff) DESC
            FETCH FIRST 3 ROWS ONLY
        """

        top_contributors = {row[0]: row[1] for row in db.run(query_attribute_diffs)}
        results[(reason_code, comparison_type)] = top_contributors

    return results