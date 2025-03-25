function displaySummaryTable(tableData) {
    console.log("DEBUG: Full table data received:", JSON.stringify(tableData, null, 2));
    
    if (!tableData || !tableData.data || !tableData.columns || tableData.data.length === 0) {
        console.error("ERROR: Invalid table data structure");
        $('#summaryTable').html('<div class="alert alert-warning">No table data available</div>');
        return;
    }
    
    // Completely destroy existing DataTable
    if ($.fn.DataTable.isDataTable('#summaryTable')) {
        $('#summaryTable').DataTable().destroy();
    }
    
    // Clear table completely
    $('#summaryTable').empty();
    
    // Recreate table structure
    let headerHtml = '<thead><tr><th></th>';
    tableData.columns.slice(1).forEach(column => {
        headerHtml += `<th>${column}</th>`;
    });
    headerHtml += '</tr></thead><tbody>';
    
    tableData.data.forEach(row => {
        headerHtml += `<tr><td class="fw-bold">${row[tableData.columns[0]]}</td>`;
        tableData.columns.slice(1).forEach(column => {
            const value = row[column] !== undefined && row[column] !== null ? row[column] : '';
            console.log(`DEBUG: Cell value for ${column}: ${value}`);
            headerHtml += `<td data-row="${row[tableData.columns[0]]}" data-col="${column}" data-value="${value}">${value}</td>`;
        });
        headerHtml += '</tr>';
    });
    
    headerHtml += '</tbody>';
    
    // Set the entire table HTML at once
    $('#summaryTable').html(headerHtml);
    
    // Reinitialize DataTable with force redraw
    const dataTable = $('#summaryTable').DataTable({
        paging: false,
        searching: false,
        info: false,
        ordering: false,
        retrieve: true,
        destroy: true
    });
    
    // Force a redraw
    dataTable.draw();
    
    // Reattach cell click event listeners
    $('#summaryTable tbody td:not(:first-child)').on('click', toggleCellSelection);
    
    console.log("DEBUG: Table rendering complete");
}