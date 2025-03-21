import streamlit as st
from utils.api_client import APIClient
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(layout="wide")

# Initialize API client
api_client = APIClient('http://localhost:5000/api')

def load_custom_css():
    with open("styles/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def init_session_state():
    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None
    if 'file_data' not in st.session_state:
        st.session_state.file_data = {}
    if 'chatbot_messages' not in st.session_state:
        st.session_state.chatbot_messages = []

def initialize_file_data(file_name):
    if file_name not in st.session_state.file_data:
        with st.spinner('Loading data...'):
            try:
                # Get summary table
                response = api_client.get_summary_table(file_name)
                if response.get('error'):
                    st.error(f"Error loading data: {response['error']}")
                    return

                st.session_state.file_data[file_name] = {
                    'name': file_name,
                    'df': response['data'],
                    'selected_cells': [],
                    'commentary': ""
                }
            except Exception as e:
                st.error(f"Failed to initialize data: {str(e)}")

def render_selection_controls(file_data):
    st.markdown("<h5>Selection Controls</h5>", unsafe_allow_html=True)

    row_index = st.selectbox("Select Row", range(len(file_data['df'])))
    column = st.selectbox("Select Column", ["Y/Y %", "Q/Q %"])

    if st.button("+ Add Selection"):
        value = file_data['df'][row_index][column]
        new_selection = (row_index, column, value)
        if new_selection not in file_data['selected_cells']:
            file_data['selected_cells'].append(new_selection)
            st.rerun()

def update_commentary(file_data):
    with st.spinner('Generating commentary...'):
        try:
            response = api_client.generate_commentary(
                file_data['selected_cells'],
                file_data['name']
            )
            if response.get('error'):
                st.error(f"Error generating commentary: {response['error']}")
                return
            file_data['commentary'] = response['commentary']
        except Exception as e:
            st.error(f"Failed to update commentary: {str(e)}")

def download_ppt(file_data):
    with st.spinner('Generating PPT...'):
        try:
            ppt_file = api_client.generate_ppt(
                file_data['commentary'],
                file_data['selected_cells'],
                file_data['name']
            )
            return ppt_file
        except Exception as e:
            st.error(f"Failed to generate PPT: {str(e)}")
            return None

def render_chatbot():
    st.markdown("### Chatbot 🤖")

    # Display chat messages
    for message in st.session_state.chatbot_messages:
        is_user = message.startswith("You: ")
        with st.chat_message("user" if is_user else "assistant"):
            st.write(message[4:] if is_user else message[5:])

    # Chat input
    if prompt := st.chat_input("Message"):
        st.session_state.chatbot_messages.append(f"You: {prompt}")

        with st.spinner('Processing...'):
            try:
                response = api_client.process_chat(prompt)
                if response.get('error'):
                    st.error(f"Error: {response['error']}")
                else:
                    st.session_state.chatbot_messages.append(f"Bot: {response['response']}")
            except Exception as e:
                st.error(f"Failed to process chat: {str(e)}")
        st.rerun()

def main():
    load_custom_css()
    init_session_state()

    st.markdown("<h1 class='main-header'>Close Pack Commentary 📝</h1>", unsafe_allow_html=True)

    # Sidebar - File Selection and Chatbot
    with st.sidebar:
        st.markdown("### File Selection")
        selected_file = st.selectbox("Select Slide", ["file1.xlsx", "file2.xlsx"])
        if st.button("Load File"):
            st.session_state.selected_file = selected_file
            initialize_file_data(selected_file)

        st.markdown("<hr>", unsafe_allow_html=True)
        render_chatbot()

    # Main Content
    if st.session_state.selected_file:
        file_data = st.session_state.file_data[st.session_state.selected_file]

        # Two-column layout
        col_a, col_b = st.columns([3, 2])

        # Column A - Data and Selection
        with col_a:
            st.markdown("### Summary Table 📊")
            st.dataframe(file_data['df'])

            st.markdown("### Manual Selection 👇")
            render_selection_controls(file_data)

        # Column B - Commentary and PPT
        with col_b:
            st.markdown("### Commentary 📝")

            if file_data['commentary']:
                st.text_area(
                    "Current Commentary",
                    value=file_data['commentary'],
                    height=400,
                    key="commentary_display"
                )

            # Commentary and PPT buttons in the same row
            col_comment, col_ppt = st.columns([3, 1])
            with col_comment:
                if st.button("Update Commentary", use_container_width=True):
                    update_commentary(file_data)
                    st.rerun()
            with col_ppt:
                ppt_file = download_ppt(file_data)
                if ppt_file:
                    st.download_button(
                        "📥 PPT",
                        ppt_file,
                        file_name=f"{file_data['name']}_presentation.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True
                    )
    else:
        st.info("Please select a file from the sidebar to begin analysis.")

if __name__ == "__main__":
    main()