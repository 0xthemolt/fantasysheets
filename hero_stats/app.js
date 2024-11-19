// Client-side JavaScript to load and filter data
async function loadData() {
    const response = await fetch('hero_stats.json');
    const data = await response.json();
    
    // Generate table HTML
    const tableHtml = generateTable(data);
    document.getElementById('table-container').innerHTML = tableHtml;
}

function generateTable(data) {
    // Generate table HTML similar to your Python code
    let html = '<table class="table">';
    // ... generate table HTML ...
    return html;
}

// Load data when page loads
document.addEventListener('DOMContentLoaded', loadData);