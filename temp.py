{% extends 'base.html' %}

{% block content %}
<div class="row">
    <!-- File Selection Section -->
    <div class="col-12 mb-4">
        <div class="card rounded-3 shadow-sm">
            <div class="card-header d-flex justify-content-between align-items-center" style="background-color: #afd5fc !important;">
                <h5 class="mb-0">File Selection</h5>
                <button class="btn btn-sm btn-outline-dark" type="button" data-bs-toggle="collapse" 
                        data-bs-target="#fileSelectionBody" aria-expanded="true" aria-controls="fileSelectionBody">
                    <i class="fas fa-chevron-up" id="fileSelectionToggle"></i>
                </button>
            </div>
            <div class="collapse show" id="fileSelectionBody">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-lg-3">
                            <div class="form-group">
                                <label for="fileSelect" class="form-label">Select File</label>
                                <select id="fileSelect" class="form-select form-select-lg">
                                    <option value="" selected disabled>Choose a file...</option>
                                    <!-- Options will be populated by JavaScript -->
                                </select>
                            </div>
                        </div>
                        <div class="col-lg-9">
                            <div id="fileDetails" class="d-flex flex-wrap mt-3 mt-lg-0">
                                <div class="alert alert-secondary w-100">
                                    Please select a file to view details.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Analysis Section -->
    <div class="col-12">
        <div class="card mb-4 rounded-4 shadow" id="analysisCard" style="display: none;">
            <div class="card-header" style="background-color: #afd5fc !important;">
                <h5 class="mb-0">Data Analysis</h5>
            </div>
            <div class="card-body">
                <!-- Settings have been moved to under the summary table -->

                <div class="row g-4">
                    <!-- Summary Table Section -->
                    <div class="col-lg-7">
                        <div class="card rounded-4 shadow-sm h-100">
                            <div class="card-header" style="background-color: #d0e4f8 !important;">
                                <h6 class="mb-0">Summary Table</h6>
                            </div>
                            <div class="card-body">
                                <div id="tableLegend" class="mb-3 p-2 rounded-3">
                                    <i class="fas fa-info-circle me-2"></i>
                                    <span class="badge" style="background-color: var(--highlight-color) !important; color: white !important;">Selected</span> cells are used for commentary generation.
                                    Click on cells to select or deselect them.
                                </div>
                                <div class="table-container">
                                    <div class="table-responsive">
                                        <table id="summaryTable" class="table table-striped table-hover rounded table-sm">
                                            <thead>
                                                <!-- Table headers will be populated by JavaScript -->
                                            </thead>
                                            <tbody>
                                                <!-- Table body will be populated by JavaScript -->
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                                <!-- Settings and Action Buttons -->
                                <div class="mt-4">
                                    <!-- All buttons in one line, centered -->
                                    <div class="d-flex align-items-center justify-content-center gap-2 flex-wrap">
                                        <button class="btn btn-outline-primary px-3" type="button" data-bs-toggle="collapse" 
                                                data-bs-target="#settingsCollapse" aria-expanded="false" aria-controls="settingsCollapse">
                                            <i class="fas fa-cog me-1"></i>Analysis Settings
                                        </button>
                                        
                                        <button id="clearSelectionBtn" class="btn btn-outline-secondary px-3">
                                            <i class="fas fa-times me-1"></i>Clear Selection
                                        </button>
                                        <button id="resetSelectionBtn" class="btn btn-outline-primary px-3">
                                            <i class="fas fa-undo me-1"></i>Reset
                                        </button>
                                        <button id="updateCommentaryBtn" class="btn btn-primary px-3">
                                            <i class="fas fa-sync-alt me-1"></i>Update Commentary
                                        </button>
                                    </div>
                                    
                                    <!-- Analysis Settings Panel -->
                                    <div id="settingsCollapse" class="collapse mt-2 p-3 border rounded-3">
                                        <div class="row">
                                            <div class="col-md-6">
                                                <div class="form-group mb-3">
                                                    <label for="contributingColumnsSelect" class="form-label">Contributing Columns</label>
                                                    <select id="contributingColumnsSelect" class="form-select" multiple>
                                                        <!-- Options will be populated by JavaScript -->
                                                    </select>
                                                    <div class="form-text">Hold Ctrl/Cmd to select multiple</div>
                                                </div>
                                            </div>
                                            <div class="col-md-6">
                                                <div class="form-group mb-3">
                                                    <label for="topNSelect" class="form-label">Top Contributors</label>
                                                    <select id="topNSelect" class="form-select">
                                                        <option value="1">Top 1</option>
                                                        <option value="2">Top 2</option>
                                                        <option value="3" selected>Top 3</option>
                                                        <option value="4">Top 4</option>
                                                        <option value="5">Top 5</option>
                                                    </select>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="text-end">
                                            <button id="saveSettingsBtn" class="btn btn-primary">
                                                <i class="fas fa-save me-2"></i>Save Settings
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Commentary Section -->
                    <div class="col-lg-5">
                        <div class="card rounded-4 shadow-sm h-100">
                            <div class="card-header d-flex justify-content-between align-items-center" style="background-color: #d0e4f8 !important;">
                                <h6 class="mb-0">Generated Commentary</h6>
                                <button id="exportPptBtn" class="btn btn-sm btn-primary">
                                    <i class="fas fa-file-powerpoint me-1"></i>Export PPT
                                </button>
                            </div>
                            <div class="card-body d-flex flex-column">
                                <div id="commentaryText" class="p-3 rounded-3 flex-grow-1">
                                    <!-- Commentary will be populated by JavaScript -->
                                </div>
                                <div class="mt-3">
                                    <div class="input-group">
                                        <input type="text" id="commentaryInput" class="form-control" 
                                               placeholder="Type to modify commentary...">
                                        <button id="sendCommentaryBtn" class="btn btn-outline-secondary">
                                            <i class="fas fa-arrow-right"></i>
                                        </button>
                                    </div>
                                    <div class="form-text text-end">Press Enter to send</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
/* Add these styles to control table appearance */
.table-container {
    max-width: 100%;
    overflow-y: auto;
}

#summaryTable {
    width: 100%;
    font-size: 0.85rem; /* Reduced font size */
}

/* Make the first column (row names) wider and prevent text truncation */
#summaryTable th:first-child,
#summaryTable td:first-child {
    min-width: 120px; /* Adjust as needed */
    max-width: 200px; /* Adjust as needed */
    white-space: normal; /* Allow text to wrap */
    font-weight: 500; /* Make row names slightly bolder */
}

/* Make all other columns narrower */
#summaryTable th:not(:first-child),
#summaryTable td:not(:first-child) {
    max-width: 80px; /* Limit column width */
    padding: 0.4rem 0.3rem; /* Reduced padding */
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Add a tooltip effect on hover for truncated data cells */
#summaryTable td:not(:first-child):hover {
    position: relative;
}

#summaryTable td:not(:first-child):hover::after {
    content: attr(data-full-text);
    position: absolute;
    left: 0;
    top: 100%;
    z-index: 1000;
    background: #f8f9fa;
    padding: 3px 6px;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    white-space: nowrap;
    font-size: 0.8rem;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    display: none; /* Only show if JavaScript sets data-full-text attribute */
}

/* Add this script to your page to enable tooltips */
</style>

<script>
// This script should be added at the end of your page or in your existing JavaScript file
document.addEventListener("DOMContentLoaded", function() {
    // Find all data cells (not row names) and set the data-full-text attribute
    const dataCells = document.querySelectorAll("#summaryTable td:not(:first-child)");
    
    dataCells.forEach(cell => {
        // Store the full text content for tooltip display
        cell.setAttribute("data-full-text", cell.textContent);
    });
    
    // Function to resize columns based on content
    function adjustColumnWidths() {
        const headerCells = document.querySelectorAll("#summaryTable th:not(:first-child)");
        const totalColumns = headerCells.length;
        
        if (totalColumns > 0) {
            // Set a reasonable maximum width per column
            const maxColWidth = Math.floor(80 / totalColumns);
            
            headerCells.forEach(th => {
                th.style.maxWidth = maxColWidth + '%';
            });
        }
    }
    
    // Call the function when the table is loaded/updated
    // Note: You'll need to call this function after your table is populated with data
    // if you're loading data dynamically.
    setTimeout(adjustColumnWidths, 500);
});
</script>
{% endblock %}