import streamlit as st
import pandas as pd
import os
from pathlib import Path

# CSS Styles - using previous working styles
st.markdown("""
<style>
.table-container {
    border: 1px solid #ddd;
    margin: 5px 0;
    transform: scale(0.9);
    transform-origin: top left;
}
.cell-button {
    width: 100% !important;
    height: 100% !important;
    padding: 2px !important;
    background-color: white;
    border: 1px solid #ddd !important;
    text-align: center !important;
    min-height: 0px !important;
}
.cell-button:hover {
    background-color: #f0f0f0;
}
.highlighted {
    background-color: red !important;
    color: white !important;
}
.header-cell {
    background-color: #f8f9fa;
    padding: 2px;
    font-weight: bold;
    text-align: center;
    border: 1px solid #ddd;
}
.index-cell {
    background-color: #f8f9fa;
    padding: 2px 8px;
    font-weight: bold;
    text-align: left;
    border: 1px solid #ddd;
    width: auto;
    white-space: nowrap;
}
.stButton button {
    width: 100% !important;
    padding: 2px !important;
    min-height: 0px !important;
}
.stButton > button {
    font-size: 8px !important;
}
.row-widget.stButton {
    margin-bottom: -15px;
}
.st-emotion-cache-1kyxreq {
    gap: 0.5rem !important;
}
.insights-text {
    margin: 10px 0;
    padding: 10px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    background-color: #f8f9fa;
}
</style>
""", unsafe_allow_html=True)

def get_file_list(folder_path):
    """Get list of Excel files from folder"""
    excel_files = [f for f in os.listdir(folder_path) if f.endswith('.xlsx')]
    return [Path(f).stem for f in excel_files]

def load_data(file_name, folder_path):
    """Load data from selected file"""
    file_path = os.path.join(folder_path, f"{file_name}.xlsx")
    return pd.read_excel(file_path)

def get_initial_highlights(df):
    """Get initial cells to highlight - replace with your logic"""
    return {(2, 3), (3, 4)}  # Example cells

def create_table(df, highlighted_cells):
    """Create interactive table"""
    st.markdown('<div class="table-container">', unsafe_allow_html=True)
    
    # Header row
    cols = st.columns([3] + [1]*len(df.columns))
    cols[0].markdown('<div class="header-cell">Metrics</div>', unsafe_allow_html=True)
    for j, col in enumerate(df.columns):
        cols[j+1].markdown(f'<div class="header-cell">{col}</div>', unsafe_allow_html=True)
    
    # Data rows
    for i in range(len(df)):
        cols = st.columns([3] + [1]*len(df.columns))
        cols[0].markdown(f'<div class="index-cell">{df.index[i]}</div>', unsafe_allow_html=True)
        
        for j in range(len(df.columns)):
            cell_value = df.iloc[i, j]
            is_highlighted = (i, j) in highlighted_cells
            button_key = f'btn_{i}_{j}'
            
            if is_highlighted:
                if cols[j+1].button(str(cell_value), key=button_key, type="primary"):
                    highlighted_cells.remove((i, j))
                    st.rerun()
            else:
                if cols[j+1].button(str(cell_value), key=button_key):
                    highlighted_cells.add((i, j))
                    st.rerun()

def main():
    st.title("Data Analysis Dashboard")
    
    # Initialize session state
    if 'highlighted_cells' not in st.session_state:
        st.session_state.highlighted_cells = set()
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'file_selected' not in st.session_state:
        st.session_state.file_selected = False
    if 'current_insights' not in st.session_state:
        st.session_state.current_insights = None
    if 'show_insights' not in st.session_state:
        st.session_state.show_insights = False
    
    # File selection
    folder_path = "your_folder_path_here"
    file_list = get_file_list(folder_path)
    selected_file = st.selectbox("Select a file", file_list)
    
    # OK button
    if st.button("OK"):
        df = load_data(selected_file, folder_path)
        st.session_state.df = df
        st.session_state.highlighted_cells = get_initial_highlights(df)
        st.session_state.file_selected = True
        st.session_state.show_insights = False  # Reset insights when new file is selected
    
    # Display table if file is selected
    if st.session_state.file_selected and st.session_state.df is not None:
        st.markdown("👆 *Click on cells to select/deselect them.*")
        create_table(st.session_state.df, st.session_state.highlighted_cells)
        
        # Generate Insights button
        if st.button("Generate Insights"):
            selected_cells = []
            for i, j in st.session_state.highlighted_cells:
                row_name = st.session_state.df.index[i]
                col_name = st.session_state.df.columns[j]
                value = st.session_state.df.iloc[i, j]
                selected_cells.append((row_name, col_name, value))
            
            # Replace with your insights generation function
            st.session_state.current_insights = "Sample insights based on selected cells"
            st.session_state.show_insights = True
        
        # Show insights section if available
        if st.session_state.show_insights:
            st.markdown("### Generated Insights")
            st.markdown(f'<div class="insights-text">{st.session_state.current_insights}</div>', 
                      unsafe_allow_html=True)
            
            # Modification input
            modification = st.text_area("Enter modifications to the commentary:", height=100)
            if st.button("Apply Modifications"):
                # Replace with your modification function
                st.session_state.current_insights = f"Modified: {st.session_state.current_insights}"
            
            # Download button
            if st.button("Download PPT"):
                # Replace with your PPT generation function
                st.success("PPT has been generated successfully!")

if __name__ == "__main__":
    main()