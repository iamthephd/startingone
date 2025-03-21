def init_session_state():
    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None
    if 'file_data' not in st.session_state:
        st.session_state.file_data = {}
    if 'commentary' not in st.session_state:
        st.session_state.commentary = ""
    if 'chatbot_messages' not in st.session_state:
        st.session_state.chatbot_messages = []
    if 'chatbot_open' not in st.session_state:
        st.session_state.chatbot_open = False

def process_chat_input():
    """Process the chat input and update chat history"""
    if st.session_state.chatbot_input:
        query = st.session_state.chatbot_input
        st.session_state.chatbot_input = ""  # Clear the input
        st.session_state.chatbot_messages.append(f"You: {query}")
        
        # Get response immediately without rerunning
        # Simulated response for testing - replace with your actual function
        response = f"Response to: {query}"  # Replace with actual process_chatbot_query function
        st.session_state.chatbot_messages.append(f"Bot: {response}")

def toggle_chatbot():
    """Toggle the chatbot open/closed state"""
    st.session_state.chatbot_open = not st.session_state.chatbot_open

def render_chatbot():
    """Render the chatbot that stays open during interaction"""
    # Only render if the chatbot is open
    if st.session_state.chatbot_open:
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
        
        if st.button("Close Chat", key="close_chat_btn"):
            st.session_state.chatbot_open = False
            st.rerun()

# In your main function, replace the chat popover with:
def main():
    # ... your existing code ...
    
    # Chat button at bottom right
    if not st.session_state.chatbot_open:
        if st.button("Chat 🤖", key="open_chat_btn"):
            st.session_state.chatbot_open = True
            st.rerun()
    else:
        # Render the chatbot directly without a popover
        st.markdown("<div style='border: 1px solid #e0e0e0; border-radius: 5px; padding: 10px; margin-top: 20px;'><h3>Chat 🤖</h3>", unsafe_allow_html=True)
        render_chatbot()
        st.markdown("</div>", unsafe_allow_html=True)