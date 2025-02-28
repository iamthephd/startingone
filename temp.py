prompt_template = PromptTemplate(
    input_variables=["values"],
    template="""
You are an expert data analyst skilled in identifying the most significant values from a dataset. 
A significant value is a number that stands out as being unusually large or small in its context, 
whether positive or negative.

Given a list of numbers, your task is to return the most significant ones as a set of 
(row_index, col_index) pairs. 

### Examples:

Input: [27, 1, -6, -18, 0, 25, 0, -1, -31, 3, -7, -29]
Output: {(0, 27), (3, -18), (5, 25), (8, -31), (11, -29)}

Input: [-6, 1, -1, -2, 0, 3, 0, 1, -18, 0, 0, 10]
Output: {(0, -6), (8, -18), (11, 10)}

Now, analyze the following dataset and return the significant values as a set of (row_index, col_index):

Input: {values}
Output:
"""
)