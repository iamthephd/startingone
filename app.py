import os
from pathlib import Path
import streamlit as st
import yaml
import traceback

from utils.helper import read_config, get_file_config_by_path, convert_to_int, format_top_contributors
from utils.ppt_export import generate_ppt
from database.get_summary_table import *
from database.database_process import create_oracle_engine
from database.get_top_contributors import get_top_attributes_by_difference
from llm.reson_code import get_reason_code
from llm.commentary import get_commentary, modify_commentary
from llm.chatbot import process_chatbot_query

# page Configuration
st.set_page_config(layout="wide")

# Setting up constants
EXCEL_DATA_PATH = "data"
config_file = "config/config.yaml"
excel_data_dir = "data"

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

@st.cache_resource
def load_engine(config):
    try:
        db_config = config.get('database', {})
        engine = create_oracle_engine(db_config)
        return engine
    except Exception as e:
        st.error(f"Failed to connect to database: {str(e)}")
        return None

def initialize_file_data(file_name):
    """Initialize data for a file if it doesn't exist"""
    try:
        if file_name not in st.session_state.file_data:
            with st.spinner('Loading file data...'):
                st.session_state.file_config = get_file_config_by_path(config, file_name)
                st.session_state.file_name = file_name

                summary_func_name = st.session_state.file_config.get('summary_table_function')
                summary_func = globals()[summary_func_name]
                df = summary_func(st.session_state.engine)
                df = df.map(convert_to_int)
                df = df.drop(columns=['Y/Y %', 'Q/Q %'])

                st.session_state.contributing_columns = st.session_state.file_config['contributing_columns']
                st.session_state.top_n = st.session_state.file_config['top_n']

                initial_selected_cells = get_reason_code(df, file_name)

                with st.spinner('Generating initial commentary...'):
                    top_contributors = get_top_attributes_by_difference(
                        st.session_state.engine,
                        initial_selected_cells,
                        st.session_state.file_config['table_name'],
                        st.session_state.contributing_columns,
                        st.session_state.top_n
                    )
                    top_contributors_formatted = format_top_contributors(top_contributors)
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

def render_selection_controls(edited_df, file_data):
    try:
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
            with st.spinner('Updating settings...'):
                if contributing_cols != st.session_state.contributing_columns or top_n != st.session_state.top_n:
                    st.session_state.contributing_columns = contributing_cols
                    st.session_state.top_n = top_n
                    with open(config_file, "w") as file:
                        config['excel_files'][st.session_state.file_name]['contributing_columns'] = list(contributing_cols)
                        config['excel_files'][st.session_state.file_name]['top_n'] = top_n
                        yaml.dump(config, file)
    except Exception as e:
        st.error(f"Error in selection controls: {str(e)}")

def render_selected_cells(file_data):
    try:
        st.text("")
        st.markdown("<h5 style='text-align: center;'>Selected Cells</h5>", unsafe_allow_html=True)
        container = st.container(height=200)

        with container:
            if not file_data['selected_cells']:
                st.info("No cells selected")
            else:
                cell_display = [f"{row}, {col}, {val}" 
                              for row, col, val in file_data['selected_cells']]
                selected_indices = st.multiselect(
                    "Selected cells",
                    options=range(len(cell_display)),
                    default=range(len(cell_display)),
                    format_func=lambda i: cell_display[i],
                    label_visibility="visible"
                )

                if len(selected_indices) != len(file_data['selected_cells']):
                    file_data['selected_cells'] = [file_data['selected_cells'][i] for i in selected_indices]
                    st.rerun()

        st.button("Reset", key="reset", on_click=lambda: reset_selections(file_data), use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying selected cells: {str(e)}")

def update_commentary(file_data):
    try:
        with st.spinner('Updating commentary...'):
            top_contributors = get_top_attributes_by_difference(
                st.session_state.engine,
                file_data['selected_cells'],
                st.session_state.file_config['table_name'],
                st.session_state.contributing_columns,
                st.session_state.top_n
            )
            top_contributors_formatted = format_top_contributors(top_contributors)
            file_data['commentary'] = get_commentary(top_contributors_formatted, st.session_state.file_name)
    except Exception as e:
        st.error(f"Error updating commentary: {str(e)}")

def process_chatbot():
    try:
        if st.session_state.chatbot_input:
            with st.spinner('Processing your query...'):
                st.session_state.chatbot_messages.append(f"You: {st.session_state.chatbot_input}")
                response = process_chatbot_query(st.session_state.engine, st.session_state.chatbot_input)
                st.session_state.chatbot_messages.append(f"Bot: {response}")
                st.rerun()
    except Exception as e:
        st.error(f"Error processing chatbot query: {str(e)}")

def export_to_ppt(file_data):
    try:
        with st.spinner('Generating PPT...'):
            ppt_file = generate_ppt(
                file_data['df'],
                file_data['commentary'],
                st.session_state.selected_file
            )
            return ppt_file
    except Exception as e:
        st.error(f"Error generating PPT: {str(e)}")
        return None

def reset_selections(file_data):
    """Reset to initial selected cells"""
    file_data['selected_cells'] = file_data['initial_selected_cells'].copy()
    st.rerun()

def main():
    try:
        st.markdown("<center><h1>Close Pack Commentary 📝</h1></center>", unsafe_allow_html=True)

        config = read_config(config_file)
        st.session_state.engine = load_engine(config)

        if not st.session_state.engine:
            st.error("Failed to initialize database connection")
            return

        init_session_state()

        # Left Sidebar - File Selection
        with st.sidebar:
            st.markdown("### File Selection")
            excel_files = [f for f in os.listdir(EXCEL_DATA_PATH) if f.endswith('.xlsx')]
            file_list = [Path(f).stem for f in excel_files]
            selected_file = st.selectbox("Select Slide", file_list)
            if st.button("Ok"):
                st.session_state.selected_file = selected_file
                initialize_file_data(selected_file)

        # Right Sidebar - Chatbot
        with st.sidebar:
            st.markdown("### Chatbot 🤖")
            for message in st.session_state.chatbot_messages:
                st.text(message)

            st.text_input("Message", key="chatbot_input", on_change=process_chatbot)

        # Main Content
        if st.session_state.selected_file:
            file_data = st.session_state.file_data[st.session_state.selected_file]
            col_a, col_b = st.columns([3, 2])

            # Column A - Data Overview and Cell Selection
            with col_a:
                st.markdown("### Summary Table 📊")
                edited_df = st.data_editor(
                    file_data['df'],
                    key=f"data_editor_{st.session_state.selected_file}",
                    hide_index=False
                )

                st.markdown("### Manual Selection 👇")
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
                st.markdown("### Commentary 📝")

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
                    user_comment = st.text_input(
                        "Type to modify analysis",
                        key=f"user_comment_input_{st.session_state.selected_file}"
                    )
                    if st.button("Update Commentary"):
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
                    if st.button("Generate PPT"):
                        ppt_file = export_to_ppt(file_data)
                        if ppt_file:
                            st.success("PPT generated successfully!")
        else:
            st.info("Please select a file from the sidebar and click 'Ok' to begin analysis.")

    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        st.error(f"Stack trace: {traceback.format_exc()}")

if __name__ == "__main__":
    main()