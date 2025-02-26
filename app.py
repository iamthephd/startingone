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
db_client_path = r"C:\\instantclient_23_7"

# Loading the env variables
load_dotenv()

db_username = os.getenv('ORACLE_DB_USERNAME')
db_password = os.getenv('ORACLE_DB_PASSWORD')
db_host = os.getenv('ORACLE_DB_HOSTNAME')
db_port = os.getenv('ORACLE_DB_PORTNO')
db_service_name = os.getenv('ORACLE_DB_SERVICENAME')

oracledb.init_oracle_client(lib_dir=db_client_path)

engine = create_engine(f"oracle+oracledb://{db_username}:{db_password}@{db_host}:{db_port}/?service_name={db_service_name}")


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
    selected_file = st.selectbox("Select a file", file_list)

    # OK button
    if st.button("OK"):
        # raw_df = pd.read_sql(f"SELECT * FROM {selected_file}", con=engine)
        raw_df = pd.read_csv("temp.csv")  # REMOVE THIS
        raw_df = raw_df.round(1)

        try:
            processing_func = getattr(get_summary_table, selected_file)
            df = processing_func(raw_df)
            df = df.round(1)
        except AttributeError:
            print(f"No function defined for {selected_file}")

        st.session_state.df = df
        st.session_state.raw_df = raw_df
        st.session_state.highlighted_cells = get_reason_code(df)
        st.session_state.file_selected = True

    # Display table if file is selected
    if st.session_state.file_selected and st.session_state.df is not None:
        st.markdown("⚡ Click on cells to select/deselect them.")
        create_table(st.session_state.df, st.session_state.highlighted_cells)

    # Generate Insights button
    if st.button("Generate Insights"):
        selected_cells = []
        for i, j in st.session_state.highlighted_cells:
            row_name = st.session_state.df.index[i]
            col_name = st.session_state.df.columns[j]
            value = st.session_state.df.iloc[i, j]
            selected_cells.append((row_name, col_name, value))
        
        # Commentary generation function
        commentary = get_commentary(selected_cells, st.session_state.df, st.session_state.raw_df)
        st.markdown("### Generated Insights")
        st.markdown(f"<div class='insights-text'>{commentary}</div>", unsafe_allow_html=True)

    # Modification input
    modification = st.text_area("Enter modifications to the commentary:", height=100)
    if st.button("Apply Modifications"):
        modified_commentary = modify_commentary(modification, commentary)
        st.markdown(f"<div class='insights-text'>{modified_commentary}</div>", unsafe_allow_html=True)

    # Download button
    if st.button("Download PPT"):
        # PPT generation function
        generate_ppt(modified_commentary)

if __name__ == "__main__":
    main()