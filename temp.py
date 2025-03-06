import streamlit as st
import pandas as pd
from typing import List, Tuple
from utils.file_processor import process_file, SAMPLE_FILES
from utils.insights_generator import generate_insights
from utils.ppt_generator import generate_ppt

def load_custom_css():
    """Load custom CSS styles"""
    with open("styles/custom.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
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

def get_default_tuples(df: pd.DataFrame) -> List[Tuple[str, str, any]]:
    """Generate default tuples from the DataFrame"""
    if df is None:
        return []
    index_name = df.index[0]
    column_name = df.columns[0]
    return [(index_name, column_name, df.loc[index_name, column_name])]

def format_tuple(tup: Tuple[str, str, any]) -> str:
    """Format tuple for display"""
    return f"({tup[0]}, {tup[1]}, {tup[2]})"

def add_tuple(index_name: str, column_name: str):
    """Add a new tuple to the list"""
    if index_name and column_name:
        value = st.session_state.df.loc[index_name, column_name]
        new_tuple = (index_name, column_name, value)
        if new_tuple in st.session_state.tuples:
            st.session_state.warning_message = f"Tuple ({index_name}, {column_name}, {value}) already exists!"
            return
        st.session_state.warning_message = None
        st.session_state.tuples.append(new_tuple)
        st.session_state.insights = None

def auto_select():
    """Add default tuples to the current selection"""
    default_tuples = get_default_tuples(st.session_state.df)
    st.session_state.default_tuples = default_tuples
    st.session_state.has_defaults = True
    for tup in default_tuples:
        if tup not in st.session_state.tuples:
            st.session_state.tuples.append(tup)

def handle_file_selection():
    """Handle file selection and processing"""
    st.session_state.file_selected = True
    filename = st.session_state.selected_file
    df = process_file(filename)
    if df is not None:
        st.session_state.df = df
        st.session_state.tuples = []
        st.session_state.has_defaults = False
        st.session_state.warning_message = None
        st.session_state.insights = None

def render_file_selector():
    """Render the file selection column"""
    st.markdown('<p class="section-header">File Selection</p>', unsafe_allow_html=True)
    st.selectbox(
        "Choose a file to analyze",
        options=list(SAMPLE_FILES.keys()),
        key="selected_file",
    )
    if st.button("Load File", use_container_width=True):
        handle_file_selection()

def render_dataframe_section():
    """Render the DataFrame and insights section"""
    if st.session_state.df is not None:
        st.markdown('<p class="section-header">Data Preview</p>', unsafe_allow_html=True)
        st.dataframe(st.session_state.df, use_container_width=True, height=400)

        # Full-width Generate Insights button
        if st.button("Generate Insights", use_container_width=True):
            if not st.session_state.tuples:
                st.warning("Please select at least one data point first!")
            else:
                st.session_state.insights = generate_insights(st.session_state.tuples)

        if st.session_state.insights:
            st.markdown('<div class="insight-container">', unsafe_allow_html=True)
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown("### Generated Insights")
            with col2:
                if st.button("📋 Copy", key="copy_insights"):
                    st.write("Insights copied to clipboard!")
                    st.markdown(
                        f"""
                        <script>
                            navigator.clipboard.writeText("{st.session_state.insights}");
                        </script>
                        """,
                        unsafe_allow_html=True
                    )
            st.markdown(st.session_state.insights)
            st.markdown('</div>', unsafe_allow_html=True)

            ppt_buffer = generate_ppt(st.session_state.insights, st.session_state.tuples)
            st.download_button(
                label="📥 Download PPT Report",
                data=ppt_buffer,
                file_name="analysis_report.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True
            )

def render_controls_section():
    """Render the controls and tuples section"""
    st.markdown('<p class="section-header">Controls</p>', unsafe_allow_html=True)
    
    # Auto select button
    if st.button("🎯 Auto Select", use_container_width=True):
        auto_select()

    # Selection controls
    st.markdown("**Row and Column Selection**")
    col_index, col_column = st.columns(2)
    
    with col_index:
        index_name = st.selectbox(
            "Select Row Index",
            options=st.session_state.df.index,
            key="index_select"
        )
    
    with col_column:
        column_name = st.selectbox(
            "Select Column",
            options=st.session_state.df.columns,
            key="column_select"
        )

    if st.button("➕ Add Selection", use_container_width=True):
        add_tuple(index_name, column_name)

    # Display selected value
    if index_name and column_name:
        selected_value = st.session_state.df.loc[index_name, column_name]
        st.info(f"Selected Value: {selected_value}")

    # Warning message
    if st.session_state.warning_message:
        st.warning(st.session_state.warning_message)

    # Reset and Clear buttons
    col_reset, col_clear = st.columns(2)
    with col_reset:
        if st.button("🔄 Reset", use_container_width=True):
            if st.session_state.has_defaults:
                st.session_state.tuples = st.session_state.default_tuples.copy()
            else:
                st.info("No default selections available")

    with col_clear:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.tuples = []

    # Display current tuples
    st.markdown('<p class="section-header">Current Selections</p>', unsafe_allow_html=True)
    for i, tup in enumerate(st.session_state.tuples):
        with st.container():
            col_tuple, col_delete = st.columns([4, 1])
            with col_tuple:
                st.code(format_tuple(tup), language="python")
            with col_delete:
                if st.button("🗑️", key=f"delete_{i}"):
                    st.session_state.tuples.pop(i)
                    st.session_state.insights = None
                    st.rerun()

def main():
    st.set_page_config(page_title="DataFrame Tuple Manager", layout="wide")
    load_custom_css()
    initialize_session_state()

    st.markdown('<h1 class="main-header">DataFrame Tuple Manager</h1>', unsafe_allow_html=True)

    # Create three columns with specific ratios
    col_files, col_data, col_controls = st.columns([1, 4, 2])

    with col_files:
        render_file_selector()

    with col_data:
        render_dataframe_section()

    with col_controls:
        if st.session_state.file_selected and st.session_state.df is not None:
            render_controls_section()

if __name__ == "__main__":
    main()


###
# def render_dataframe_section():
#     """Render the DataFrame and insights section"""
#     if st.session_state.df is not None:
#         st.markdown('<p class="section-header">Data Preview</p>', unsafe_allow_html=True)
#         st.dataframe(st.session_state.df, use_container_width=True, height=400)