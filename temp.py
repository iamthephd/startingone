function handleFileSelection() {
    const filename = $('#fileSelect').val();
    if (!filename) return;

    console.log(`File selected: ${filename}`);
    
    // Reset all state
    selectedCells = [];
    originalSelectedCells = [];
    contributingColumns = [];
    topN = 3;
    commentarySections = [];
    
    // Clear all UI elements
    $('#summaryTable thead').empty();
    $('#summaryTable tbody').empty();
    $('#commentaryText').html('');
    $('#contributingColumnsSelect').empty();

    // Show loading state
    $('#fileDetails').html('<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>');
    $('#analysisCard').hide();

    // Fetch file details and analysis with cache busting
    $.ajax({
        url: '/api/file_details',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ 
            filename,
            timestamp: new Date().getTime() // Add timestamp to prevent caching
        }),
        success: function(data) {
            console.log("File details received:", data);
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Reload the page after selecting a file
            location.reload();
        },
        error: function(xhr, status, error) {
            console.error('Error fetching file details:', {xhr, status, error});
            const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : error;
            $('#fileDetails').html(`
                <div class="alert alert-danger">
                    Error loading file details: ${errorMsg}
                </div>
            `);
        }
    });
}