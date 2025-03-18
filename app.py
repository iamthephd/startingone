import os
from pathlib import Path
from typing import List, Tuple
import streamlit as st
import pandas as pd
from langchain_community.utilities import SQLDatabase

from utils.helper import read_config, get_file_config_by_path, convert_to_int, format_top_contributors, names_to_index
from utils.ppt_export import generate_ppt
from database.get_summary_table import *
from database.database_process import create_oracle_engine
from database.get_top_contributors import get_top_attributes_by_difference
from llm.reson_code import get_reason_code
from llm.commentary import get_commentary

# setting up the DB engine
EXCEL_DATA_PATH = "data"
config_file = "config/config.yaml"
excel_data_dir = "data"
config = read_config(config_file)

# caching the resources to avoid loading multiple times
@st.cache_resource
def load_engine(config):
    # database configuration
    db_config = config.get('database', {})
    engine = create_oracle_engine(db_config)
    db = SQLDatabase(engine)
    return engine, db

# CHECK FOR ALTERNATIVE FOR LANGCHAIN SQLDATABASE
# MAX RETRIES

# loading the style
def load_custom_css():
    """Load custom CSS styles"""
    with open("styles/custom.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# setting up the states, as these variable will be used throughout the code
def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'file_selected' not in st.session_state:
        st.session_state.file_selected = False
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'tuples' not in st.session_state:
        st.session_state.tuples = []
    if 'has_defaults' not in st.session_state:
        st.session_state.has_defaults = False
    if 'default_tuples' not in st.session_state:
        st.session_state.default_tuples = []
    if 'warning_message' not in st.session_state:
        st.session_state.warning_message = None
    if 'insights' not in st.session_state:
        st.session_state.insights = None

# helper function to get the default tuples
def get_default_tuples(df: pd.DataFrame) -> List[Tuple[str, str, any]]:
    """Generate default tuples from the DataFrame"""
    if df is None:
        return []
    index_name = df.index[0]
    column_name = df.columns[0]
    return [(index_name, column_name, df.loc[index_name, column_name])]

# helper function to format the tuple
def format_tuple(tup: Tuple[str, str, any]) -> str:
    """Format tuple for display"""
    return f"({tup[0]}, {tup[1]}, {tup[2]})"

# adding tuple to the current list
def add_tuple(index_name: str, column_name: str):
    """Add a new tuple to the list"""
    if index_name and column_name:
        value = st.session_state.df.loc[index_name, column_name]
        new_tuple = (index_name, column_name, value)
        if new_tuple in st.session_state.tuples:
            st.session_state.warning_message = f" The data ({index_name}, {column_name}, {value}) already exists!"
            return
        st.session_state.warning_message = None
        st.session_state.tuples.append(new_tuple)
        st.session_state.insights = None

# llm selecting the reason code
def auto_select():
    """Add default tuples to the current selection"""
    default_tuples = get_reason_code(st.session_state.df, st.session_state.selected_file)
    st.session_state.default_tuples = default_tuples
    st.session_state.has_defaults = True
    for tup in default_tuples:
        if tup not in st.session_state.tuples:
            st.session_state.tuples.append(tup)

# processing and getting the data
def handle_file_selection():
    """Handle file selection and processing"""
    st.session_state.file_selected = True
    filename = st.session_state.selected_file
    st.session_state.file_config = get_file_config_by_path(config, filename)
    summary_func_name = st.session_state.file_config.get('summary_table_function')
    summary_func = globals()[summary_func_name]
    df = summary_func(st.session_state.engine)
    df = df.map(convert_to_int)
    df = df.drop(columns=['Y/Y %', 'Q/Q %'])
    
    if df is not None:
        st.session_state.df = df
        st.session_state.tuples = []
        st.session_state.has_defaults = False
        st.session_state.warning_message = None
        st.session_state.insights = None

# slecting a file
def render_file_selector():
    """Render the file selection column"""
    # file selection
    excel_files = [f for f in os.listdir(EXCEL_DATA_PATH) if f.endswith('.xlsx')]
    file_list = [Path(f).stem for f in excel_files]
    
    # writing the file title
    st.markdown("<center><div style='background-color:skyblue;border-radius:5px; padding:1px'><p class='section-header'>Slide Selection</p></div></center>", unsafe_allow_html=True)
    st.selectbox(
        "Choose a file to analyze",
        options=file_list,
        key="selected_file",
    )
    if st.button("Load Data", use_container_width=True):
        handle_file_selection()

# helper function to format the values in the data
def format_values(x):
    return f"${x} M"

def render_dataframe_section():
    """Rendering the DataFrame and insights section"""
    if st.session_state.df is not None:
        st.markdown("<center><div style='background-color:skyblue;border-radius:5px; padding:1px'><p class='section-header'>Summary Table</p></div></center>", unsafe_allow_html=True)
        formated_df = st.session_state.df.style.format(format_values)

        st.dataframe(formated_df, use_container_width=True, height=400)

        # Full-width Generate Insights button
        if st.button("Generate Insights 🔍", use_container_width=True):
            if not st.session_state.tuples:
                st.warning("Please select at least one data sample!")
            else:
                table_name = st.session_state.file_config.get('table_name')
                top_contributors = get_top_attributes_by_difference(st.session_state.db,
                                                                    st.session_state.tuples, table_name)
                print(top_contributors)
                top_contributors_formatted = format_top_contributors(top_contributors)
                print(top_contributors_formatted)
                st.session_state.insights = get_commentary(top_contributors_formatted, st.session_state.selected_file)

        if st.session_state.insights:
            st.markdown("<center><h4><div style='background-color:skyblue;border-radius:10px; padding:10px'>Generated Insights 📝</div></h4></center>", unsafe_allow_html=True)
            
            st.text(st.session_state.insights)
            # st.markdown('</div>', unsafe_allow_html=True)
            
            selected_cells_modified = names_to_index(st.session_state.df, st.session_state.tuples)
            df_modified = st.session_state.df.reset_index()
            pptx_file = generate_ppt(df_modified, selected_cells_modified,
                                     st.session_state.insights, st.session_state.selected_file)
            
            st.download_button(
                label="📊 Download PPT Report",
                data=pptx_file,
                file_name=f"analysis_report_{st.session_state.selected_file}.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True
            )

def render_controls_section():
    """Rendering the controls and tuples section"""
    st.markdown("<center><div style='background-color:skyblue;border-radius:5px; padding:1px'><p class='section-header'>Reason Code Selection</p></div></center>", unsafe_allow_html=True)
    
    # auto select button
    if st.button("🤖 Auto Select", use_container_width=True):
        auto_select()
    
    # selection controls
    st.markdown("**Manual Selection (Optional)**")
    col_index, col_column = st.columns(2)
    
    with col_index:
        index_name = st.selectbox(
            "Select Reason Code",
            options=st.session_state.df.index,
            key="index_select"
        )
    
    with col_column:
        column_name = st.selectbox(
            "Select Column",
            options=["Y/Y $", "Q/Q $"], # only two fields to choose from (maybe change later)
            key="column_select"
        )
    
    # displaying selected value
    if index_name and column_name:
        selected_value = st.session_state.df.loc[index_name, column_name]
        st.info(f"Selected Value: ${selected_value} M")
    
    if st.button("➕ Add Selection", use_container_width=True):
        add_tuple(index_name, column_name)
    
    # warning message
    if st.session_state.warning_message:
        st.warning(st.session_state.warning_message)
    
    # resetting and clearing buttons
    col_reset, col_clear = st.columns(2)
    
    with col_reset:
        if st.button("🔄 Reset", use_container_width=True):
            if st.session_state.has_defaults:
                st.session_state.tuples = st.session_state.default_tuples.copy()
            else:
                st.info("No default selections available")
    
    with col_clear:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.tuples = []
    
    # displaying current tuples
    st.markdown('<p class="section-header">Current Selections</p>', unsafe_allow_html=True)
    for i, tup in enumerate(st.session_state.tuples):
        with st.container():
            col_tuple, col_delete = st.columns([4, 1])
            with col_tuple:
                st.code(format_tuple(tup), language="python")
            with col_delete:
                if st.button("🗑️", key=f"delete_{i}"):
                    st.session_state.tuples.pop(i)
                    st.session_state.insights = None
                    st.rerun()

def main():
    st.set_page_config(page_title="LLM Commentary Generation", layout="wide")
    load_custom_css()
    initialize_session_state()
    
    st.markdown('<center><h1 class="main-header">LLM Commentary Generation 📝</h1></center>', unsafe_allow_html=True)
    
    st.session_state.engine, st.session_state.db = load_engine(config)
    
    # creating three columns with specific ratios
    col_files, col_data, col_controls = st.columns([1, 5, 2])
    
    with col_files:
        render_file_selector()
    
    with col_data:
        render_dataframe_section()
    
    with col_controls:
        if st.session_state.file_selected and st.session_state.df is not None:
            render_controls_section()

if __name__ == "__main__":
    main() 