import os
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st

import oracledb
from sqlalchemy import create_engine

from utils.llm import get_reason_code, get_commentary, modify_commentary
from utils.ppt_export import generate_ppt
from utils import get_summary_table


# STEP 0 : Setting up the DB engine
EXCEL_DATA_PATH = "data"
config_file = "config/config.yaml"
excel_data_dir = "data"
config = read_config(config_file)

@st.cache_resource
def load_engine(config):
    # database configuration
    db_config = config.get('database', {})
    engine = create_oracle_engine(db_config)
    return engine


def load_css():
    """Load custom CSS"""
    css_file = "utils/styles.css"
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def create_table(df, highlighted_cells):
    """Create interactive table"""
    st.markdown("<div class='table-container'>", unsafe_allow_html=True)

    # Header row
    cols = st.columns([1] + [1] * len(df.columns))
    cols[0].markdown("<div class='header-cell'>Metrics</div>", unsafe_allow_html=True)
    for j, col in enumerate(df.columns):
        cols[j + 1].markdown(f"<div class='header-cell'>{col}</div>", unsafe_allow_html=True)

    # Data rows
    for i in range(len(df)):
        cols = st.columns([1] + [1] * len(df.columns))
        cols[0].markdown(f"<div class='index-cell'>{df.index[i]}</div>", unsafe_allow_html=True)
        
        for j in range(len(df.columns)):
            cell_value = df.iloc[i, j]
            is_highlighted = (i, j) in highlighted_cells
            button_key = f'btn_{i}_{j}'

            if is_highlighted:
                if cols[j + 1].button(str(cell_value), key=button_key, type="primary"):
                    highlighted_cells.remove((i, j))
                    st.rerun()
            else:
                if cols[j + 1].button(str(cell_value), key=button_key):
                    highlighted_cells.add((i, j))
                    st.rerun()


def main():
    st.title("LLM Commentary")

    # Load CSS
    load_css()

    engine = load_engine(config)

    # Initialize session state
    if 'highlighted_cells' not in st.session_state:
        st.session_state.highlighted_cells = set()
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

        st.session_state.highlighted_cells = get_reason_code(st.session_state.df)
        st.session_state.file_selected = True
        st.session_state.show_commentary = False  # resetting commentary when new file is selected

    # Display table if file is selected
    if st.session_state.file_selected and st.session_state.df is not None:
        st.markdown("( Click on cells to select/deselect them. )")
        create_table(st.session_state.df, st.session_state.highlighted_cells)

    # Generate Insights button
    commentary_button = st.button("Generate Insights")
    
    if commentary_button:
        selected_cells = []
        for i, j in st.session_state.highlighted_cells:
            row_name = st.session_state.df.index[i]
            col_name = st.session_state.df.columns[j]
            value = st.session_state.df.iloc[i, j]
            selected_cells.append((row_name, col_name, convert_to_int(float(value))))

        # getting the top contributors
        table_name = st.session_state.file_config.get('table_name')
        top_contributors = get_top_attributes_by_difference(engine, selected_cells, table_name)
        st.session_state.selected_cells = selected_cells

        top_contributors_formatted = format_top_contributors(top_contributors)

        # generating the commentary
        st.session_state.commentary = get_commentary(top_contributors_formatted)
        st.session_state.show_commentary = True

    # showing the commentary
    if st.session_state.show_commentary:
        st.markdown("### Generated Insights")
        st.markdown(f"<div class='insights-text'>{st.session_state.commentary}</div>", unsafe_allow_html=True)

        # Download button
        selected_cells_modified = names_to_index(st.session_state.df, st.session_state.selected_cells)
        df_modified = st.session_state.df.reset_index()
        pptx_file = generate_ppt(df_modified, selected_cells_modified, st.session_state.commentary, st.session_state.selected_file)

        st.download_button(
            label="Download PPT",
            data=pptx_file,
            file_name="sample_presentation.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )


if __name__ == "__main__":
    main()