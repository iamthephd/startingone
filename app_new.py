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

# Custom CSS
def load_custom_css():
    st.markdown("""
    <style>
    .main {padding: 0rem 1rem;}
    .st-emotion-cache-1y4p8pa {padding-top: 0rem;}
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    .section-title {
        background-color: #0083B8;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }
    .stButton button {border-radius: 5px;}
    .row-container {margin-bottom: 10px;}
    .dataframe-container {
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 5px;
        background-color: #f9f9f9;
    }
    .selection-box {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        background-color: #f9f9f9;
    }
    .commentary-box {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        background-color: #f5f5f5;
        min-height: 200px;
    }
    .chat-box {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        background-color: white;
    }
    .chat-message {
        padding: 8px;
        border-radius: 5px;
        margin-bottom: 5px;
    }
    .user-message {
        background-color: #DCF8C6;
        margin-left: 20%;
    }
    .bot-message {
        background-color: #ECECEC;
        margin-right: 20%;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
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
        initial_sidebar_state="collapsed"
    )
    
    load_custom_css()
    initialize_session_state()
    
    # Load DB engine
    st.session_state.engine, st.session_state.db = load_engine(config)
    
    # App Header
    st.markdown('<h2 style="text-align: center; color: #0083B8;">LLM Commentary Generation</h2>', unsafe_allow_html=True)
    
    # Main container
    with st.container():
        # Top row - File selection
        col1, col2 = st.columns([2, 10])
        
        with col1:
            st.markdown('<div class="section-title">Slide Selection</div>', unsafe_allow_html=True)
            excel_files = [f for f in os.listdir(EXCEL_DATA_PATH) if f.endswith('.xlsx')]
            file_list = [Path(f).stem for f in excel_files]
            
            selected_file = st.selectbox(
                "", 
                options=file_list,
                key="selected_file",
                label_visibility="collapsed"
            )
            
            if st.button("Ok", use_container_width=True):
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
                    st.session_state.tuples = []
                    st.session_state.has_defaults = False
                    st.session_state.warning_message = None
                    st.session_state.insights = None
                st.rerun()
        
        # Main content area - split into 3 columns
        if st.session_state.file_selected and st.session_state.df is not None:
            # Middle content - 3 columns layout
            left_col, middle_col, right_col = st.columns([5, 5, 3])
            
            # Left column - Summary Table and Manual Selections
            with left_col:
                # Summary Table
                st.markdown('<div class="section-title">Summary Table</div>', unsafe_allow_html=True)
                with st.container():
                    formatted_df = st.session_state.df.style.format(format_values)
                    st.dataframe(formatted_df, use_container_width=True, height=300)
                
                # Manual Selection controls
                with st.container():
                    # Use a form to prevent rerunning on every change
                    with st.form(key="manual_selection_form"):
                        st.markdown('<div class="section-title">Manual Selection (Optional)</div>', unsafe_allow_html=True)
                        
                        # Row 1 - Reason code and column selection
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
                        
                        # Row 2 - Contributing columns and Top n
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
                            if st.session_state.has_defaults:
                                st.session_state.tuples = st.session_state.default_tuples.copy()
                                st.rerun()
                    
                    with btn_col2:
                        if st.button("🗑️ Clear All", use_container_width=True):
                            st.session_state.tuples = []
                            st.rerun()
            
            # Middle column - Current Selections and Commentary
            with middle_col:
                # Current Selections
                st.markdown('<div class="section-title">Current Selections</div>', unsafe_allow_html=True)
                selection_container = st.container()
                
                # Auto select button
                if st.button("🤖 Auto Select", use_container_width=True):
                    # Get LLM-selected reason codes
                    default_tuples = get_reason_code(st.session_state.df, st.session_state.selected_file)
                    st.session_state.default_tuples = default_tuples
                    st.session_state.has_defaults = True
                    for tup in default_tuples:
                        if tup not in st.session_state.tuples:
                            st.session_state.tuples.append(tup)
                    st.rerun()
                
                # Display current selections
                with selection_container:
                    for i, tup in enumerate(st.session_state.tuples):
                        cols = st.columns([10, 1])
                        with cols[0]:
                            st.code(format_tuple(tup), language=None)
                        with cols[1]:
                            if st.button("🗑️", key=f"delete_{i}"):
                                st.session_state.tuples.pop(i)
                                st.session_state.insights = None
                                st.rerun()
                
                # Generated Commentary
                st.markdown('<div class="section-title">Generated Commentary</div>', unsafe_allow_html=True)
                with st.container():
                    commentary_container = st.container()
                    
                    # Generate commentary button
                    if st.button("Modify commentary...", use_container_width=True):
                        if st.session_state.tuples:
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
                    
                    # Display commentary if available
                    with commentary_container:
                        if st.session_state.insights:
                            commentary_tabs = st.tabs(["Y/Y Commentary", "Q/Q Commentary"])
                            
                            with commentary_tabs[0]:
                                st.text("Y/Y Commentary:")
                                st.text("RMA ($ -44 million): The overall decline of $44 million is mainly due to World Wide Technology Holding Company Inc's negative contribution of $50 million, partially offset by BT Group PLC's positive contribution of $3 million, while Red River Computer Company Inc also contributed negatively with $3 million.")
                                st.text("...")
                            
                            with commentary_tabs[1]:
                                st.text("Q/Q Commentary:")
                                st.text("RMA ($ -42 million): The overall decline of $42 million is mainly due to World Wide Technology Holding Company Inc's negative contribution of $48 million, partially offset by Cisco Systems Inc's positive contribution of $5 million, while Red River Computer Company Inc also contributed negatively with $3 million.")
                                st.text("...")
                    
                    # Chat input for modifying commentary
                    with st.container():
                        chat_input = st.text_input("Enter your comments here...", key="commentary_chat")
                        if chat_input:
                            # Process user input (placeholder for now)
                            st.session_state.chat_messages.append(("user", chat_input))
                            # Add bot response (would be replaced with LLM response)
                            st.session_state.chat_messages.append(("bot", "I'll update the commentary based on your feedback."))
                            st.rerun()
            
            # Right column - ChatBot
            with right_col:
                st.markdown('<div class="section-title">ChatBot 🤖</div>', unsafe_allow_html=True)
                
                # ChatBot container
                chat_container = st.container()
                with chat_container:
                    # Sample chat messages
                    with st.container():
                        st.markdown('<div class="chat-message bot-message">Find the total amount for each quarter</div>', unsafe_allow_html=True)
                        
                        # Bot response with data
                        st.markdown("""
                        <div class="chat-message bot-message">
                        The total amount for each date is as follows:
                        <br>•2024Q1: -$267,251,091.67
                        <br>•2024Q2: -$291,666,372.66
                        <br>•2024Q3: -$283,156,445.66
                        <br>•2024Q4: -$286,165,111.58
                        <br>•2025Q1: -$352,851,284.65
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Display chat history
                    for role, message in st.session_state.chat_messages:
                        message_class = "user-message" if role == "user" else "bot-message"
                        st.markdown(f'<div class="chat-message {message_class}">{message}</div>', unsafe_allow_html=True)
                
                # Chatbot input
                chat_user_input = st.text_input("Typing...", key="chatbot_input")
                if chat_user_input:
                    # Process user chat (placeholder)
                    st.session_state.chat_messages.append(("user", chat_user_input))
                    # Add bot response (would be replaced with actual chatbot response)
                    st.session_state.chat_messages.append(("bot", "I'm analyzing your request..."))
                    st.rerun()

if __name__ == "__main__":
    main()