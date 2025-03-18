import os
from pathlib import Path
import streamlit as st
import pandas as pd

# Import your existing functions
from utils.helper import read_config, get_file_config_by_path, convert_to_int, format_top_contributors, names_to_index
from utils.ppt_export import generate_ppt
from database.get_summary_table import *
from database.database_process import create_oracle_engine
from database.get_top_contributors import get_top_attributes_by_difference
from llm.reson_code import get_reason_code
from llm.commentary import get_commentary
from langchain_community.utilities import SQLDatabase

# Configuration
EXCEL_DATA_PATH = "data"
config_file = "config/config.yaml"
config = read_config(config_file)

# Cache resources
@st.cache_resource
def load_engine(config):
    db_config = config.get('database', {})
    engine = create_oracle_engine(db_config)
    db = SQLDatabase(engine)
    return engine, db

# Load custom CSS from external file
def load_custom_css():
    with open("styles/custom.css", "r") as f:
        st.markdown(f.read(), unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    if 'file_selected' not in st.session_state:
        st.session_state.file_selected = False
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'tuples' not in st.session_state:
        st.session_state.tuples = []
    if 'warning_message' not in st.session_state:
        st.session_state.warning_message = None
    if 'insights' not in st.session_state:
        st.session_state.insights = None
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []

# Format display functions
def format_tuple(tup):
    return f"({tup[0]}, {tup[1]}, {tup[2]})"

def format_values(x):
    return f"${x} M"

# App layout
def main():
    st.set_page_config(
        page_title="LLM Commentary Generation", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    load_custom_css()
    initialize_session_state()
    
    # Load DB engine
    st.session_state.engine, st.session_state.db = load_engine(config)
    
    # App Header
    st.markdown('<h2 style="text-align: center; color: #0083B8;">LLM Commentary Generation</h2>', unsafe_allow_html=True)
    
    # Move file selection to sidebar
    with st.sidebar:
        st.markdown('<div class="section-title">Slide Selection</div>', unsafe_allow_html=True)
        excel_files = [f for f in os.listdir(EXCEL_DATA_PATH) if f.endswith('.xlsx')]
        file_list = [Path(f).stem for f in excel_files]
        
        # File selection in a single horizontal line
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_file = st.selectbox(
                "", 
                options=file_list,
                key="selected_file",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("Load", use_container_width=True):
                # Handle file selection
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
                    # Automatically select tuples using get_reason_code
                    st.session_state.tuples = get_reason_code(df, st.session_state.selected_file)
                    st.session_state.warning_message = None
                    st.session_state.insights = None
                st.rerun()
    
    # Main content
    main_container = st.container()
    
    with main_container:
        if st.session_state.file_selected and st.session_state.df is not None:
            # Summary Table
            st.markdown('<div class="section-title">Summary Table</div>', unsafe_allow_html=True)
            with st.container():
                formatted_df = st.session_state.df.style.format(format_values)
                st.dataframe(formatted_df, use_container_width=True, height=300)
            
            # Two blocks under the summary table
            left_col, right_col = st.columns(2)
            
            # Left block - Selection controls
            with left_col:
                st.markdown('<div class="section-title">Selection Controls</div>', unsafe_allow_html=True)
                
                # Use a form to prevent rerunning on every change
                with st.form(key="manual_selection_form"):
                    # Row 1 - Reason code and column selection
                    st.markdown('<div class="sub-section">Reason Code and Column Selection</div>', unsafe_allow_html=True)
                    sel_col1, sel_col2 = st.columns(2)
                    with sel_col1:
                        index_name = st.selectbox(
                            "Select Reason Code",
                            options=st.session_state.df.index,
                        )
                    
                    with sel_col2:
                        column_name = st.selectbox(
                            "Select Column",
                            options=["Y/Y $", "Q/Q $"],
                        )
                    
                    # Row 2 - Contributing columns and Top n (separated from the above)
                    st.markdown('<hr class="sep-line">', unsafe_allow_html=True)
                    st.markdown('<div class="sub-section">Analysis Parameters</div>', unsafe_allow_html=True)
                    cont_col1, cont_col2 = st.columns(2)
                    with cont_col1:
                        contributing_cols = st.multiselect(
                            "Contributing Columns",
                            options=["Customer", "Product", "Region", "Channel"],
                            default=["Customer", "Product"]
                        )
                    
                    with cont_col2:
                        top_n = st.selectbox(
                            "Top n",
                            options=list(range(1, 11)),
                            index=2
                        )
                    
                    # Form submission
                    submitted = st.form_submit_button("+ Add Selection", use_container_width=True)
                    if submitted:
                        if index_name and column_name:
                            value = st.session_state.df.loc[index_name, column_name]
                            new_tuple = (index_name, column_name, value)
                            if new_tuple not in st.session_state.tuples:
                                st.session_state.tuples.append(new_tuple)
                                st.session_state.insights = None
                
                # Reset and clear buttons
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("🔄 Reset", use_container_width=True):
                        st.session_state.tuples = get_reason_code(st.session_state.df, st.session_state.selected_file)
                        st.rerun()
                
                with btn_col2:
                    if st.button("🗑️ Clear All", use_container_width=True):
                        st.session_state.tuples = []
                        st.rerun()
            
            # Right block - Current Selections
            with right_col:
                st.markdown('<div class="section-title">Current Selections</div>', unsafe_allow_html=True)
                selection_container = st.container()
                
                # Display current selections
                with selection_container:
                    if not st.session_state.tuples:
                        st.info("No selections yet. Use the controls on the left to add selections.")
                    else:
                        for i, tup in enumerate(st.session_state.tuples):
                            cols = st.columns([10, 1])
                            with cols[0]:
                                st.code(format_tuple(tup), language=None)
                            with cols[1]:
                                if st.button("🗑️", key=f"delete_{i}"):
                                    st.session_state.tuples.pop(i)
                                    st.session_state.insights = None
                                    st.rerun()
            
            # Commentary section
            st.markdown('<div class="section-title">Generated Commentary</div>', unsafe_allow_html=True)
            with st.container():
                if not st.session_state.insights and st.session_state.tuples:
                    if st.button("Generate Commentary", use_container_width=True):
                        table_name = st.session_state.file_config.get('table_name')
                        top_contributors = get_top_attributes_by_difference(
                            st.session_state.db,
                            st.session_state.tuples, 
                            table_name
                        )
                        top_contributors_formatted = format_top_contributors(top_contributors)
                        st.session_state.insights = get_commentary(
                            top_contributors_formatted, 
                            st.session_state.selected_file
                        )
                        st.rerun()
                
                # Display generated commentary if available
                if st.session_state.insights:
                    commentary_tabs = st.tabs(["Y/Y Commentary", "Q/Q Commentary"])
                    
                    with commentary_tabs[0]:
                        st.markdown('<div class="commentary-content">', unsafe_allow_html=True)
                        st.text("Y/Y Commentary:")
                        st.text("RMA ($ -44 million): The overall decline of $44 million is mainly due to World Wide Technology Holding Company Inc's negative contribution of $50 million, partially offset by BT Group PLC's positive contribution of $3 million, while Red River Computer Company Inc also contributed negatively with $3 million.")
                        st.text("...")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with commentary_tabs[1]:
                        st.markdown('<div class="commentary-content">', unsafe_allow_html=True)
                        st.text("Q/Q Commentary:")
                        st.text("RMA ($ -42 million): The overall decline of $42 million is mainly due to World Wide Technology Holding Company Inc's negative contribution of $48 million, partially offset by Cisco Systems Inc's positive contribution of $5 million, while Red River Computer Company Inc also contributed negatively with $3 million.")
                        st.text("...")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Commentary modification
                    if st.button("Modify Commentary", use_container_width=True):
                        st.session_state.show_chat = True
                    
                    # Chat input for modifying commentary
                    if st.session_state.get('show_chat', False):
                        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
                        # Display chat history
                        for role, message in st.session_state.chat_messages:
                            message_class = "user-message" if role == "user" else "bot-message"
                            st.markdown(f'<div class="chat-message {message_class}">{message}</div>', unsafe_allow_html=True)
                        
                        # Chat input
                        chat_input = st.text_input("Enter your comments here...", key="commentary_chat")
                        if chat_input:
                            # Process user input
                            st.session_state.chat_messages.append(("user", chat_input))
                            # Add bot response (would be replaced with LLM response)
                            st.session_state.chat_messages.append(("bot", "I'll update the commentary based on your feedback."))
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()