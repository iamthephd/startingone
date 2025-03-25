function setupEventListeners() {
    // File selection change
    $('#fileSelect').on('change', function(event) {
        // Check if this is the first file selection
        if (!sessionStorage.getItem('firstFileSelectionDone')) {
            // First time file selection - just proceed normally
            sessionStorage.setItem('firstFileSelectionDone', 'true');
            handleFileSelection();
            return;
        }

        // This is a subsequent file selection - show confirmation for page reload
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
                            Changing the file will reload the page and reset all current selections. Do you want to proceed?
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

        // Store the selected file for reload
        sessionStorage.setItem('selectedFileOnReload', selectedFile);

        // Handle confirmation button
        $('#confirmFileChangeBtn').on('click', function() {
            // Reload the page
            location.reload();
        });

        // Prevent default selection
        event.preventDefault();
        $(this).val('');
    });

    // Rest of the existing event listeners remain the same
    // (Copy all other event listeners from the original implementation)
    // ... (keep all other event listeners)
}

function initApp() {
    console.log("Application initializing...");
    
    // Check for previously selected file on reload
    const selectedFileOnReload = sessionStorage.getItem('selectedFileOnReload');
    
    // Load available files
    fetchFiles();
    
    // Set up event listeners
    setupEventListeners();
    
    // If a file was selected before reload, automatically select it
    if (selectedFileOnReload) {
        // Remove the stored file to prevent future automatic selections
        sessionStorage.removeItem('selectedFileOnReload');
        
        // Set the dropdown to the previously selected file
        $('#fileSelect').val(selectedFileOnReload);
        
        // Trigger file selection
        handleFileSelection();
    }
    
    // Setup file selection collapse toggle icon behavior
    $('#fileSelectionBody').on('show.bs.collapse', function () {
        $('#fileSelectionToggle').removeClass('fa-chevron-down').addClass('fa-chevron-up');
    });
    
    $('#fileSelectionBody').on('hide.bs.collapse', function () {
        $('#fileSelectionToggle').removeClass('fa-chevron-up').addClass('fa-chevron-down');
    });
}