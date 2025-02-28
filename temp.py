from typing import List, Tuple, Dict

def get_comparison_quarters(db) -> Dict[str, Tuple[str, str]]:
    """Fetches distinct Date values, sorts them, and determines base and compare quarters."""
    query = 'SELECT DISTINCT "Date" FROM your_table ORDER BY "Date" ASC'
    sorted_dates = [row[0] for row in db.run(query)]  # Extract dates from query result

    if len(sorted_dates) < 2:
        raise ValueError("Not enough dates for comparison.")

    return {
        "Y/Y $": (sorted_dates[0], sorted_dates[-1]),
        "Q/Q $": (sorted_dates[-2], sorted_dates[-1])
    }

def fetch_reason_data(db, reason_code: str):
    """Fetches data for the specified reason_code from the database."""
    query = f"""
        SELECT "Date", "Attribute", "Amount"
        FROM your_table
        WHERE "Reason_Code" = '{reason_code}'
    """
    return db.run(query)  # Returns list of tuples (Date, Attribute, Amount)

def calculate_attribute_differences(data, base_quarter: str, compare_quarter: str) -> Dict[str, float]:
    """Calculates differences in attributes between base and compare quarters."""
    differences = {}

    for attribute in set(row[1] for row in data):  # Unique attributes
        base_amount = sum(row[2] for row in data if row[0] == base_quarter and row[1] == attribute)
        compare_amount = sum(row[2] for row in data if row[0] == compare_quarter and row[1] == attribute)
        
        diff = compare_amount - base_amount
        if diff != 0:
            differences[attribute] = diff

    return differences

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
        reason_data = fetch_reason_data(db, reason_code)

        attribute_diffs = calculate_attribute_differences(reason_data, base_quarter, compare_quarter)
        top_contributors = get_top_contributors(attribute_diffs)

        results[(reason_code, comparison_type)] = top_contributors

    return results
