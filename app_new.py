import streamlit as st
import pandas as pd
import numpy as np
from config import load_config, save_config

# Set page config
st.set_page_config(layout="wide")

# Load custom CSS
def load_css():
    with open("style.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Call the function to load CSS
load_css()

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
st.markdown("<h2 class='app-title'>Interactive Dashboard</h2>", unsafe_allow_html=True)

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
    st.markdown("<div class='sidebar-header'>File Selection</div>", unsafe_allow_html=True)
    file_list = ["File1", "File2", "File3"]
    selected_file = st.selectbox("Select File", file_list)
    if st.button("Ok", use_container_width=True):
        st.session_state.selected_file = selected_file
        initialize_file_data(selected_file)

# Only show main content after file selection
if st.session_state.selected_file:
    file_data = initialize_file_data(st.session_state.selected_file)

    col_a, col_b, col_c = st.columns([3, 2, 1])

    # Column A
    with col_a:
        st.markdown('<div class="column-container">', unsafe_allow_html=True)

        # A Top - Data Overview
        st.markdown("<div class='section-header'>Data Overview</div>", unsafe_allow_html=True)
        df = file_data['df']
        edited_df = st.data_editor(df, key=f"data_editor_{st.session_state.selected_file}", hide_index=False)

        # A Bottom - Cell Selection with subsection border
        st.markdown("<div class='subsection'><div class='section-header'>Cell Selection</div>", unsafe_allow_html=True)
        left_col, right_col = st.columns(2)

        # A Bottom Left - Selection Controls
        with left_col:
            st.markdown("<div class='subsection-header'>Selection Controls</div>", unsafe_allow_html=True)
            
            # Use a custom HTML layout for side-by-side selectors without nested columns
            st.markdown("<div class='selectors-container'>", unsafe_allow_html=True)
            st.markdown("<div class='selector-label'>Select Row and Column</div>", unsafe_allow_html=True)
            
            # Create the selectors in a single row using HTML styling
            row_col_container = st.container()
            row_index = row_col_container.selectbox("Select Row", edited_df.index.tolist(), key="row_selector", label_visibility="collapsed")
            column = row_col_container.selectbox("Select Column", edited_df.columns.tolist(), key="column_selector", label_visibility="collapsed")
            
            st.markdown("</div>", unsafe_allow_html=True)

            if st.button("+ Add Selection", use_container_width=True):
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
        with left_col:
            st.markdown("<h5 style='text-align: center;'>Selection Controls</h5>", unsafe_allow_html=True)
            
            # Create two columns for row and column selection
            row_col, column_col = st.columns(2)
            
            # Place row selection in the first column
            with row_col:
                row_index = st.selectbox("Select Row", edited_df.index.tolist())
            
            # Place column selection in the second column
            with column_col:
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

            # Add spacing
            st.write("")

            # Only keep the Reset button (removed Clear All)
            if st.button("Reset", key="reset", use_container_width=True):
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
        st.markdown('<div class="column-container">', unsafe_allow_html=True)
        st.markdown("<div class='section-header'>Commentary</div>", unsafe_allow_html=True)
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
        if st.button("Update Commentary", key=f"update_commentary_btn_{st.session_state.selected_file}", use_container_width=True):
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
        st.markdown('<div class="column-container">', unsafe_allow_html=True)
        st.markdown("<div class='section-header'>Chatbot</div>", unsafe_allow_html=True)

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
                                <div class="chat-message user-message">
                                    <div class="message-content">
                                        {message[4:]}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                f"""
                                <div class="chat-message bot-message">
                                    <div class="message-content">
                                        {message[5:]}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

            st.markdown('<hr class="chat-divider">', unsafe_allow_html=True)

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
    st.markdown('<div class="welcome-message">', unsafe_allow_html=True)
    st.info("Please select a file from the sidebar and click 'Ok' to begin analysis.")
    st.markdown('</div>', unsafe_allow_html=True)