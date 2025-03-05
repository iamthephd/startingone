import streamlit as st
import pandas as pd
import numpy as np

# Create sample dataframe
def create_sample_df():
    data = {
        'A': [1, 2, 3, 4],
        'B': [5, 6, 7, 8],
        'C': [9, 10, 11, 12],
        'D': [13, 14, 15, 16]
    }
    df = pd.DataFrame(data)
    df.index = [f'Row_{i}' for i in range(len(df))]
    return df

# Function to initialize default tuples
def get_default_tuples():
    return [
        ('Row_0', 'A', 1),
        ('Row_2', 'C', 9),
    ]

# App title
st.title('Interactive DataFrame Viewer')

# Create and display the dataframe
df = create_sample_df()

# Initialize session state for storing selected tuples if not exists
if 'selected_tuples' not in st.session_state:
    st.session_state.selected_tuples = get_default_tuples()

# Main layout
st.subheader('DataFrame')
st.dataframe(df, use_container_width=True)

# Selection and Tuple Management Row
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    # Row selection dropdown
    selected_row = st.selectbox('Select Row', options=df.index, label_visibility='visible')

with col2:
    # Column selection dropdown
    selected_column = st.selectbox('Select Column', options=df.columns, label_visibility='visible')

with col3:
    # Add Selection button (aligned with dropdowns)
    st.text(" ")  # Add a blank line to align with dropdowns
    if st.button('Add Selection', use_container_width=True):
        selected_value = df.at[selected_row, selected_column]
        new_tuple = (selected_row, selected_column, selected_value)
        if new_tuple not in st.session_state.selected_tuples:
            st.session_state.selected_tuples.append(new_tuple)
            st.experimental_rerun()

# Tuple Display and Management
st.subheader('Selected Tuples')
tuple_col1, tuple_col2 = st.columns([3, 1])

with tuple_col1:
    # Display selected tuples
    for idx, (index, column, value) in enumerate(st.session_state.selected_tuples):
        tuple_container = st.container()
        with tuple_container:
            col_a, col_b = st.columns([5, 1])
            with col_a:
                st.text(f"({index}, {column}, {value})")
            with col_b:
                if st.button("❌", key=f"delete_{idx}"):
                    st.session_state.selected_tuples.pop(idx)
                    st.experimental_rerun()

with tuple_col2:
    # Reset and Clear buttons
    if st.button("Reset to Defaults", use_container_width=True):
        st.session_state.selected_tuples = get_default_tuples()
        st.experimental_rerun()
    
    if st.button("Clear All", use_container_width=True):
        st.session_state.selected_tuples = []
        st.experimental_rerun()