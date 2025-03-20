import os
from pathlib import Path
import streamlit as st
import yaml
import traceback

from utils.helper import read_config, get_file_config_by_path, convert_to_int, format_top_contributors, names_to_index
from utils.ppt_export import generate_ppt
from database.get_summary_table import *
from database.database_process import create_oracle_engine
from database.get_top_contributors import get_top_attributes_by_difference
from llm.reson_code import get_reason_code
from llm.commentary import get_commentary, modify_commentary
from llm.chatbot import process_chatbot_query

# Page Configuration
st.set_page_config(layout="wide")

# Loading the style
def load_custom_css():
    """Load custom CSS styles"""
    with open("styles/style_new.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Setting up the DB engine
EXCEL_DATA_PATH = "data"
config_file = "config/config.yaml"
excel_data_dir = "data"

try:
    config = read_config(config_file)
except Exception as e:
    st.error(f"Failed to load configuration: {str(e)}")
    st.stop()

# Caching the resources
@st.cache_resource
def load_engine(config):
    try:
        db_config = config.get('database', {})
        engine = create_oracle_engine(db_config)
        return engine
    except Exception as e:
        st.error(f"Failed to connect to database: {str(e)}")
        return None

# Initialize Session State
def init_session_state():
    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None
    if 'file_data' not in st.session_state:
        st.session_state.file_data = {}
    if 'commentary' not in st.session_state:
        st.session_state.commentary = ""
    if 'chatbot_messages' not in st.session_state:
        st.session_state.chatbot_messages = []

def initialize_file_data(file_name):
    """Initialize data for a file if it doesn't exist"""
    try:
        if file_name not in st.session_state.file_data:
            with st.spinner('Loading file data...'):
                st.session_state.file_config = get_file_config_by_path(config, file_name)
                st.session_state.file_name = file_name
                
                # Summary table
                summary_func_name = st.session_state.file_config.get('summary_table_function')
                summary_func = globals()[summary_func_name]
                df = summary_func(st.session_state.engine)
                df = df.map(convert_to_int)
                df = df.drop(columns=['Y/Y %', 'Q/Q %'])
                
                st.session_state.contributing_columns = st.session_state.file_config['contributing_columns']
                st.session_state.top_n = st.session_state.file_config['top_n']
                
                # Reason code
                with st.spinner('Generating reason codes...'):
                    initial_selected_cells = get_reason_code(df, file_name)
                
                # Getting contributing factors
                with st.spinner('Calculating top contributors...'):
                    top_contributors = get_top_attributes_by_difference(
                        st.session_state.engine,
                        initial_selected_cells,
                        st.session_state.file_config['table_name'],
                        st.session_state.contributing_columns,
                        st.session_state.top_n
                    )
                    top_contributors_formatted = format_top_contributors(top_contributors)
                
                with st.spinner('Generating commentary...'):
                    commentary = get_commentary(top_contributors_formatted, file_name)
                
                st.session_state.file_data[file_name] = {
                    'name': file_name,
                    'df': df,
                    'selected_cells': initial_selected_cells.copy(),
                    'initial_selected_cells': initial_selected_cells,
                    'commentary': commentary
                }
        return st.session_state.file_data[file_name]
    except Exception as e:
        st.error(f"Error initializing file data: {str(e)}")
        return None

def modify_config():
    """Updates the config file"""
    try:
        with open(config_file, "w") as file:
            config['excel_files'][st.session_state.file_name]['contributing_columns'] = list(st.session_state.contributing_columns)
            config['excel_files'][st.session_state.file_name]['top_n'] = st.session_state.top_n
            yaml.dump(config, file)
    except Exception as e:
        st.error(f"Failed to update configuration: {str(e)}")

# Keep all other functions unchanged
[... Rest of the original functions remain exactly the same until main() ...]

def main():
    load_custom_css()
    
    st.markdown("<center><h1 class='main-header'>Close Pack Commentary 📝</h1></center>", unsafe_allow_html=True)
    
    # Setting the engine
    st.session_state.engine = load_engine(config)
    if not st.session_state.engine:
        st.error("Failed to initialize database connection")
        st.stop()
    
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        # Add logo
        st.image("assets/logo.svg", use_column_width=True)
        
        try:
            excel_files = [f for f in os.listdir(EXCEL_DATA_PATH) if f.endswith('.xlsx')]
            file_list = [Path(f).stem for f in excel_files]
            selected_file = st.selectbox("Select Slide", file_list)
            if st.button("Ok"):
                with st.spinner('Loading file...'):
                    st.session_state.selected_file = selected_file
                    initialize_file_data(selected_file)
        except Exception as e:
            st.error(f"Error loading files: {str(e)}")
    
    # Main Content
    if st.session_state.selected_file:
        try:
            file_data = st.session_state.file_data[st.session_state.selected_file]
            col_a, col_b, col_c = st.columns([3, 2, 1])
            
            # Column A - Data Overview and Cell Selection
            with col_a:
                st.markdown("<center><div style='background-color:skyblue;border-radius:5px; padding:1px'><p class='section-header'>Summary Table 📊</p></div></center>", unsafe_allow_html=True)
                edited_df = st.data_editor(file_data['df'], key=f"data_editor_{st.session_state.selected_file}", hide_index=False)
                
                st.markdown("<center><div style='background-color:skyblue;border-radius:5px; padding:1px'><p class='section-header'>Manual Selection 👇</p></div></center>", unsafe_allow_html=True)
                
                left_col, right_col = st.columns(2)
                with left_col:
                    render_selection_controls(edited_df, file_data)
                with right_col:
                    render_selected_cells(file_data)
                
                if st.button("Modify Commentary", use_container_width=True):
                    with st.spinner('Updating commentary...'):
                        update_commentary(file_data)
                        st.rerun()
            
            # Column B - Commentary
            with col_b:
                st.markdown("<center><div style='background-color:lightpink;border-radius:5px; padding:1px'><p class='section-header'>Commentary 📝</p></div></center>", unsafe_allow_html=True)
                
                if file_data['commentary']:
                    st.text_area(
                        "Commentary",
                        value=file_data['commentary'],
                        height=400,
                        key=f"commentary_display_{st.session_state.selected_file}",
                        label_visibility="collapsed"
                    )
                else:
                    st.info("Click 'Modify Commentary' to generate analysis")
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button("Update Commentary", key=f"update_commentary_btn_{st.session_state.selected_file}", use_container_width=True):
                        user_comment = st.session_state.get(f"user_comment_input_{st.session_state.selected_file}", "")
                        if user_comment:
                            with st.spinner('Updating commentary...'):
                                file_data['commentary'] = modify_commentary(
                                    user_comment,
                                    file_data['commentary'],
                                    file_data['selected_cells'],
                                    st.session_state.selected_file,
                                    st.session_state.contributing_columns,
                                    st.session_state.top_n
                                )
                                st.rerun()
                        else:
                            st.error("Please provide comments to update the commentary")
                
                with col2:
                    if st.button("Export PPT", use_container_width=True):
                        try:
                            with st.spinner('Generating PPT...'):
                                generate_ppt(file_data['commentary'], st.session_state.selected_file)
                            st.success("PPT generated successfully!")
                        except Exception as e:
                            st.error(f"Failed to generate PPT: {str(e)}")
                
                user_comment = st.text_input("Type to modify analysis", key=f"user_comment_input_{st.session_state.selected_file}")
            
            # Column C - Chatbot
            with col_c:
                with st.expander("ChatBot", expanded=False):
                    render_chatbot()
                    
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error(f"Stack trace: {traceback.format_exc()}")
    else:
        st.info("Please select a file from the sidebar and click 'Ok' to begin analysis.")

if __name__ == "__main__":
    main()