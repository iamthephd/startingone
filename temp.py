function displaySummaryTable(tableData) {
    console.log("Displaying summary table:", tableData);
    
    if (!tableData || !tableData.data || !tableData.columns || tableData.data.length === 0) {
        $('#summaryTable').html('<div class="alert alert-warning">No table data available</div>');
        return;
    }
    
    // Destroy existing DataTable completely
    if ($.fn.DataTable.isDataTable('#summaryTable')) {
        $('#summaryTable').DataTable().destroy(true);
    }
    
    // Clear HTML completely before setting new content
    $('#summaryTable').empty();
    
    // Recreate table structure
    let tableHtml = '<thead><tr><th></th>';
    tableData.columns.slice(1).forEach(column => {
        tableHtml += `<th>${column}</th>`;
    });
    tableHtml += '</tr></thead><tbody>';
    
    tableData.data.forEach(row => {
        tableHtml += `<tr><td class="fw-bold">${row[tableData.columns[0]]}</td>`;
        tableData.columns.slice(1).forEach(column => {
            const value = row[column] !== undefined && row[column] !== null ? row[column] : '';
            tableHtml += `<td data-row="${row[tableData.columns[0]]}" data-col="${column}" data-value="${value}">${value}</td>`;
        });
        tableHtml += '</tr>';
    });
    
    tableHtml += '</tbody>';
    
    // Set the entire table HTML at once
    $('#summaryTable').html(tableHtml);
    
    // Reinitialize DataTable with more robust options
    $('#summaryTable').DataTable({
        paging: false,
        searching: false,
        info: false,
        ordering: false,
        retrieve: true, // Important for reusing the existing table
        destroy: true
    });
    
    // Reattach cell click event listeners
    $('#summaryTable tbody td:not(:first-child)').on('click', toggleCellSelection);
}



function handleFileSelection() {
    // ... existing code ...
    
    success: function(data) {
        // ... existing code ...
        
        // Force a complete redraw of the DataTable
        if ($.fn.DataTable.isDataTable('#summaryTable')) {
            $('#summaryTable').DataTable().clear().rows.add(data.table.data).draw();
        } else {
            displaySummaryTable(data.table);
        }
        
        // ... rest of the existing code ...
    }
}