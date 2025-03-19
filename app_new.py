import streamlit as st
import pandas as pd
import numpy as np
from config import load_config, save_config

# Set page config
st.set_page_config(layout="wide")

# Initialize session state
if 'selected_file' not in st.session_state:
    st.session_state.selected_file = None
if 'file_data' not in st.session_state:
    st.session_state.file_data = {}
if 'commentary' not in st.session_state:
    st.session_state.commentary = ""
if 'contributing_columns' not in st.session_state:
    config = load_config()
    st.session_state.contributing_columns = config['contributing_columns']
    st.session_state.top_n = config['top_n']
if 'chatbot_messages' not in st.session_state:
    st.session_state.chatbot_messages = []

def get_summary_table(file_name):
    """Return a sample DataFrame for demonstration"""
    np.random.seed(42)
    df = pd.DataFrame({
        'Date': pd.date_range(start='2023-01-01', periods=10),
        'Sales': np.random.randint(1000, 5000, 10),
        'Revenue': np.random.randint(5000, 15000, 10),
        'Customers': np.random.randint(100, 500, 10),
        'Region': np.random.choice(['North', 'South', 'East', 'West'], 10),
        'Category': np.random.choice(['Electronics', 'Clothing', 'Food'], 10)
    })
    return df

def get_reason_code(df, file_name):
    """Return significant differences as tuples"""
    return [
        (0, 'Sales', df.loc[0, 'Sales']),
        (2, 'Revenue', df.loc[2, 'Revenue'])
    ]

def get_commentary(selected_cells, file_name, contributing_columns, top_n):
    """Generate commentary based on selected cells and parameters"""
    if not selected_cells:
        return "No cells selected for analysis."

    commentary = f"Analysis based on {len(selected_cells)} selected data points:\n\n"
    for row, col, val in selected_cells:
        commentary += f"- {col} value at row {row} is {val}\n"

    if contributing_columns:
        commentary += f"\nContributing columns considered: {', '.join(contributing_columns)}"

    commentary += f"\nAnalyzing top {top_n} significant factors."
    return commentary

def modify_commentary(user_comment):
    """Modify selected cells, contributing columns and top_n based on user comment"""
    if "focus on sales" in user_comment.lower():
        st.session_state.contributing_columns = ['Sales', 'Revenue']
        st.session_state.top_n = 3
        save_config({
            'contributing_columns': st.session_state.contributing_columns,
            'top_n': st.session_state.top_n
        })
    elif "show more items" in user_comment.lower():
        st.session_state.top_n = min(10, st.session_state.top_n + 2)
        save_config({
            'contributing_columns': st.session_state.contributing_columns,
            'top_n': st.session_state.top_n
        })
    elif "show fewer items" in user_comment.lower():
        st.session_state.top_n = max(1, st.session_state.top_n - 2)
        save_config({
            'contributing_columns': st.session_state.contributing_columns,
            'top_n': st.session_state.top_n
        })

    return get_commentary(
        st.session_state.selected_cells,
        st.session_state.selected_file,
        st.session_state.contributing_columns,
        st.session_state.top_n
    )

def process_chatbot_query(query):
    """Process chatbot queries and return responses"""
    responses = {
        "help": "I can help you analyze the data and understand trends.",
        "data": "The current dataset shows sales and revenue information.",
        "analysis": "I can help you analyze specific data points or trends.",
        "trends": "Looking at the data, there are some interesting patterns in sales and revenue.",
        "summary": "The data shows various metrics including sales, revenue, and customer information across different regions and categories."
    }

    query = query.lower()
    for key, response in responses.items():
        if key in query:
            return response
    return "I'm here to help with your data analysis questions. Try asking about specific metrics or trends."

# Center-aligned title with smaller font
st.markdown("<h2 style='text-align: center;'>Interactive Dashboard</h2>", unsafe_allow_html=True)

# Initialize file data structure if needed
def initialize_file_data(file_name):
    """Initialize data for a file if it doesn't exist"""
    if file_name not in st.session_state.file_data:
        df = get_summary_table(file_name)
        selected_cells = get_reason_code(df, file_name)
        commentary = get_commentary(
            selected_cells,
            file_name,
            st.session_state.contributing_columns,
            st.session_state.top_n
        )
        st.session_state.file_data[file_name] = {
            'df': df,
            'selected_cells': selected_cells,
            'commentary': commentary
        }
    return st.session_state.file_data[file_name]

# Sidebar
with st.sidebar:
    file_list = ["File1", "File2", "File3"]
    selected_file = st.selectbox("Select File", file_list)
    if st.button("Ok"):
        st.session_state.selected_file = selected_file
        initialize_file_data(selected_file)

# Only show main content after file selection
if st.session_state.selected_file:
    file_data = initialize_file_data(st.session_state.selected_file)

    col_a, col_b, col_c = st.columns([3, 2, 1])

    # Column A
    with col_a:
        st.markdown('<div class="column-container section-border">', unsafe_allow_html=True)

        # A Top - Data Overview
        st.markdown("<h4 style='text-align: center;'>Data Overview</h4>", unsafe_allow_html=True)
        df = file_data['df']
        edited_df = st.data_editor(df, key=f"data_editor_{st.session_state.selected_file}", hide_index=False)

        # A Bottom - Cell Selection with subsection border
        st.markdown("<div class='subsection-border'><h4 style='text-align: center;'>Cell Selection</h4>", unsafe_allow_html=True)
        left_col, right_col = st.columns(2)

        # A Bottom Left - Selection Controls
        with left_col:
            st.markdown("<h5 style='text-align: center;'>Selection Controls</h5>", unsafe_allow_html=True)
            row_index = st.selectbox("Select Row", edited_df.index.tolist())
            column = st.selectbox("Select Column", edited_df.columns.tolist())

            if st.button("+ Add Selection"):
                if row_index is not None and column is not None:
                    value = edited_df.loc[row_index, column]
                    new_selection = (row_index, column, value)
                    if new_selection in file_data['selected_cells']:
                        st.warning(f"Cell ({row_index}, {column}, {value}) is already selected!")
                    else:
                        file_data['selected_cells'].append(new_selection)
                        file_data['commentary'] = get_commentary(
                            file_data['selected_cells'],
                            st.session_state.selected_file,
                            st.session_state.contributing_columns,
                            st.session_state.top_n
                        )
                        st.rerun()

            # Additional Settings in an expander
            with st.expander("Additional Settings", expanded=False):
                contributing_cols = st.multiselect(
                    "Contributing Columns",
                    edited_df.columns.tolist(),
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
                        save_config({
                            'contributing_columns': contributing_cols,
                            'top_n': top_n
                        })
                        file_data['commentary'] = get_commentary(
                            file_data['selected_cells'],
                            st.session_state.selected_file,
                            st.session_state.contributing_columns,
                            st.session_state.top_n
                        )


        # A Bottom Right - Selected Cells with fixed height and scrolling
        with right_col:
            st.markdown("<h5 style='text-align: center;'>Selected Cells</h5>", unsafe_allow_html=True)

            # Create a fixed-height scrollable container
            container = st.container(height=200, border=True)

            # Use the container to display the selected cells
            with container:
                if not file_data['selected_cells']:
                    st.info("No cells selected")
                else:
                    for i, (row, col, val) in enumerate(file_data['selected_cells']):
                        # Use a horizontal layout without nested columns
                        cell_info = f"({row}, {col}, {val})"

                        # Display cell info and remove button side by side
                        st.markdown(
                            f"""<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                                <code style="background-color: var(--code-bg-color); color: var(--code-text-color); padding: 3px 6px; border-radius: 3px; flex-grow: 1;">{cell_info}</code>
                                <span>&nbsp;</span>
                            </div>""",
                            unsafe_allow_html=True
                        )

                        if st.button("❌", key=f'remove_{i}_{st.session_state.selected_file}', help=f'Remove selection'):
                            file_data['selected_cells'].pop(i)
                            file_data['commentary'] = get_commentary(
                                file_data['selected_cells'],
                                st.session_state.selected_file,
                                st.session_state.contributing_columns,
                                st.session_state.top_n
                            )
                            st.rerun()

            # Add spacing
            st.write("")

            # Add buttons without column nesting
            if st.button("Clear All", key="clear_all"):
                file_data['selected_cells'] = []
                file_data['commentary'] = get_commentary(
                    file_data['selected_cells'],
                    st.session_state.selected_file,
                    st.session_state.contributing_columns,
                    st.session_state.top_n
                )
                st.rerun()

            st.write("") # Add minimal spacing between buttons

            if st.button("Reset", key="reset"):
                file_data['selected_cells'] = get_reason_code(file_data['df'], st.session_state.selected_file)
                file_data['commentary'] = get_commentary(
                    file_data['selected_cells'],
                    st.session_state.selected_file,
                    st.session_state.contributing_columns,
                    st.session_state.top_n
                )
                st.rerun()

        if st.button("Modify Commentary", use_container_width=True):
            file_data['commentary'] = get_commentary(
                file_data['selected_cells'],
                st.session_state.selected_file,
                st.session_state.contributing_columns,
                st.session_state.top_n
            )
        st.markdown('</div></div>', unsafe_allow_html=True)

    # Column B - Commentary
    with col_b:
        st.markdown('<div class="column-container section-border">', unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center;'>Commentary</h4>", unsafe_allow_html=True)
        if file_data['commentary']:
            st.text_area(
                label="Commentary",
                value=file_data['commentary'],
                height=200,
                key=f"commentary_display_{st.session_state.selected_file}",
                label_visibility="collapsed"
            )
        else:
            st.info("Click 'Modify Commentary' to generate analysis")

        user_comment = st.text_input("Type to modify analysis", key=f"user_comment_input_{st.session_state.selected_file}")
        if st.button("Update Commentary", key=f"update_commentary_btn_{st.session_state.selected_file}"):
            if user_comment:
                if "focus on sales" in user_comment.lower():
                    st.session_state.contributing_columns = ['Sales', 'Revenue']
                    st.session_state.top_n = 3
                    save_config({
                        'contributing_columns': st.session_state.contributing_columns,
                        'top_n': st.session_state.top_n
                    })
                elif "show more items" in user_comment.lower():
                    st.session_state.top_n = min(10, st.session_state.top_n + 2)
                    save_config({
                        'contributing_columns': st.session_state.contributing_columns,
                        'top_n': st.session_state.top_n
                    })
                elif "show fewer items" in user_comment.lower():
                    st.session_state.top_n = max(1, st.session_state.top_n - 2)
                    save_config({
                        'contributing_columns': st.session_state.contributing_columns,
                        'top_n': st.session_state.top_n
                    })

                file_data['commentary'] = get_commentary(
                    file_data['selected_cells'],
                    st.session_state.selected_file,
                    st.session_state.contributing_columns,
                    st.session_state.top_n
                )
                st.rerun()
            else:
                st.error("Please provide comments to update the commentary")
        st.markdown('</div>', unsafe_allow_html=True)

    # Column C - Chatbot
    with col_c:
        st.markdown('<div class="column-container section-border">', unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center;'>Chatbot</h4>", unsafe_allow_html=True)

        main_container = st.container(border=True)
        with main_container:
            message_container = st.container(height=300)

            with message_container:
                if not st.session_state.chatbot_messages:
                    st.info("Type a message to start chatting")
                else:
                    for message in st.session_state.chatbot_messages:
                        if message.startswith("You: "):
                            st.markdown(
                                f"""
                                <div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
                                    <div style="background-color: #DCF8C6; border-radius: 10px; padding: 8px 12px; max-width: 80%; box-shadow: 0 1px 1px rgba(0,0,0,0.1);">
                                        {message[4:]}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                f"""
                                <div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">
                                    <div style="background-color: white; border-radius: 10px; padding: 8px 12px; max-width: 80%; box-shadow: 0 1px 1px rgba(0,0,0,0.1);">
                                        {message[5:]}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

            st.markdown('<hr style="margin: 5px 0;">', unsafe_allow_html=True)

            chatbot_input = st.text_input(
                "Message",
                placeholder="Type a message...",
                label_visibility="collapsed",
                key="chatbot_input"
            )

            send_button = st.button("Send", key="send_chatbot", use_container_width=True)

            if send_button and chatbot_input:
                st.session_state.chatbot_messages.append(f"You: {chatbot_input}")
                response = process_chatbot_query(chatbot_input)
                st.session_state.chatbot_messages.append(f"Bot: {response}")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Please select a file from the sidebar and click 'Ok' to begin analysis.")