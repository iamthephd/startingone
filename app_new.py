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
    if 'chatbot_expanded' not in st.session_state:
        st.session_state.chatbot_expanded = False

def process_chat_input():
    """Process the chat input and update chat history"""
    if st.session_state.chatbot_input:
        query = st.session_state.chatbot_input
        st.session_state.chatbot_input = ""  # Clear the input
        st.session_state.chatbot_messages.append(f"You: {query}")
        
        # Process query directly without rerunning
        # Replace this with your actual query processing function
        response = process_chatbot_query(st.session_state.engine, query, st.session_state.config['table_name'])
        st.session_state.chatbot_messages.append(f"Bot: {response}")
        st.session_state.chatbot_expanded = True

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
    
    # Chat input with on_change to handle Enter key press
    st.text_input(
        "Message",
        placeholder="Type a message and press Enter...",
        label_visibility="collapsed",
        key="chatbot_input",
        on_change=process_chat_input
    )

# In your main function, keep the popover but use JavaScript to auto-click it when needed
def main():
    # ... your existing code ...
    
    # Chat Popover at bottom right with auto-expand functionality
    chatbot_id = "chatbot-popover"
    with st.popover("Chat 🤖", use_container_width=False, key=chatbot_id):
        render_chatbot()
    
    # Auto-open popover using JavaScript when needed
    if st.session_state.chatbot_expanded:
        # Reset the flag immediately to avoid infinite clicks
        st.session_state.chatbot_expanded = False
        
        # Inject JavaScript to auto-click the popover button
        st.markdown(
            f"""
            <script>
                // Use a small delay to ensure the DOM is loaded
                setTimeout(function() {{
                    // Find the button by its aria-controls attribute
                    var popoverButton = document.querySelector('button[aria-controls="{chatbot_id}"]');
                    if (popoverButton && !popoverButton.classList.contains('st-emotion-cache-1c7y2kw')) {{
                        popoverButton.click();
                    }}
                }}, 100);
            </script>
            """,
            unsafe_allow_html=True
        )