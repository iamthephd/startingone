import streamlit as st
import pandas as pd
from utils import create_sample_dataframe, get_default_tuples

def format_tuple(tup: Tuple[str, str, any]) -> str:
    """Format tuple for display"""
    return f"({tup[0]}, {tup[1]}, {tup[2]})"

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'df' not in st.session_state:
        st.session_state.df = create_sample_dataframe()
    if 'tuples' not in st.session_state:
        st.session_state.tuples = []
    if 'has_defaults' not in st.session_state:
        st.session_state.has_defaults = False
    if 'default_tuples' not in st.session_state:
        st.session_state.default_tuples = []
    if 'warning_message' not in st.session_state:
        st.session_state.warning_message = None

def add_tuple(index_name: str, column_name: str):
    """Add a new tuple to the list"""
    if index_name and column_name:
        value = st.session_state.df.loc[index_name, column_name]
        new_tuple = (index_name, column_name, value)
        if new_tuple in st.session_state.tuples:
            st.session_state.warning_message = f"Tuple ({index_name}, {column_name}, {value}) already exists!"
            return
        st.session_state.warning_message = None
        st.session_state.tuples.append(new_tuple)

def auto_select():
    """Add default tuples to the current selection"""
    default_tuples = get_default_tuples(st.session_state.df)
    st.session_state.default_tuples = default_tuples
    st.session_state.has_defaults = True
    for tup in default_tuples:
        if tup not in st.session_state.tuples:
            st.session_state.tuples.append(tup)

def main():
    st.set_page_config(page_title="DataFrame Tuple Manager", layout="wide")

    # Initialize session state
    initialize_session_state()

    st.title("DataFrame Tuple Manager")

    # Create two columns with custom width ratio
    col1, col2 = st.columns([2, 1])

    # Display DataFrame in left column
    with col1:
        st.dataframe(st.session_state.df, use_container_width=True)

    # All controls in right column
    with col2:
        # Controls header with Auto button
        col_header, col_auto = st.columns([2, 1])
        with col_header:
            st.markdown("### Controls")
        with col_auto:
            if st.button("🎯 Auto", use_container_width=True):
                auto_select()

        # Create side-by-side dropdowns and add button
        col_index, col_column, col_add = st.columns([2, 2, 1])

        with col_index:
            st.markdown("**Row Index**")
            index_name = st.selectbox(
                "Select Index",
                options=st.session_state.df.index,
                key="index_select",
                label_visibility="collapsed"
            )

        with col_column:
            st.markdown("**Column Name**")
            column_name = st.selectbox(
                "Select Column",
                options=st.session_state.df.columns,
                key="column_select",
                label_visibility="collapsed"
            )

        with col_add:
            st.markdown("&nbsp;")  # Add spacing to align with dropdowns
            if st.button("➕ Add", use_container_width=True):
                add_tuple(index_name, column_name)

        # Display selected cell value
        if index_name and column_name:
            selected_value = st.session_state.df.loc[index_name, column_name]
            st.write(f"Selected Value: {selected_value}")

        # Display warning message if exists
        if st.session_state.warning_message:
            st.warning(st.session_state.warning_message)

        # Reset and Clear buttons
        col_reset, col_clear = st.columns(2)
        with col_reset:
            if st.button("🔄 Reset", use_container_width=True):
                if st.session_state.has_defaults:
                    st.session_state.tuples = st.session_state.default_tuples.copy()
                else:
                    st.info("No default selections to reset to. Use Auto to add defaults first.")

        with col_clear:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state.tuples = []

        # Display tuples
        st.markdown("### Current Tuples")
        for i, tup in enumerate(st.session_state.tuples):
            col_tuple, col_delete = st.columns([4, 1])
            with col_tuple:
                st.code(format_tuple(tup), language="python")
            with col_delete:
                if st.button("🗑️", key=f"delete_{i}"):
                    st.session_state.tuples.pop(i)
                    st.rerun()

if __name__ == "__main__":
    main()