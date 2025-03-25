from flask import send_file
import io

@app.route('/api/export_ppt', methods=['POST'])
def export_to_ppt():
    """Get details for a specific file"""
    data = request.json
    df = pd.DataFrame(data['table_data']['data'])
    columns = data['table_data']['columns']
    df = df.set_index(columns[0])

    # Generate PowerPoint file
    pptx_bytes = generate_ppt(df, data['selected_cells'], data['commentary'], data['filename'])
    
    # Create a BytesIO object to send the file
    pptx_file = io.BytesIO(pptx_bytes)
    pptx_file.seek(0)
    
    # Send the file as an attachment
    return send_file(
        pptx_file, 
        mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
        as_attachment=True, 
        download_name=f"{data['filename'].replace('.', '_')}_analysis.pptx"
    )


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
            
            // Try to parse error message if possible
            let errorMessage = 'Error creating PowerPoint file. Please try again.';
            try {
                const errorResponse = JSON.parse(xhr.responseText);
                errorMessage = errorResponse.error || errorMessage;
            } catch(e) {}
            
            showAlert(errorMessage, 'danger');
            
            // Reset button state
            $button.html(originalText);
            $button.prop('disabled', false);
        },
        complete: function() {
            // Ensure button is re-enabled even if there's an error
            $button.html(originalText);
            $button.prop('disabled', false);
        }
    });
}