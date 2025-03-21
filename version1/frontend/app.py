import os
import sys
from pathlib import Path
import streamlit as st
import yaml
import sys
import requests

# Add parent directory to path to import api client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.client import APIClient

# page Configuration
st.set_page_config(layout="wide")

# Initialize API client
API_ENDPOINT = os.getenv("API_ENDPOINT", "http://localhost:5000")
api_client = APIClient(API_ENDPOINT)

# loading the style
def load_custom_css():
    """Load custom CSS styles"""
    with open("frontend/styles/style_new.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load data files
EXCEL_DATA_PATH = "frontend/data"
config_file = "config/config.yaml"

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

def initialize_file_data(file_name):
    """Initialize data for a file if it doesn't exist"""
    if file_name not in st.session_state.file_data:
        with st.spinner("Loading file data..."):
            # Get file config via API
            file_config = api_client.get_file_config(file_name)
            st.session_state.file_config = file_config
            st.session_state.file_name = file_name
            
            # Get summary table via API
            df = api_client.get_summary_table(file_name)
            
            st.session_state.contributing_columns = file_config['contributing_columns']
            st.session_state.top_n = file_config['top_n']
            
            # Get reason code via API
            initial_selected_cells = api_client.get_reason_code(file_name, df)
            
            # Get top contributors via API
            top_contributors_formatted = api_client.get_top_contributors(
                file_name, 
                initial_selected_cells,
                file_config['contributing_columns'],
                file_config['top_n']
            )
            
            # Get commentary via API
            commentary = api_client.get_commentary(file_name, top_contributors_formatted)
            
            st.session_state.file_data[file_name] = {
                'name': file_name,
                'df': df,
                'selected_cells': initial_selected_cells.copy(),
                'initial_selected_cells': initial_selected_cells, # Store initial selection
                'commentary': commentary
            }
    return st.session_state.file_data[file_name]

def modify_config():
    """Updates the config file via API"""
    with st.spinner("Updating configuration..."):
        api_client.update_config(
            st.session_state.file_name,
            list(st.session_state.contributing_columns),
            st.session_state.top_n
        )

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

def process_chat_input():
    """Process the chat input and update chat history"""
    if st.session_state.chatbot_input and not st.session_state.processing_query:
        query = st.session_state.chatbot_input
        st.session_state.chatbot_input = ""  # Clear the input
        st.session_state.processing_query = True
        st.session_state.chatbot_messages.append(f"You: {query}")
        
        # Rerun to show the user message first
        st.rerun()

def render_chatbot():
    """Render the chatbot in a popover"""
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
                response = api_client.process_chatbot_query(
                    query, 
                    st.session_state.file_config['table_name']
                )
                st.session_state.chatbot_messages.append(f"Bot: {response}")
            
            st.session_state.processing_query = False
            st.rerun()
    
    # Chat input with on_change to handle Enter key press
    st.text_input(
        "Message",
        placeholder="Type a message and press Enter...",
        label_visibility="collapsed",
        key="chatbot_input",
        on_change=process_chat_input
    )

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
        # Getting top contributors via API
        top_contributors_formatted = api_client.get_top_contributors(
            st.session_state.file_name,
            file_data['selected_cells'],
            st.session_state.contributing_columns,
            st.session_state.top_n
        )
        
        # Getting commentary via API
        file_data['commentary'] = api_client.get_commentary(
            st.session_state.file_name, 
            top_contributors_formatted
        )

# Main Application
def main():
    load_custom_css()
    
    st.markdown("<center><h1 class='main-header'>Close Pack Commentary 📝</h1></center>", unsafe_allow_html=True)
    
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        excel_files = api_client.get_available_files()
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
                    with st.spinner("Modifying commentary..."):
                        file_data['commentary'] = api_client.modify_commentary(
                            st.session_state.file_name,
                            user_comment,
                            file_data['commentary'],
                            file_data['selected_cells'],
                            st.session_state.contributing_columns,
                            st.session_state.top_n
                        )
                        st.rerun()
                else:
                    st.error("Please provide comments to update the commentary")
        
        # Chat Popover at bottom right
        with st.popover("Chat 🤖", use_container_width=False):
            render_chatbot()
    else:
        st.info("Please select a file from the sidebar and click 'Ok' to begin analysis.")

if __name__ == "__main__":
    main()