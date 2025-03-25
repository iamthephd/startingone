function toggleCellSelection(event) {
    const $cell = $(event.target).closest('td');
    const rowName = $cell.data('row');
    const columnName = $cell.data('col');
    
    // Create a unique identifier for the cell
    const cellKey = `${rowName}:${columnName}`;
    
    // Check if the cell is already selected
    const cellIndex = selectedCells.findIndex(cell => 
        cell.row === rowName && cell.column === columnName
    );
    
    if (cellIndex > -1) {
        // Cell is already selected, so deselect it
        selectedCells.splice(cellIndex, 1);
        $cell.removeClass('table-active');
    } else {
        // Select the cell
        selectedCells.push({
            row: rowName,
            column: columnName,
            value: $cell.data('value')
        });
        $cell.addClass('table-active');
    }
    
    console.log('Current Selected Cells:', selectedCells);
}

function highlightSelectedCells() {
    // Clear existing highlights
    $('#summaryTable tbody td').removeClass('table-active');
    
    // Highlight selected cells
    selectedCells.forEach(cell => {
        $(`#summaryTable tbody td[data-row="${cell.row}"][data-col="${cell.column}"]`)
            .addClass('table-active');
    });
}

function handleFileSelection() {
    const filename = $('#fileSelect').val();
    if (!filename) return;
    
    // Option 1: Refresh the entire page
    if (confirm('Selecting a new file will reset the current analysis. Do you want to continue?')) {
        location.reload();
        return;
    }
    
    // Option 2: If you don't want a full page reload, use the existing logic
    // ... (rest of your existing handleFileSelection code)
}

// Add CSS for selected cells
const styleTag = document.createElement('style');
styleTag.innerHTML = `
    #summaryTable .table-active {
        background-color: var(--highlight-color) !important;
        color: white !important;
    }
`;
document.head.appendChild(styleTag);

// Clear selection buttons
$('#clearSelectionBtn').on('click', function() {
    selectedCells = [];
    $('#summaryTable tbody td').removeClass('table-active');
});

$('#resetSelectionBtn').on('click', function() {
    // Revert to original selected cells
    selectedCells = [...originalSelectedCells];
    highlightSelectedCells();
});