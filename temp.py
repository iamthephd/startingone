import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

# Set up a sample dataframe
def create_sample_data():
    return pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eva'],
        'Age': [25, 30, 35, 40, 45],
        'City': ['New York', 'London', 'Paris', 'Tokyo', 'Berlin'],
        'Score': [85, 90, 78, 92, 88]
    })

# Main app
def main():
    st.title('AgGrid Table with Selectable Cells')
    
    df = create_sample_data()
    
    # Define pre-selected cells (by row index and column name)
    preselected_cells = [
        {'row': 0, 'col': 'Age'},  # Alice's Age
        {'row': 2, 'col': 'City'}  # Charlie's City
    ]
    
    # Build grid options
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Enable selection for all columns
    gb.configure_selection('multiple', use_checkbox=False, rowMultiSelectWithClick=False)
    
    # Add custom CSS to style the selected cells
    # This will be applied via cell renderer
    cell_style_jscode = JsCode("""
    function(params) {
        return {
            'backgroundColor': params.node.isSelected() ? '#E6F3FF' : null
        };
    }
    """)
    
    # Apply cell style to all columns
    for col in df.columns:
        gb.configure_column(col, cellStyle=cell_style_jscode)
    
    # Create preselection state if not in session_state
    if 'selected_cells' not in st.session_state:
        st.session_state.selected_cells = preselected_cells
    
    grid_options = gb.build()
    
    # Pre-select cells
    grid_options['onGridReady'] = JsCode("""
    function onGridReady(params) {
        // Get the preselected cells from Python
        const preselectedCells = JSON.parse(JSON.stringify(
            """ + str(st.session_state.selected_cells) + """
        ));
        
        // Wait for grid to be ready
        setTimeout(function() {
            preselectedCells.forEach(function(cell) {
                const rowIndex = cell.row;
                const colId = cell.col;
                
                // Get row and column
                const rowNode = params.api.getDisplayedRowAtIndex(rowIndex);
                const column = params.columnApi.getColumn(colId);
                
                if (rowNode && column) {
                    // Select the cell
                    params.api.setFocusedCell(rowIndex, colId);
                    params.api.selectCell(rowIndex, colId, true);
                }
            });
        }, 100);
    }
    """)
    
    # Display the grid
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED | GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        height=300
    )
    
    # Get the current selected cells
    selected_rows = grid_response['selected_rows']
    if selected_rows:
        st.write("Selected rows:", selected_rows)
    
    # Get selected cells
    if grid_response.get('selected_cells'):
        st.write("Selected cells:")
        selected_cells = []
        for cell in grid_response['selected_cells']:
            row_idx = cell['row_index']
            col_id = cell['col_id']
            value = df.iloc[row_idx][col_id]
            selected_cells.append({
                'row': row_idx, 
                'col': col_id, 
                'value': value,
                'row_data': df.iloc[row_idx].to_dict()
            })
            
        st.json(selected_cells)
        
        # Update session state with current selections
        st.session_state.selected_cells = [{'row': cell['row'], 'col': cell['col']} for cell in selected_cells]

if __name__ == "__main__":
    main()