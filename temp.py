import streamlit as st
import pandas as pd
import numpy as np

# Set page config
st.set_page_config(layout="wide")

# Initialize session state
if 'selected_file' not in st.session_state:
    st.session_state.selected_file = None
if 'selected_cells' not in st.session_state:
    st.session_state.selected_cells = []
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'commentary' not in st.session_state:
    st.session_state.commentary = ""
if 'contributing_columns' not in st.session_state:
    st.session_state.contributing_columns = []
if 'top_n' not in st.session_state:
    st.session_state.top_n = 5

def get_summary_table(file_name):
    """Return a sample DataFrame for demonstration"""
    np.random.seed(42)
    df = pd.DataFrame({
        'Date': pd.date_range(start='2023-01-01', periods=10),
        'Sales': np.random.randint(1000, 5000, 10),
        'Revenue': np.random.randint(5000, 15000, 10),
        'Customers': np.random.randint(100, 500, 10),
        'Region': np.random.choice(['North', 'South', 'East', 'West'], 10),
        'Category': np.random.choice(['Electronics', 'Clothing', 'Food'], 10)
    })
    return df

def get_reason_code(df, file_name):
    """Return significant differences as tuples"""
    return [
        (0, 'Sales', df.loc[0, 'Sales']),
        (2, 'Revenue', df.loc[2, 'Revenue'])
    ]

def get_commentary(selected_cells, file_name, contributing_columns, top_n):
    """Generate commentary based on selected cells and parameters"""
    if not selected_cells:
        return "No cells selected for analysis."

    commentary = f"Analysis based on {len(selected_cells)} selected data points:\n\n"
    for row, col, val in selected_cells:
        commentary += f"- {col} value at row {row} is {val}\n"

    if contributing_columns:
        commentary += f"\nContributing columns considered: {', '.join(contributing_columns)}"

    commentary += f"\nAnalyzing top {top_n} significant factors."
    return commentary

def modify_commentary(user_comment):
    """Modify selected cells, contributing columns and top_n based on user comment"""
    # This is a sample implementation - in real application, this would use
    # natural language processing to understand and act on the user's comment

    # Sample modifications based on user comment
    if "focus on sales" in user_comment.lower():
        st.session_state.contributing_columns = ['Sales', 'Revenue']
        st.session_state.top_n = 3
    elif "show more items" in user_comment.lower():
        st.session_state.top_n = min(10, st.session_state.top_n + 2)
    elif "show fewer items" in user_comment.lower():
        st.session_state.top_n = max(1, st.session_state.top_n - 2)

    # Generate new commentary with modified parameters
    return get_commentary(
        st.session_state.selected_cells,
        st.session_state.selected_file,
        st.session_state.contributing_columns,
        st.session_state.top_n
    )

# Title
st.title("Interactive Dashboard")

# Sidebar
with st.sidebar:
    file_list = ["File1", "File2", "File3"]  # Replace with actual file list
    selected_file = st.selectbox("Select File", file_list)
    if st.button("Ok"):
        st.session_state.selected_file = selected_file
        st.session_state.selected_cells = []

# Main content
col_a, col_b, col_c = st.columns([3, 1, 1])

# Column A
with col_a:
    st.subheader("Data Overview")
    if st.session_state.selected_file:
        df = get_summary_table(st.session_state.selected_file)
        edited_df = st.data_editor(df, key="data_editor", hide_index=False)

        st.subheader("Cell Selection")
        left_col, right_col = st.columns(2)

        with left_col:
            st.subheader("Selection Controls")
            row_index = st.selectbox("Select Row", edited_df.index.tolist())
            column = st.selectbox("Select Column", edited_df.columns.tolist())

            if st.button("+ Add Selection"):
                if row_index is not None and column is not None:
                    value = edited_df.loc[row_index, column]
                    new_selection = (row_index, column, value)
                    if new_selection not in st.session_state.selected_cells:
                        st.session_state.selected_cells.append(new_selection)
                        st.rerun()

            contributing_cols = st.multiselect(
                "Contributing Columns",
                edited_df.columns.tolist(),
                default=st.session_state.contributing_columns,
                help="Select columns that contribute to the analysis"
            )
            st.session_state.contributing_columns = contributing_cols

            top_n = st.selectbox(
                "Top N",
                range(1, 11),
                index=st.session_state.top_n - 1,
                help="Select number of top items to display"
            )
            st.session_state.top_n = top_n

        with right_col:
            st.subheader("Selected Cells")

            if st.session_state.selected_file and not st.session_state.selected_cells:
                st.session_state.selected_cells = get_reason_code(edited_df, st.session_state.selected_file)

            for i, (row, col, val) in enumerate(st.session_state.selected_cells):
                st.write(f"({row}, {col}, {val})", end=" ")
                if st.button("×", key=f'remove_{i}', help=f'Remove selection'):
                    st.session_state.selected_cells.pop(i)
                    st.rerun()

        if st.button("Modify Commentary", use_container_width=True):
            st.session_state.commentary = get_commentary(
                st.session_state.selected_cells,
                st.session_state.selected_file,
                st.session_state.contributing_columns,
                st.session_state.top_n
            )

# Column B
with col_b:
    st.subheader("Commentary")
    if st.session_state.commentary:
        st.text_area("Generated Commentary", value=st.session_state.commentary, height=200, disabled=True)
    else:
        st.info("Click 'Modify Commentary' to generate analysis")

    st.subheader("Commentary Chat")
    for message in st.session_state.chat_messages:
        st.text(message)

    user_comment = st.text_input("Type your comment to modify analysis", key="commentary_input")
    if st.button("Update Commentary", key="update_commentary"):
        if user_comment:
            st.session_state.chat_messages.append(f"You: {user_comment}")
            st.session_state.commentary = modify_commentary(user_comment)
            st.session_state.chat_messages.append(f"System: Commentary updated based on your input")
            st.rerun()

# Column C
with col_c:
    st.subheader("Chatbot")
    st.info("Chatbot interface will be implemented in future updates")