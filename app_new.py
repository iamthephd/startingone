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
    if 'processing_query' not in st.session_state:
        st.session_state.processing_query = False
    # Add chatbot_open state to track if chatbot is opened
    if 'chatbot_open' not in st.session_state:
        st.session_state.chatbot_open = False

def initialize_file_data(file_name):
    """Initialize data for a file if it doesn't exist"""
    if file_name not in st.session_state.file_data:
        with st.spinner("Loading file data..."):
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
    with st.spinner("Updating configuration..."):
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
                with st.spinner("Adding selection..."):
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
                with st.spinner("Updating selections..."):
                    file_data['selected_cells'] = [file_data['selected_cells'][i] for i in selected_indices]
                    st.rerun()
    
    # reset button
    st.button("Reset", key="reset", on_click=lambda: reset_selections(file_data), use_container_width=True)

def toggle_chatbot():
    """Toggle the chatbot open/closed state"""
    st.session_state.chatbot_open = not st.session_state.chatbot_open

def process_chat_input():
    """Process the chat input and update chat history"""
    if st.session_state.chatbot_input and not st.session_state.processing_query:
        query = st.session_state.chatbot_input
        st.session_state.chatbot_input = ""  # Clear the input
        st.session_state.processing_query = True
        st.session_state.chatbot_messages.append(f"You: {query}")
        
        # Keep chatbot open
        st.session_state.chatbot_open = True
        
        # Rerun to show the user message first
        st.rerun()

def render_chatbot():
    """Render the chatbot in a container that maintains state"""
    # Create a button to toggle chatbot visibility
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button("💬 Chat Assistant", use_container_width=True, on_click=toggle_chatbot):
            pass

    # Show chatbot if it's open
    if st.session_state.chatbot_open:
        with st.container(border=True):
            st.markdown("### Chat Assistant")
            
            message_container = st.container(height=400)
            
            with message_container:
                if not st.session_state.chatbot_messages:
                    st.info("Type a message to start chatting")
                else:
                    for message in st.session_state.chatbot_messages:
                        is_user = message.startswith("You: ")
                        message_content = message[4:] if is_user else message[5:]
                        
                        st.markdown(
                            f"""
                            <div class="chat-message {'chat-message-user' if is_user else 'chat-message-bot'}">
                                <div class="chat-bubble {'chat-bubble-user' if is_user else 'chat-bubble-bot'}">
                                    {message_content}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            
            # Process the current query if needed
            if st.session_state.processing_query:
                with st.spinner("Getting response..."):
                    # Get the last user query
                    last_user_message = next((msg for msg in reversed(st.session_state.chatbot_messages) 
                                              if msg.startswith("You: ")), None)
                    if last_user_message:
                        query = last_user_message[4:]
                        # Implement a simple response for testing
                        try:
                            response = process_chatbot_query(st.session_state.engine, query, st.session_state.config['table_name'])
                        except Exception as e:
                            # Fallback for testing
                            response = f"I received your message: '{query}'. How can I help you further?"
                        
                        st.session_state.chatbot_messages.append(f"Bot: {response}")
                    
                    st.session_state.processing_query = False
                    
                    # Keep chatbot open after processing
                    st.session_state.chatbot_open = True
                    st.rerun()
            
            # Chat input with on_change to handle Enter key press
            st.text_input(
                "Message",
                placeholder="Type a message and press Enter...",
                label_visibility="collapsed",
                key="chatbot_input",
                on_change=process_chat_input
            )
            
            if st.button("Close Chat", use_container_width=True):
                st.session_state.chatbot_open = False
                st.rerun()

def clear_selections(file_data):
    """Clear all selected cells"""
    with st.spinner("Clearing selections..."):
        file_data['selected_cells'] = []
        st.rerun()

def reset_selections(file_data):
    """Reset to initial selected cells"""
    with st.spinner("Resetting selections..."):
        file_data['selected_cells'] = file_data['initial_selected_cells'].copy()
        st.rerun()

def update_commentary(file_data):
    """Update commentary based on current selections"""
    with st.spinner("Updating commentary..."):
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
    with st.spinner("Loading engine..."):
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
        col_a, col_b = st.columns([3, 2])  # Changed to two columns
        
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
                
            # add a button to update commentary
            st.button("Generate Commentary", key="update_commentary", on_click=lambda: update_commentary(file_data), use_container_width=True)
        
        # Column B - Commentary and actions
        with col_b:
            # Commentary Section
            st.markdown("<center><div style='background-color:skyblue;border-radius:5px; padding:1px'><p class='section-header'>Commentary 📝</p></div></center>", unsafe_allow_html=True)
            
            # Text Area for Commentary
            st.text_area("", value=file_data.get('commentary', ''), height=300, key=f"commentary_{st.session_state.selected_file}")
            
            st.markdown("<center><div style='background-color:skyblue;border-radius:5px; padding:1px'><p class='section-header'>Actions 🧰</p></div></center>", unsafe_allow_html=True)
            
            # Actions
            st.button("Export to PowerPoint", key="export_ppt", on_click=lambda: generate_ppt(file_data, st.session_state.file_config), use_container_width=True)
            
        # Render chatbot at the bottom outside the columns
        st.markdown("---")
        render_chatbot()

if __name__ == "__main__":
    main()
