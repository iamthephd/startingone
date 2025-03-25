// New function to encapsulate the original file-loading logic
function loadFileDetails(filename) {
    console.log(`Loading file: ${filename}`);
    
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
            
            // Call your display functions here using the received data
            displayFileDetails(data.details);
            displaySummaryTable(data.table);
            // Set and highlight cells, populate contributing columns, display commentary, etc.
            
            // For example:
            selectedCells = Array.isArray(data.selected_cells) ? [...data.selected_cells] : [];
            originalSelectedCells = Array.isArray(data.selected_cells) ? [...data.selected_cells] : [];
            setTimeout(() => {
                highlightSelectedCells();
            }, 200);
            contributingColumns = Array.isArray(data.contributing_columns) ? [...data.contributing_columns] : [];
            populateContributingColumns(data.table.columns);
            topN = data.top_n || 3;
            $('#topNSelect').val(topN);
            displayCommentary(data.commentary);
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

// Updated handleFileSelection with confirmation and reload logic
function handleFileSelection() {
    const filename = $('#fileSelect').val();
    if (!filename) return;

    // If this flag is set, it means we're coming back from a reload—don't show the confirmation again.
    if (sessionStorage.getItem('reloading') === 'true') {
        sessionStorage.removeItem('reloading');
        loadFileDetails(filename); // Directly load file details without confirmation.
        return;
    }
    
    // Show confirmation popup
    if (confirm(`Are you sure you want to load the file: ${filename}? This will reload the page.`)) {
        // Save the file name so that after reload we know which file to load
        sessionStorage.setItem('selectedFile', filename);
        // Set a flag to prevent re-triggering the confirmation on reload
        sessionStorage.setItem('reloading', 'true');
        location.reload();
    } else {
        // Reset the selection if the user cancels
        $('#fileSelect').val('');
    }
}

// On page load, check if a file was saved from a confirmed selection and load it automatically.
$(document).ready(function() {
    // Existing initialization logic
    initApp();
    
    // Check if a file was previously selected and stored in sessionStorage
    const savedFile = sessionStorage.getItem('selectedFile');
    if (savedFile) {
        // Remove the stored file since we are now processing it
        sessionStorage.removeItem('selectedFile');
        loadFileDetails(savedFile);
    }
    
    // Set up event listener for file selection
    $('#fileSelect').on('change', handleFileSelection);
});
