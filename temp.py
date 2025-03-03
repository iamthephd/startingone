import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

# Sample DataFrame
data = pd.DataFrame({
    "A": [10, 20, 30, 40],
    "B": [50, 60, 70, 80],
    "C": [90, 100, 110, 120]
})

# Pre-highlighted cells (row, column) index
pre_selected_cells = [(0, "A"), (2, "B")]  # Example: Highlight A1 and B3

# JavaScript for conditional styling
cell_style_js = JsCode("""
function(params) {
    let selectedCells = params.context.selectedCells || [];
    let cellKey = params.node.rowIndex + '_' + params.column.colId;

    if (selectedCells.includes(cellKey)) {
        return {backgroundColor: '#D3E3FC'};  // Light blue for selection
    }
    return {};
}
""")

# Grid options setup
gb = GridOptionsBuilder.from_dataframe(data)
gb.configure_selection(selection_mode="multiple", use_checkbox=False)
gb.configure_grid_options(enableRangeSelection=True)
gb.configure_grid_options(getRowStyle=cell_style_js)
grid_options = gb.build()

# Initialize session state for selected cells
if "selected_cells" not in st.session_state:
    st.session_state["selected_cells"] = [f"{r}_{c}" for r, c in pre_selected_cells]

# Pass selected cells to JavaScript context
grid_options["context"] = {"selectedCells": st.session_state["selected_cells"]}

# Create AgGrid Table
grid_response = AgGrid(
    data,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    allow_unsafe_jscode=True
)

# Get selected cells from user interaction
selected_rows = grid_response["selected_rows"]

# Display Selected Cells
st.write("Selected Cells:", st.session_state["selected_cells"])
