function setupEventListeners() {
    // File selection change
    $('#fileSelect').on('change', function(event) {
        // Check if this is the first file selection ever
        if (!sessionStorage.getItem('firstFileSelectionDone')) {
            // First time file selection - just proceed normally
            sessionStorage.setItem('firstFileSelectionDone', 'true');
            handleFileSelection();
            return;
        }

        // This is a subsequent file selection - show confirmation modal
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

        // Temporarily store the selected file
        sessionStorage.setItem('pendingFileSelection', selectedFile);

        // Reset the dropdown
        $(this).val('');

        // Handle confirmation button
        $('#confirmFileChangeBtn').on('click', function() {
            // Retrieve the pending file selection
            const fileToLoad = sessionStorage.getItem('pendingFileSelection');
            
            // Set the file select to the chosen file
            $('#fileSelect').val(fileToLoad);

            // Close the modal
            modal.hide();

            // Remove pending file storage
            sessionStorage.removeItem('pendingFileSelection');

            // Trigger file selection
            handleFileSelection();
        });

        // Prevent default selection
        event.preventDefault();
    });

    // Rest of the existing event listeners remain the same
    // (Copy all other event listeners from the original implementation)
    $('#updateCommentaryBtn').on('click', handleManualCommentaryUpdate);
    $('#saveSettingsBtn').on('click', handleSaveSettings);
    $('#sendCommentaryBtn').on('click', handleCommentaryModification);
    $('#commentaryInput').on('keypress', function(e) {
        if (e.key === 'Enter') {
            handleCommentaryModification();
        }
    });
    $('#contributingColumnsSelect').on('change', function() {
        contributingColumns = Array.from($(this).find('option:selected')).map(option => option.value);
    });
    $('#topNSelect').on('change', function() {
        topN = parseInt(this.value);
    });
    $('#clearSelectionBtn').on('click', function() {
        selectedCells = [];
        highlightSelectedCells();
        showAlert('Selection cleared.', 'info');
    });
    $('#resetSelectionBtn').on('click', function() {
        if (originalSelectedCells && originalSelectedCells.length > 0) {
            selectedCells = [...originalSelectedCells];
            highlightSelectedCells();
            showAlert('Selection reset to original.', 'info');
        } else {
            showAlert('No original selection to reset to.', 'warning');
        }
    });
    $('#exportPptBtn').on('click', function() {
        handleExportToPPT();
    });
}

function initApp() {
    console.log("Application initializing...");
    
    // Clear confirmed files at the start of a new session
    sessionStorage.removeItem('confirmedFiles');
    
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
}