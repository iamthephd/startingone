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

# Create main layout
main_col1, main_col2 = st.columns([3, 1])

with main_col1:
    # Display the dataframe
    st.subheader('DataFrame')
    st.dataframe(df, use_container_width=True)

with main_col2:
    # Row and Column Selection
    st.subheader('Select Data Point')
    
    # Dropdowns for row and column selection
    selected_row = st.selectbox('Select Row', options=df.index)
    selected_column = st.selectbox('Select Column', options=df.columns)
    
    # Show the selected value
    selected_value = df.at[selected_row, selected_column]
    st.write(f'Selected Value: {selected_value}')
    
    # Add button to add selection
    if st.button('Add Selection'):
        new_tuple = (selected_row, selected_column, selected_value)
        if new_tuple not in st.session_state.selected_tuples:
            st.session_state.selected_tuples.append(new_tuple)
            st.experimental_rerun()

# Tuple Management Section
st.subheader('Selected Tuples')

# Columns for tuple management
col1, col2 = st.columns([3, 1])

with col1:
    # Display and manage selected tuples
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

with col2:
    # Reset and Clear buttons
    if st.button("Reset to Defaults"):
        st.session_state.selected_tuples = get_default_tuples()
        st.experimental_rerun()
    
    if st.button("Clear All"):
        st.session_state.selected_tuples = []
        st.experimental_rerun()