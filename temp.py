function setupEventListeners() {
    // File selection change
    $('#fileSelect').on('change', function(event) {
        // Get the current selected file
        const selectedFile = $(this).val();
        
        // Check if this is the initial page load
        if (!sessionStorage.getItem('initialFileLoaded')) {
            // First time loading a file, proceed normally
            sessionStorage.setItem('initialFileLoaded', 'true');
            handleFileSelection();
            return;
        }

        // Check if this file has already been confirmed in this session
        const confirmedFiles = JSON.parse(sessionStorage.getItem('confirmedFiles') || '[]');
        
        // If file has already been confirmed, proceed with selection
        if (confirmedFiles.includes(selectedFile)) {
            handleFileSelection();
            return;
        }

        // Prevent default selection
        event.preventDefault();
        
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
            // Add this file to confirmed files list
            const confirmedFiles = JSON.parse(sessionStorage.getItem('confirmedFiles') || '[]');
            if (!confirmedFiles.includes(selectedFile)) {
                confirmedFiles.push(selectedFile);
                sessionStorage.setItem('confirmedFiles', JSON.stringify(confirmedFiles));
            }

            // Set the file select to the chosen file
            $('#fileSelect').val(selectedFile);

            // Close the modal
            modal.hide();

            // Trigger file selection
            handleFileSelection();
        });
    });

    // Rest of the existing event listeners remain the same
    // (Copy the rest of the event listeners from the previous implementation)
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