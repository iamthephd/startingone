function handleExportToPPT() {
    // Show loading state
    const $button = $('#exportPptBtn');
    const originalText = $button.html();
    $button.html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Exporting...');
    $button.prop('disabled', true);
    
    // Get current file name, table data, and commentary
    const filename = $('#fileSelect').val();
    const commentary = $('#commentaryText').html(); // Using HTML to preserve formatting
    
    if (!filename) {
        showAlert('Please select a file first.', 'warning');
        $button.html(originalText);
        $button.prop('disabled', false);
        return;
    }
    
    console.log('Exporting to PPT:', filename);
    
    // Prepare data for the API call
    const data = {
        filename: filename,
        commentary: commentary,
        selected_cells: selectedCells,
        table_html: $('#summaryTable').parent().html(),
        timestamp: new Date().getTime() // Add timestamp to prevent caching
    };
    
    // Send data to the server for PPT generation
    $.ajax({
        url: '/api/export_ppt',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        xhrFields: {
            responseType: 'blob' // Important for handling binary response
        },
        success: function(blob) {
            // Create a download link for the returned file
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${filename.replace(/\.[^/.]+$/, '')}_analysis.pptx`;
            document.body.appendChild(a);
            a.click();
            
            // Clean up
            setTimeout(() => {
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                showAlert('PowerPoint file exported successfully!', 'success');
            }, 1000);
        },
        error: function(xhr, status, error) {
            console.error('Error exporting to PPT:', {xhr, status, error});
            showAlert('Error creating PowerPoint file. Please try again.', 'danger');
        },
        complete: function() {
            // Reset button state
            $button.html(originalText);
            $button.prop('disabled', false);
        }
    });
}