function setupEventListeners() {
    // Modify the file selection change event
    $('#fileSelect').on('change', function(event) {
        // Check if this is the initial page load or first file selection
        if (!sessionStorage.getItem('initialFileLoaded')) {
            // First time loading a file, just proceed normally
            sessionStorage.setItem('initialFileLoaded', 'true');
            handleFileSelection();
            return;
        }

        // Capture the current selected file
        const selectedFile = $(this).val();

        // Create confirmation modal dynamically
        const confirmModal = `
            <div class="modal fade" id="fileChangeConfirmModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Confirm File Change</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            Changing the file will reset all current selections and analysis. Do you want to proceed?
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="confirmFileChangeBtn">Confirm</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove any existing modal first
        $('#fileChangeConfirmModal').remove();
        $('body').append(confirmModal);

        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('fileChangeConfirmModal'));
        modal.show();

        // Handle confirmation button
        $('#confirmFileChangeBtn').on('click', function() {
            // Store the selected file in sessionStorage for persistence
            sessionStorage.setItem('selectedFileOnReload', selectedFile);
            
            // Reload the page
            location.reload();
        });

        // Prevent default file selection and reset dropdown
        event.preventDefault();
        $(this).val('');
    });

    // Rest of the existing event listeners remain the same
    // Update commentary button
    $('#updateCommentaryBtn').on('click', handleManualCommentaryUpdate);
    
    // Save settings button
    $('#saveSettingsBtn').on('click', handleSaveSettings);
    
    // Send commentary modification
    $('#sendCommentaryBtn').on('click', handleCommentaryModification);
    $('#commentaryInput').on('keypress', function(e) {
        if (e.key === 'Enter') {
            handleCommentaryModification();
        }
    });
    
    // Contributing columns and top N changes
    $('#contributingColumnsSelect').on('change', function() {
        contributingColumns = Array.from($(this).find('option:selected')).map(option => option.value);
    });
    
    $('#topNSelect').on('change', function() {
        topN = parseInt(this.value);
    });
    
    // Clear selection button
    $('#clearSelectionBtn').on('click', function() {
        selectedCells = [];
        highlightSelectedCells();
        showAlert('Selection cleared.', 'info');
    });
    
    // Reset selection button
    $('#resetSelectionBtn').on('click', function() {
        if (originalSelectedCells && originalSelectedCells.length > 0) {
            selectedCells = [...originalSelectedCells];
            highlightSelectedCells();
            showAlert('Selection reset to original.', 'info');
        } else {
            showAlert('No original selection to reset to.', 'warning');
        }
    });
    
    // Export to PPT button
    $('#exportPptBtn').on('click', function() {
        handleExportToPPT();
    });
}

function initApp() {
    console.log("Application initializing...");
    
    // Check for previously selected file on reload
    const selectedFileOnReload = sessionStorage.getItem('selectedFileOnReload');
    
    // Load available files
    fetchFiles();
    
    // Set up event listeners
    setupEventListeners();
    
    // Setup file selection collapse toggle icon behavior
    $('#fileSelectionBody').on('show.bs.collapse', function () {
        $('#fileSelectionToggle').removeClass('fa-chevron-down').addClass('fa-chevron-up');
    });
    
    $('#fileSelectionBody').on('hide.bs.collapse', function () {
        $('#fileSelectionToggle').removeClass('fa-chevron-up').addClass('fa-chevron-down');
    });
    
    // If a file was selected before reload, automatically select it
    if (selectedFileOnReload) {
        // Remove the stored file to prevent future automatic selections
        sessionStorage.removeItem('selectedFileOnReload');
        
        // Set the dropdown to the previously selected file
        $('#fileSelect').val(selectedFileOnReload);
        
        // Trigger file selection
        handleFileSelection();
    }
}