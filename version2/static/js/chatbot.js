$(document).ready(function() {
    const chatbotIcon = $('#chatbot-icon');
    const chatbotPanel = $('#chatbot-panel');
    const chatbotClose = $('.chatbot-close');
    const chatbotInput = $('#chatbot-input');
    const chatbotSend = $('#chatbot-send');
    const chatbotMessages = $('.chatbot-messages');
    
    // Toggle chatbot panel when icon is clicked
    chatbotIcon.on('click', function() {
        chatbotPanel.toggleClass('hidden');
        if (!chatbotPanel.hasClass('hidden')) {
            chatbotInput.focus();
        }
    });
    
    // Close chatbot panel when close icon is clicked
    chatbotClose.on('click', function() {
        chatbotPanel.addClass('hidden');
    });
    
    // Send message when send button is clicked
    chatbotSend.on('click', sendMessage);
    
    // Send message when Enter key is pressed
    chatbotInput.on('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    function sendMessage() {
        const message = chatbotInput.val().trim();
        if (!message) return;
        
        // Add user message to chat
        appendMessage(message, 'user');
        
        // Clear input
        chatbotInput.val('');
        
        // Show typing indicator
        showTypingIndicator();
        
        // Send message to backend
        $.ajax({
            url: '/api/chatbot',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ query: message }),
            success: function(data) {
                // Remove typing indicator
                removeTypingIndicator();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Add bot response to chat
                appendMessage(data.reply, 'bot');
            },
            error: function(error) {
                // Remove typing indicator
                removeTypingIndicator();
                
                console.error('Error sending message to chatbot:', error);
                appendMessage('Sorry, I encountered an error. Please try again later.', 'bot error');
            }
        });
    }
    
    function appendMessage(message, sender) {
        const messageElement = $('<div>').addClass(`message ${sender}`).text(message);
        chatbotMessages.append(messageElement);
        
        // Scroll to bottom
        chatbotMessages.scrollTop(chatbotMessages[0].scrollHeight);
    }
    
    function showTypingIndicator() {
        const typingElement = $('<div>')
            .addClass('message bot typing')
            .attr('id', 'typing-indicator')
            .html('<span></span><span></span><span></span>');
        
        chatbotMessages.append(typingElement);
        
        // Scroll to bottom
        chatbotMessages.scrollTop(chatbotMessages[0].scrollHeight);
    }
    
    function removeTypingIndicator() {
        $('#typing-indicator').remove();
    }
});
