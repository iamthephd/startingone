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
    
    function initApp() {
        console.log("Application initializing...");
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
    
    function fetchFiles() {
        fetch('/api/files')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(files => {
                console.log("Files fetched successfully:", files);
                populateFileSelect(files);
            })
            .catch(error => {
                console.error('Error fetching files:', error);
                showAlert('Error loading files. Please try again later.', 'danger');
            });
    }
    
    function populateFileSelect(files) {
        const fileSelect = document.getElementById('fileSelect');
        fileSelect.innerHTML = '<option value="" selected disabled>Choose a file...</option>';
        
        files.forEach(file => {
            const option = document.createElement('option');
            option.value = file;
            option.textContent = file;
            fileSelect.appendChild(option);
        });
    }
    
    function setupEventListeners() {
        // File selection change
        $('#fileSelect').on('change', handleFileSelection);
        
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
    
    function handleSaveSettings() {
        // Show loading state
        const button = $('#saveSettingsBtn');
        const originalText = button.text();
        button.html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...');
        button.prop('disabled', true);
        
        // Prepare data for the API call
        const data = {
            contributing_columns: contributingColumns,
            top_n: topN,
            timestamp: new Date().getTime() // Add timestamp to prevent caching
        };
        
        // Call the API to save settings
        $.ajax({
            url: '/api/save_settings',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(response) {
                // Show success message
                showAlert(response.message || 'Settings saved successfully', 'success');
                
                // Close the accordion
                $('#settingsCollapse').collapse('hide');
            },
            complete: function() {
                // Reset button state
                button.html(originalText);
                button.prop('disabled', false);
            }
        });
    }
    
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
    
    function displayFileDetails(details) {
        console.log("Displaying file details:", details);
        
        if (!details) {
            $('#fileDetails').html('<div class="alert alert-warning">No file details available</div>');
            return;
        }
        
        let detailsHtml = `
            <div class="d-flex flex-wrap align-items-center justify-content-between w-100">
                <div class="badge bg-primary p-2 flex-grow-1 mx-1">
                    <div class="text-small">Total Rows</div>
                    <div class="fs-5">${details.rows || 'N/A'}</div>
                </div>
                <div class="badge bg-secondary p-2 flex-grow-1 mx-1">
                    <div class="text-small">Total Columns</div>
                    <div class="fs-5">${details.columns || 'N/A'}</div>
                </div>
                <div class="badge bg-success p-2 flex-grow-1 mx-1">
                    <div class="text-small">Average Amount</div>
                    <div class="fs-5">${details.avg_amount !== undefined ? details.avg_amount.toFixed(2) : 'N/A'}</div>
                </div>
                <div class="badge bg-info p-2 flex-grow-1 mx-1">
                    <div class="text-small">Min Amount</div>
                    <div class="fs-5">${details.min_amount !== undefined ? details.min_amount.toFixed(2) : 'N/A'}</div>
                </div>
                <div class="badge bg-warning p-2 flex-grow-1 mx-1">
                    <div class="text-small">Max Amount</div>
                    <div class="fs-5">${details.max_amount !== undefined ? details.max_amount.toFixed(2) : 'N/A'}</div>
                </div>
            </div>
        `;
        
        $('#fileDetails').html(detailsHtml);
    }
    
    function displaySummaryTable(tableData) {
        console.log("Displaying summary table:", tableData);
        
        if (!tableData || !tableData.data || !tableData.columns || tableData.data.length === 0) {
            $('#summaryTable').html('<div class="alert alert-warning">No table data available</div>');
            return;
        }
        
        // Destroy DataTable if it exists
        if ($.fn.DataTable.isDataTable('#summaryTable')) {
            $('#summaryTable').DataTable().destroy();
        }
        
        // Clear HTML completely before setting new content
        $('#summaryTable thead').empty();
        $('#summaryTable tbody').empty();
        
        // Create table headers
        let headerHtml = '<tr><th></th>';
        tableData.columns.slice(1).forEach(column => {
            headerHtml += `<th>${column}</th>`;
        });
        headerHtml += '</tr>';
        
        // Create table body
        let bodyHtml = '';
        tableData.data.forEach(row => {
            bodyHtml += `<tr><td class="fw-bold">${row[tableData.columns[0]]}</td>`;
            tableData.columns.slice(1).forEach(column => {
                // Make sure we're handling undefined/null values
                const value = row[column] !== undefined && row[column] !== null ? row[column] : '';
                bodyHtml += `<td data-row="${row[tableData.columns[0]]}" data-col="${column}" data-value="${value}">${value}</td>`;
            });
            bodyHtml += '</tr>';
        });
        
        // Set table HTML
        $('#summaryTable thead').html(headerHtml);
        $('#summaryTable tbody').html(bodyHtml);
        
        // Initialize DataTable with a slight delay to ensure DOM is updated
        setTimeout(() => {
            $('#summaryTable').DataTable({
                paging: false,
                searching: false,
                info: false,
                ordering: false,
                destroy: true // Ensure it can be reinitialized
            });
            
            // Add click event listeners to cells
            $('#summaryTable tbody td:not(:first-child)').on('click', toggleCellSelection);
        }, 100);
    }
    
    function toggleCellSelection(event) {
        const $cell = $(event.target);
        const row = $cell.data('row');
        const col = $cell.data('col');
        const value = parseFloat($cell.data('value'));
        
        if (isNaN(row) || isNaN(value) || !col) {
            console.warn('Invalid cell data:', {row, col, value});
            return;
        }
        
        // Check if cell is already selected
        const cellIndex = selectedCells.findIndex(c => 
            c[0] === row && c[1] === col && c[2] === value
        );
        
        if (cellIndex === -1) {
            // Add to selected cells
            selectedCells.push([row, col, value]);
            $cell.addClass('selected-cell');
        } else {
            // Remove from selected cells
            selectedCells.splice(cellIndex, 1);
            $cell.removeClass('selected-cell');
        }
        
        console.log('Selected cells:', selectedCells);
    }
    
    function highlightSelectedCells() {
        console.log('Highlighting selected cells:', selectedCells);
        
        // Remove all selections first
        $('#summaryTable tbody td:not(:first-child)').removeClass('selected-cell');
        
        // Add selection to the cells in selectedCells
        if (Array.isArray(selectedCells)) {
            selectedCells.forEach(cellInfo => {
                if (Array.isArray(cellInfo) && cellInfo.length >= 2) {
                    const [row, col] = cellInfo;
                    const $cell = $(`#summaryTable tbody td[data-row="${row}"][data-col="${col}"]`);
                    if ($cell.length > 0) {
                        $cell.addClass('selected-cell');
                    } else {
                        console.warn(`Cell not found in DOM: row=${row}, col=${col}`);
                    }
                }
            });
        }
    }
    
    function populateContributingColumns(columns) {
        console.log('Populating contributing columns:', columns);
        
        const $select = $('#contributingColumnsSelect');
        $select.empty();
        
        if (!columns || columns.length <= 1) {
            console.warn('No columns to populate');
            return;
        }
        
        // Skip the first column (row names)
        columns.slice(1).forEach(column => {
            const option = $('<option>', {
                value: column,
                text: column,
                selected: contributingColumns.includes(column)
            });
            
            $select.append(option);
        });
    }
    
    function displayCommentary(commentary) {
        console.log('Displaying commentary');
        
        // First, clear commentarySections array
        commentarySections = [];
        
        // If no commentary, just display empty
        if (!commentary || commentary.trim() === '') {
            $('#commentaryText').html('<em class="text-muted">No commentary available.</em>');
            return;
        }
        
        // Parse commentary to identify cell references and add span elements
        let formattedCommentary = commentary;
        
        // Process each selected cell and mark it in the commentary text
        if (Array.isArray(selectedCells)) {
            selectedCells.forEach((cell, idx) => {
                if (!Array.isArray(cell) || cell.length < 3) return;
                
                const [row, col, value] = cell;
                
                // Create a unique ID for this cell reference
                const spanId = `cell-ref-${idx}`;
                
                // Look for "Cell [row], [col]" pattern in text
                let cellRefPattern = new RegExp(`(Cell\\s+${row}\\s*,\\s*${col})`, 'gi');
                
                // Also look for exact matches of the cell reference without "Cell" prefix
                let simpleCellRefPattern = new RegExp(`\\b(${row}\\s*,\\s*${col})\\b`, 'g');
                
                // Replace all instances with highlighted spans
                formattedCommentary = formattedCommentary.replace(cellRefPattern, 
                    `<span id="${spanId}" class="cell-reference" data-row="${row}" data-col="${col}">$1</span>`);
                    
                // Replace simple cell references too
                formattedCommentary = formattedCommentary.replace(simpleCellRefPattern, 
                    `<span id="${spanId}-simple" class="cell-reference" data-row="${row}" data-col="${col}">$1</span>`);
                
                // Store the mapping for hover behaviors
                commentarySections.push({
                    id: spanId,
                    row: row,
                    col: col,
                    value: value
                });
            });
        }
        
        // Set the formatted commentary
        $('#commentaryText').html(formattedCommentary);
        
        // Add event listeners for hover effects
        setupHoverHighlighting();
    }
    
    function setupHoverHighlighting() {
        // Remove any existing event listeners first
        $('.cell-reference').off('mouseenter mouseleave');
        $('#summaryTable tbody td').off('mouseenter mouseleave');
        
        // Add event listeners to commentary spans
        $('.cell-reference').on({
            mouseenter: function() {
                const spanId = $(this).attr('id');
                if (!spanId) return;
                
                const section = commentarySections.find(s => s && s.id === spanId);
                
                if (section) {
                    // Highlight corresponding cell in table
                    $(`#summaryTable tbody td[data-row="${section.row}"][data-col="${section.col}"]`)
                        .addClass('hover-highlight');
                } else {
                    // Check if this is a simple cell reference (with -simple suffix)
                    const baseId = spanId.replace('-simple', '');
                    const baseSection = commentarySections.find(s => s && s.id === baseId);
                    
                    if (baseSection) {
                        // Highlight corresponding cell in table
                        $(`#summaryTable tbody td[data-row="${baseSection.row}"][data-col="${baseSection.col}"]`)
                            .addClass('hover-highlight');
                    }
                }
                
                // Highlight the span itself
                $(this).addClass('hover-highlight');
            },
            mouseleave: function() {
                // Remove all hover highlights
                $('#summaryTable tbody td').removeClass('hover-highlight');
                $('.cell-reference').removeClass('hover-highlight');
            }
        });
        
        // Add event listeners to table cells
        $('#summaryTable tbody td').on({
            mouseenter: function() {
                const row = $(this).data('row');
                const col = $(this).data('col');
                
                if (row && col) {
                    // Find sections that reference this cell
                    const relatedSections = commentarySections.filter(
                        s => s && s.row.toString() === row.toString() && s.col.toString() === col.toString()
                    );
                    
                    // Highlight the cell
                    $(this).addClass('hover-highlight');
                    
                    // Highlight relevant commentary spans
                    relatedSections.forEach(section => {
                        $(`#${section.id}`).addClass('hover-highlight');
                        // Also highlight any simple references to this cell
                        $(`#${section.id}-simple`).addClass('hover-highlight');
                    });
                }
            },
            mouseleave: function() {
                // Remove all hover highlights
                $('#summaryTable tbody td').removeClass('hover-highlight');
                $('.cell-reference').removeClass('hover-highlight');
            }
        });
    }
    
    function handleManualCommentaryUpdate() {
        console.log('Updating commentary manually');
        
        // Show loading state
        const $button = $('#updateCommentaryBtn');
        const originalText = $button.text();
        $button.html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Updating...');
        $button.prop('disabled', true);
        
        // Prepare data for the API call
        const data = {
            selected_cells: selectedCells,
            contributing_columns: contributingColumns,
            top_n: topN,
            timestamp: new Date().getTime() // Add timestamp to prevent caching
        };
        
        // Call the API to update commentary
        $.ajax({
            url: '/api/update_commentary',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(data) {
                if (data.error) {
                    throw new Error(data.error);
                }
                console.log("update commentary")
                // Display updated commentary
                displayCommentary(data.commentary);
                
                // Show success message
                showAlert('Commentary updated successfully.', 'success');
            },
            complete: function() {
                // Reset button state
                $button.html(originalText);
                $button.prop('disabled', false);
            }
        });
    }
    
    function handleCommentaryModification() {
        const $input = $('#commentaryInput');
        const query = $input.val().trim();
        
        if (!query) return;
        
        console.log('Modifying commentary with query:', query);
        
        // Show loading state
        $input.prop('disabled', true);
        const $button = $('#sendCommentaryBtn');
        $button.prop('disabled', true);
        $button.html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>');
        
        // Call the API to modify commentary
        $.ajax({
            url: '/api/modify_commentary',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ 
                query,
                timestamp: new Date().getTime() // Add timestamp to prevent caching
            }),
            success: function(data) {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Display updated commentary
                displayCommentary(data.commentary);
                
                // Clear input
                $input.val('');
                
                // Show success message
                showAlert('Commentary modified successfully.', 'success');
            },
            complete: function() {
                // Reset input and button state
                $input.prop('disabled', false);
                $input.focus();
                $button.prop('disabled', false);
                $button.html('<i class="fas fa-arrow-right"></i>');
            }
        });
    }
    
    function showAlert(message, type = 'info') {
        // Create alert element
        const $alertDiv = $('<div>', {
            class: `alert alert-${type} alert-dismissible fade show position-fixed bottom-0 end-0 m-3`,
            style: 'z-index: 1050;',
            html: `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `
        });
        
        // Add to body
        $('body').append($alertDiv);
        
        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert($alertDiv[0]);
            bsAlert.close();
        }, 3000);
    }
    
    function handleExportToPPT() {
        // Show loading state
        const $button = $('#exportPptBtn');
        const originalText = $button.html();
        $button.html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Exporting...');
        $button.prop('disabled', true);
        
        // Get current file name, table data, and commentary
        const filename = $('#fileSelect').val();
        const commentary = $('#commentaryText').text();
        
        if (!filename) {
            showAlert('Please select a file first.', 'warning');
            $button.html(originalText);
            $button.prop('disabled', false);
            return;
        }
        
        console.log('Exporting to PPT:', filename);
        
        // Create a virtual canvas to capture the table as an image
        const tableHtml = $('#summaryTable').parent().html();
        
        // Create a blob with PowerPoint XML content
        const pptxContent = generatePPTXContent(filename, tableHtml, commentary);
        
        // Create download link
        const blob = new Blob([pptxContent], { type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filename.replace(/\.[^/.]+$/, '')}_analysis.pptx`;
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            $button.html(originalText);
            $button.prop('disabled', false);
            showAlert('PowerPoint file exported successfully!', 'success');
        }, 1000);
    }
});