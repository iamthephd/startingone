from typing import List, Tuple, Dict

def analyze_variance_contributors(db, reason_code_tuples: List[Tuple[str, str]]):
    results = {}  # Initialize results dictionary
    
    # Process each Reason_Code and comparison type pair
    for reason_code, comparison_type in reason_code_tuples:
        # Validate the comparison type
        if comparison_type not in {"Y/Y $", "Q/Q $"}:
            raise ValueError(f"Invalid comparison type: {comparison_type}")
        
        # Determine relevant quarters based on comparison type
        if comparison_type == "Y/Y $":
            base_quarter = "2024Q1"
            compare_quarter = "2025Q1"
        else:  # Q/Q $
            base_quarter = "2024Q4"
            compare_quarter = "2025Q1"
        
        # Calculate differences for each attribute using SQL
        attribute_diffs = calculate_attribute_differences(db, reason_code, base_quarter, compare_quarter)
        
        # Get top 3 contributors
        top_contributors = get_top_contributors(attribute_diffs)
        
        # Store results
        results[(reason_code, comparison_type)] = top_contributors
    
    return results

def calculate_attribute_differences(db, reason_code: str, base_quarter: str, compare_quarter: str) -> Dict[str, float]:
    # SQL query to calculate differences for each attribute in one query
    # Using string formatting instead of parameter binding
    difference_query = f"""
    WITH base_amounts AS (
        SELECT ATTRIBUTE, SUM(AMOUNT) AS base_amount
        FROM YOUR_TABLE_NAME
        WHERE REASON_CODE = '{reason_code}'
        AND DATE = '{base_quarter}'
        GROUP BY ATTRIBUTE
    ),
    compare_amounts AS (
        SELECT ATTRIBUTE, SUM(AMOUNT) AS compare_amount
        FROM YOUR_TABLE_NAME
        WHERE REASON_CODE = '{reason_code}'
        AND DATE = '{compare_quarter}'
        GROUP BY ATTRIBUTE
    )
    SELECT 
        COALESCE(b.ATTRIBUTE, c.ATTRIBUTE) AS ATTRIBUTE,
        NVL(c.compare_amount, 0) - NVL(b.base_amount, 0) AS difference
    FROM 
        base_amounts b
        FULL OUTER JOIN compare_amounts c ON b.ATTRIBUTE = c.ATTRIBUTE
    WHERE 
        NVL(c.compare_amount, 0) - NVL(b.base_amount, 0) != 0
    """
    
    # Execute query
    cursor = db.run(difference_query)
    
    # Convert results to dictionary
    differences = {}
    for row in cursor:
        differences[row[0]] = row[1]
    
    return differences

def get_top_contributors(differences: Dict[str, float]) -> Dict[str, float]:
    # Sort by absolute value but keep original difference
    sorted_diffs = sorted(
        differences.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )
    
    # Take top 3 and convert back to dictionary
    return dict(sorted_diffs[:3])