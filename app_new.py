# Main app layout
st.title("LLM Commentary Generation")

# Sidebar for file selection
with st.sidebar:
    # File selection
    file_options = ["cmdm_service", "sales_data", "revenue_report", "customer_analytics"]
    selected_file = st.selectbox("Slide Selection", file_options)
    st.button("Ok", key="confirm_file")

# Main layout with three columns
col1, col2, col3 = st.columns([2, 2, 1])

# First column - Summary Table and Manual Selection
with col1:
    # Get summary table based on selected file
    summary_table = get_summary_table(selected_file)
    
    # Display summary table
    st.subheader("Summary Table")
    st.dataframe(summary_table, use_container_width=True)
    
    # Manual selection form
    st.subheader("Manual Selection (Optional)")
    
    # Create a form to prevent rerun on every selection change
    with st.form("manual_selection_form"):
        # Load current config
        config = load_config(selected_file)
        
        # Get reason codes from summary table
        reason_codes = summary_table.index.tolist()
        columns = summary_table.columns.tolist()
        
        # Selection dropdowns
        selected_reason = st.selectbox("Select Reason Code", [""] + reason_codes)
        selected_column = st.selectbox("Select Column", [""] + columns)
        
        # Contributing columns (multi-select)
        all_contributing_columns = ["Customer", "Product", "Region", "Channel", "Segment"]
        default_contributing = config.get("contributing_columns", [])
        contributing_columns = st.multiselect(
            "Contributing Columns", 
            all_contributing_columns, 
            default=default_contributing
        )
        
        # Top n selection
        top_n = st.selectbox("Top n", list(range(1, 11)), index=config.get("top_n", 3) - 1)
        
        # Form submission button
        add_selection_submitted = st.form_submit_button("+ Add Selection")
    
    # Reset and Clear All buttons
    col_reset, col_clear = st.columns(2)
    with col_reset:
        reset = st.button("🔄 Reset")
    with col_clear:
        clear_all = st.button("🗑️ Clear All")

# Second column - Current Selections and Commentary
with col2:
    # Current selections
    st.subheader("Current Selections")
    
    # Get significant differences
    significant_diffs = get_reason_code(summary_table, selected_file)
    
    # Display current selections
    for reason, column, value in significant_diffs:
        st.text(f"({reason}, {column}, {value})")
    
    # Get top contributors
    contributors_data = get_top_contributors(
        significant_diffs, 
        selected_file, 
        config.get("contributing_columns", []), 
        config.get("top_n", 3)
    )
    
    # Generate commentary
    commentaries = get_commentary(contributors_data)
    
    # Display generated commentary
    st.subheader("Generated Commentary")
    
    # Y/Y Commentary
    if "Y/Y" in commentaries:
        st.markdown("**Y/Y Commentary:**")
        st.text(commentaries["Y/Y"])
        st.text("...")
    
    # Q/Q Commentary
    if "Q/Q" in commentaries:
        st.markdown("**Q/Q Commentary:**")
        st.text(commentaries["Q/Q"])
        st.text("...")
    
    # Modify commentary button
    st.button("Modify commentary...")
    
    # Chat input for modifying commentary
    st.text_input("Enter your comments here...", key="chat_input")

# Third column - ChatBot (placeholder for now)
with col3:
    st.subheader("ChatBot 🤖")
    
    # Display a simple chat interface mockup
    st.markdown("""
    <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px;">
    <p>Find the total amount for each quarter</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Mock chatbot response
    st.markdown("""
    <div style="background-color: #e6f3ff; padding: 10px; border-radius: 5px;">
    <p>The total amount for each date is as follows:</p>
    <p>•2024Q1: -$267,251,091.67</p>
    <p>•2024Q2: -$291,666,372.66</p>
    <p>•2024Q3: -$283,156,445.66</p>
    <p>•2024Q4: -$286,165,111.58</p>
    <p>•2025Q1: -$352,851,284.65</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Placeholder for user typing
    st.text_input("Typing...", key="typing_placeholder")