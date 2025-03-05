import streamlit as st
import pandas as pd
import os
from pathlib import Path

def main():
    st.title("LLM Commentary")

    # Initialize session state
    if 'highlighted_cells' not in st.session_state:
        st.session_state.highlighted_cells = set()  # Stores (index_name, column_name)
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'file_selected' not in st.session_state:
        st.session_state.file_selected = False

    # File selection
    excel_files = [f for f in os.listdir(EXCEL_DATA_PATH) if f.endswith('.xlsx')]
    file_list = [Path(f).stem for f in excel_files]
    st.session_state.selected_file = st.sidebar.selectbox("Select a file", file_list)

    # OK button
    if st.sidebar.button("OK"):
        st.session_state.file_config = get_file_config_by_path(config, st.session_state.selected_file)
        summary_func_name = st.session_state.file_config.get('summary_table_function')
        summary_func = globals()[summary_func_name]
        st.session_state.df = summary_func(engine)
        st.session_state.df = st.session_state.df.drop(columns=['Y/Y %', 'Q/Q %'])
        st.session_state.df = st.session_state.df.map(convert_to_int)

        # Convert highlighted cells to (index_name, column_name) pairs
        highlighted_indices = get_reason_code(st.session_state.df)
        st.session_state.highlighted_cells = {
            (st.session_state.df.index[i], st.session_state.df.columns[j]) for (i, j) in highlighted_indices
        }

        st.session_state.file_selected = True
        st.session_state.show_commentary = False  # Reset commentary when new file is selected

    # Display table if file is selected
    if st.session_state.file_selected and st.session_state.df is not None:
        st.markdown("### Summary Table (Click to Select/Deselect)")
        st.dataframe(st.session_state.df.style.applymap(
            lambda _: "background-color: yellow", 
            subset=pd.IndexSlice[
                [idx for idx, _ in st.session_state.highlighted_cells], 
                [col for _, col in st.session_state.highlighted_cells]
            ]
        ))

        # Selection UI
        st.markdown("### Select Cells to Highlight")
        reason_code = st.selectbox("Reason Code (Row)", st.session_state.df.index)
        attribute = st.selectbox("Attribute (Column)", st.session_state.df.columns)

        if st.button("Add Selection"):
            st.session_state.highlighted_cells.add((reason_code, attribute))
            st.rerun()

        # Display Selected Cells
        st.markdown("### Selected Cells")
        if st.session_state.highlighted_cells:
            selected_cells = list(st.session_state.highlighted_cells)
            to_remove = st.multiselect("Remove Selection", selected_cells, format_func=lambda x: f"{x[0]} - {x[1]}")
            if st.button("Remove Selected"):
                st.session_state.highlighted_cells -= set(to_remove)
                st.rerun()
        else:
            st.write("No cells selected.")

if __name__ == "__main__":
    main()
