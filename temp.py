$(document).ready(function() {
    // Global variables
    let selectedCells = [];
    let originalSelectedCells = []; // Store original cells for reset
    let contributingColumns = [];
    let topN = 3;
    let commentarySections = []; // Store mapping between cells and commentary sections
    
    // Initialize the application
    initApp();
    
    // Set up global AJAX error handling
    $.ajaxSetup({
        error: function(xhr, status, error) {
            console.error('AJAX Error:', {xhr, status, error});
            
            // Display user-friendly error message
            const errorMsg = xhr.responseJSON && xhr.responseJSON.error
                ? xhr.responseJSON.error
                : 'An unexpected error occurred. Please try again.';
                
            showAlert(`Error: ${errorMsg}`, 'danger');
        }
    });

    // Check for stored file selection on page load
    const storedFile = localStorage.getItem('selectedFile');
    
    if (storedFile) {
        // Remove the stored file from localStorage
        localStorage.removeItem('selectedFile');
        
        // Set the select dropdown to the stored file
        $('#fileSelect').val(storedFile);
        
        // Trigger the file selection logic
        handleFileSelection();
    }

    // Event listener for file selection
    $('#fileSelect').on('change', function() {
        // Show confirmation dialog
        if (confirm('Selecting a new file will reset the current analysis. Do you want to continue?')) {
            // Store the selected filename in localStorage
            localStorage.setItem('selectedFile', $(this).val());
            
            // Reload the page
            location.reload();
        }
    });
});

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
            
            // Display file details
            displayFileDetails(data.details);
            
            // Display summary table
            displaySummaryTable(data.table);
            
            // Set selected cells
            selectedCells = Array.isArray(data.selected_cells) ? [...data.selected_cells] : [];
            originalSelectedCells = Array.isArray(data.selected_cells) ? [...data.selected_cells] : []; // Store original cells for reset
            
            // Highlight selected cells
            setTimeout(() => {
                highlightSelectedCells();
            }, 200);
            
            // Set contributing columns
            contributingColumns = Array.isArray(data.contributing_columns) ? [...data.contributing_columns] : [];
            populateContributingColumns(data.table.columns);
            
            // Set top N
            topN = data.top_n || 3;
            $('#topNSelect').val(topN);
            
            // Display commentary
            displayCommentary(data.commentary);
            
            // Show analysis card
            $('#analysisCard').fadeIn();
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