function handleFileSelection() {
    const filename = $('#fileSelect').val();
    if (!filename) return;

    // If this flag is set, it means the reload already occurred, so clear it and do nothing.
    if (sessionStorage.getItem('reloading') === 'true') {
        sessionStorage.removeItem('reloading');
        return;
    }
    
    // Only show confirmation if the flag is not set.
    if (confirm(`Are you sure you want to load the file: ${filename}? This will reload the page.`)) {
        // Set the flag before reloading to prevent the confirmation from showing after reload.
        sessionStorage.setItem('reloading', 'true');
        location.reload();
    } else {
        // Reset the selection if the user cancels.
        $('#fileSelect').val('');
    }
}
