function appendMessage(message, sender) {
    const messageElement = $('<div>').addClass(`message ${sender}`);

    // Check for markdown-like table or plain text
    if (isMarkdownTable(message)) {
        const tableHTML = markdownToHTMLTable(message);
        messageElement.html(tableHTML);
    } else {
        messageElement.text(message);
    }

    chatbotMessages.append(messageElement);

    // Scroll to bottom
    chatbotMessages.scrollTop(chatbotMessages[0].scrollHeight);
}

// Check if the message contains a markdown-like table
function isMarkdownTable(message) {
    return message.includes('|') && message.includes('---');
}

// Convert markdown table to HTML
function markdownToHTMLTable(markdown) {
    const lines = markdown.trim().split('\n');
    const headers = lines[0].split('|').map(h => h.trim()).filter(h => h);
    const rows = lines.slice(2).map(line =>
        line.split('|').map(cell => cell.trim()).filter(cell => cell)
    );

    let tableHTML = `
        <div class="chat-bubble">
            <table class="chat-table">
                <thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead>
                <tbody>
                    ${rows.map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`).join('')}
                </tbody>
            </table>
        </div>
    `;

    return tableHTML;
}
