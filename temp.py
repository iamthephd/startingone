function handleExportToPPT() {
    // Show loading state
    const $button = $('#exportPptBtn');
    const originalText = $button.html();
    $button.html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Exporting...');
    $button.prop('disabled', true);
    
    // Get current file name and commentary
    const filename = $('#fileSelect').val();
    const commentary = $('#commentaryText').html(); // Using HTML to preserve formatting
    
    if (!filename) {
        showAlert('Please select a file first.', 'warning');
        $button.html(originalText);
        $button.prop('disabled', false);
        return;
    }
    
    console.log('Exporting to PPT:', filename);
    
    // Extract table data in a format suitable for pandas DataFrame conversion
    const tableData = extractTableData();
    
    // Prepare data for the API call
    const data = {
        filename: filename,
        commentary: commentary,
        selected_cells: selectedCells,
        table_data: tableData,
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

// Helper function to extract table data in a format suitable for pandas DataFrame
function extractTableData() {
    const table = $('#summaryTable').DataTable();
    const headers = [];
    
    // Extract column headers
    $('#summaryTable thead th').each(function() {
        headers.push($(this).text());
    });
    
    // Extract row data
    const rows = [];
    $('#summaryTable tbody tr').each(function() {
        const rowData = {};
        $(this).find('td').each(function(index) {
            // First column is usually the row identifier
            if (index === 0) {
                rowData[headers[index] || 'index'] = $(this).text();
            } else {
                // Try to convert numeric values
                const value = $(this).data('value');
                const numValue = parseFloat(value);
                rowData[headers[index] || `column${index}`] = isNaN(numValue) ? value : numValue;
            }
        });
        rows.push(rowData);
    });
    
    return {
        columns: headers,
        data: rows
    };
}