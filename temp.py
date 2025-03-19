import streamlit as st

# Initialize session state to store the list of tuples if it doesn't exist
if 'tuple_list' not in st.session_state:
    # Example initial data - replace with your actual data
    st.session_state.tuple_list = [
        ('Apple', 1.2, 'Red'),
        ('Banana', 0.8, 'Yellow'),
        ('Orange', 1.5, 'Orange'),
        ('Grape', 2.0, 'Purple'),
        ('Kiwi', 1.8, 'Green'),
    ]

# App title
st.title("Tuple List Manager")

# Create nice string representations for the tuples to display in the multiselect
tuple_display = [f"{t[0]} - ${t[1]} - {t[2]}" for t in st.session_state.tuple_list]

# Use multiselect to show all items and let users deselect to remove
selected_indices = st.multiselect(
    "Select items to keep (uncheck to remove):",
    options=range(len(tuple_display)),
    default=range(len(tuple_display)),
    format_func=lambda i: tuple_display[i]
)

# Update the tuple list based on selected indices
if len(selected_indices) != len(st.session_state.tuple_list):
    # Create a new list with only the selected items
    st.session_state.tuple_list = [st.session_state.tuple_list[i] for i in selected_indices]
    st.success("List updated!")

# Option to add a new tuple
st.divider()
st.subheader("Add New Item")

# Create a form for better layout without columns
with st.form(key="add_item_form", clear_on_submit=True):
    new_item1 = st.text_input("Item Name")
    new_item2 = st.number_input("Price", format="%.1f", step=0.1, min_value=0.0)
    new_item3 = st.text_input("Color")