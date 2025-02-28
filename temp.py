system_message = """
You are an expert data analyst. Your task is to identify the most significant values 
in the given dataset. A significant value is an extreme positive or negative number 
that stands out in its context.

You will be provided with a dataset containing only two columns: 'Sales' and 'Revenue'.
Your output should be a **set of tuples** in the format {(row_index, col_name), ...}.

### Criteria for Significance:
- Extreme positive or negative values should be considered significant.
- The number of significant values is not fixed; it depends on the dataset.

### Examples:

Input:
[
    {"row_index": 0, "Sales": 27, "Revenue": 1},
    {"row_index": 1, "Sales": -6, "Revenue": -18},
    {"row_index": 2, "Sales": 0, "Revenue": 25},
    {"row_index": 3, "Sales": 0, "Revenue": -1},
    {"row_index": 4, "Sales": -31, "Revenue": 3},
    {"row_index": 5, "Sales": -7, "Revenue": -29}
]

Output:
{(0, "Sales"), (1, "Revenue"), (2, "Revenue"), (4, "Sales"), (5, "Revenue")}

Now, analyze the following dataset and return the set of tuples for significant values:
"""

def convert_indices_to_names(df, index_set):
    """
    Converts {(row_index, col_index), ...} to [(index_name, col_name), ...]
    using index names and column names from the dataframe.
    """
    try:
        # Convert index positions to actual index names
        index_mapping = {i: idx_name for i, idx_name in enumerate(df.index)}

        # Convert column positions to actual column names
        column_mapping = {i: col_name for i, col_name in enumerate(df.columns)}

        # Replace row indices and column indices with actual names
        converted_list = [(index_mapping[row], column_mapping[col]) for row, col in index_set if row in index_mapping and col in column_mapping]

        return converted_list
    except Exception as e:
        print(f"Error converting indices to names: {e}")
        return []  # Return empty list in case of failure
