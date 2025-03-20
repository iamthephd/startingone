import os
from pathlib import Path
import streamlit as st
import yaml

from utils.helper import read_config, get_file_config_by_path, convert_to_int, format_top_contributors, names_to_index
from utils.ppt_export import generate_ppt
from database.get_summary_table import *
from database.database_process import create_oracle_engine
from database.get_top_contributors import get_top_attributes_by_difference
from llm.reson_code import get_reason_code
from llm.commentary import get_commentary, modify_commentary
from llm.chatbot import process_chatbot_query


# page Configuration
st.set_page_config(layout="wide")

# loading the style
def load_custom_css():
    """Load custom CSS styles"""
    with open("styles/style_new.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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
    return engine

# initialize Session State
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
    if file_name not in st.session_state.file_data:
        st.session_state.file_config = get_file_config_by_path(config, file_name)
        st.session_state.file_name = file_name
        # summary table (one time)
        summary_func_name = st.session_state.file_config.get('summary_table_function')
        summary_func = globals()[summary_func_name]
        df = summary_func(st.session_state.engine)
        df = df.map(convert_to_int)
        df = df.drop(columns=['Y/Y %', 'Q/Q %'])
        
        st.session_state.contributing_columns = st.session_state.file_config['contributing_columns']
        st.session_state.top_n = st.session_state.file_config['top_n']
        
        # reason code (one time)
        initial_selected_cells = get_reason_code(df, file_name)
        
        # getting the contributing factors
        top_contributors = get_top_attributes_by_difference(st.session_state.engine,
                                                         initial_selected_cells,
                                                         st.session_state.file_config['table_name'],
                                                         st.session_state.contributing_columns,
                                                         st.session_state.top_n)
        top_contributors_formatted = format_top_contributors(top_contributors)
        
        commentary = get_commentary(top_contributors_formatted, file_name)
        
        st.session_state.file_data[file_name] = {
            'name': file_name,
            'df': df,
            'selected_cells': initial_selected_cells.copy(),
            'initial_selected_cells': initial_selected_cells, # Store initial selection
            'commentary': commentary
        }
    return st.session_state.file_data[file_name]

def modify_config():
    """Updates the config file"""
    with open(config_file, "w") as file:
        config['excel_files'][st.session_state.file_name]['contributing_columns'] = list(st.session_state.contributing_columns)
        config['excel_files'][st.session_state.file_name]['top_n'] = st.session_state.top_n
        yaml.dump(config, file)

def render_selection_controls(edited_df, file_data):
    """Render the selection controls section"""
    st.text("")
    st.markdown("<h5 style='text-align: center;'>Selection Controls</h5>", unsafe_allow_html=True)
    row_index = st.selectbox("Select Row", edited_df.index.tolist())
    column = st.selectbox("Select Column", ["Y/Y %", "Q/Q %"])
    
    if st.button("+ Add Selection"):
        if row_index is not None and column is not None:
            value = edited_df.loc[row_index, column]
            new_selection = (row_index, column, value)
            if new_selection in file_data['selected_cells']:
                st.warning(f"Cell ({row_index}, {column}, {value}) is already selected!")
            else:
                file_data['selected_cells'].append(new_selection)
                st.rerun()
    
    with st.expander("Additional Settings", expanded=False):
        contributing_cols = st.multiselect(
            "Contributing Columns",
            st.session_state.contributing_columns,
            default=st.session_state.contributing_columns
        )
        
        top_n = st.selectbox(
            "Top N",
            range(1, 11),
            index=st.session_state.top_n - 1
        )
        
    if st.button("Apply Changes", use_container_width=True):
        if contributing_cols != st.session_state.contributing_columns or top_n != st.session_state.top_n:
            st.session_state.contributing_columns = contributing_cols
            st.session_state.top_n = top_n
            # modify the config
            modify_config()

def render_selected_cells(file_data):
    """Render the selected cells section with multiselect interface"""
    st.text("")
    st.markdown("<h5 style='text-align: center;'>Selected Cells</h5>", unsafe_allow_html=True)
    container = st.container(height=200)
    
    with container:
        if not file_data['selected_cells']:
            st.info("No cells selected")
        else:
            # Create display strings for the cells
            cell_display = [f"{row}, {col}, {val}" 
                          for row, col, val in file_data['selected_cells']]
            
            # Create indices for multiselect
            selected_indices = st.multiselect(
                "Selected cells",
                options=range(len(cell_display)),
                default=range(len(cell_display)),
                format_func=lambda i: cell_display[i],
                label_visibility="visible"
            )
            
            # Update selected cells if selections change
            if len(selected_indices) != len(file_data['selected_cells']):
                file_data['selected_cells'] = [file_data['selected_cells'][i] for i in selected_indices]
                st.rerun()
    
    # reset button
    st.button("Reset", key="reset", on_click=lambda: reset_selections(file_data), use_container_width=True)

def render_chatbot():
    """Render the chatbot section"""
    st.markdown("<center><div style='background-color:lightgreen;border-radius:5px; padding:1px'><p class='section-header'>ChatBot 🤖</p></div></center>", unsafe_allow_html=True)
    main_container = st.container(border=True)
    
    with main_container:
        message_container = st.container(height=400)
        with message_container:
            if not st.session_state.chatbot_messages:
                st.info("Type a message to start chatting")
            else:
                for message in st.session_state.chatbot_messages:
                    is_user = message.startswith("You: ")
                    message_content = message[4:] if is_user else message[5:]
                    align = "flex-end" if is_user else "flex-start"
                    bg_color = "#DCF8C6" if is_user else "white"
                    
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: {align}; margin-bottom: 10px;">
                            <div style="background-color: {bg_color}; border-radius: 10px; padding: 8px 12px; max-width: 80%; box-shadow: 0 1px 1px rgba(0,0,0,0.1);">
                                {message_content}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        
        chatbot_input = st.text_input(
            "Message",
            placeholder="Type a message...",
            label_visibility="collapsed",
            key="chatbot_input"
        )
        
        if st.button("Send", use_container_width=True) and chatbot_input:
            st.session_state.chatbot_messages.append(f"You: {chatbot_input}")
            response = process_chatbot_query(st.session_state.engine, chatbot_input)
            st.session_state.chatbot_messages.append(f"Bot: {response}")
            st.rerun()

def clear_selections(file_data):
    """Clear all selected cells"""
    file_data['selected_cells'] = []
    st.rerun()

def reset_selections(file_data):
    """Reset to initial selected cells"""
    file_data['selected_cells'] = file_data['initial_selected_cells'].copy()
    st.rerun()

def update_commentary(file_data):
    """Update commentary based on current selections"""
    
    # getting the contributing factors
    top_contributors = get_top_attributes_by_difference(st.session_state.engine,
                                                     file_data['selected_cells'],
                                                     st.session_state.file_config['table_name'],
                                                     st.session_state.contributing_columns,
                                                     st.session_state.top_n)
    
    top_contributors_formatted = format_top_contributors(top_contributors)
    # getting the commentary
    file_data['commentary'] = get_commentary(top_contributors_formatted, st.session_state.file_name)

# Main Application
def main():
    load_custom_css()
    
    st.markdown("<center><h1 class='main-header'>Close Pack Commentary 📝</h1></center>", unsafe_allow_html=True)
    
    # setting the engine
    st.session_state.engine = load_engine(config)
    
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        excel_files = [f for f in os.listdir(EXCEL_DATA_PATH) if f.endswith('.xlsx')]
        file_list = [Path(f).stem for f in excel_files]
        selected_file = st.selectbox("Select Slide", file_list)
        if st.button("Ok"):
            st.session_state.selected_file = selected_file
            initialize_file_data(selected_file)
    
    # Main Content
    if st.session_state.selected_file:
        file_data = st.session_state.file_data[st.session_state.selected_file]
        col_a, col_b, col_c = st.columns([3, 2, 1])
        
        # Column A - Data Overview and Cell Selection
        with col_a:
            # Data Overview
            st.markdown("<center><div style='background-color:skyblue;border-radius:5px; padding:1px'><p class='section-header'>Summary Table 📊</p></div></center>", unsafe_allow_html=True)
            edited_df = st.data_editor(file_data['df'], key=f"data_editor_{st.session_state.selected_file}", hide_index=False)
            
            # Cell Selection
            st.markdown("<center><div style='background-color:skyblue;border-radius:5px; padding:1px'><p class='section-header'>Manual Selection 👇</p></div></center>", unsafe_allow_html=True)
            
            left_col, right_col = st.columns(2)
            with left_col:
                render_selection_controls(edited_df, file_data)
            with right_col:
                render_selected_cells(file_data)
            
            if st.button("Modify Commentary", use_container_width=True):
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
            
            user_comment = st.text_input("Type to modify analysis", key=f"user_comment_input_{st.session_state.selected_file}")
            if st.button("Update Commentary", key=f"update_commentary_btn_{st.session_state.selected_file}"):
                if user_comment:
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
        
        # Column C - Chatbot
        with col_c:
            with st.expander("ChatBot", expanded=False):
                render_chatbot()
    else:
        st.info("Please select a file from the sidebar and click 'Ok' to begin analysis.")

if __name__ == "__main__":
    main()