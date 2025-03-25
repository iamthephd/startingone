function handleFileSelection() {
    const filename = $('#fileSelect').val();
    if (!filename) return;

    // Show confirmation popup
    if (confirm(`Are you sure you want to load the file: ${filename}? This will reload the page.`)) {
        // Reload the page on confirmation
        location.reload();
    } else {
        // Reset the dropdown if the user cancels
        $('#fileSelect').val('');
    }
}
