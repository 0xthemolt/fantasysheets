// Pagination state
let currentPage = 1;
const defaultItemsPerPage = 50;
let itemsPerPage = defaultItemsPerPage;

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize pagination controls
    const prevPageBtn = document.getElementById('prevPage');
    const nextPageBtn = document.getElementById('nextPage');
    const itemsPerPageSelect = document.getElementById('itemsPerPage');
    
    if (!prevPageBtn || !nextPageBtn || !itemsPerPageSelect) {
        console.error('Pagination controls not found');
        return;
    }

    // Set initial items per page
    itemsPerPageSelect.value = defaultItemsPerPage;

    // Add event listeners
    prevPageBtn.addEventListener('click', () => changePage(-1));
    nextPageBtn.addEventListener('click', () => changePage(1));
    itemsPerPageSelect.addEventListener('change', function() {
        itemsPerPage = parseInt(this.value);
        currentPage = 1; // Reset to first page
        updatePagination();
    });

    // Initial pagination setup
    updatePagination();
});

let isFiltered = false; // Track if the table is filtered

function updatePagination() {
    const table = document.getElementById('playersTable');
    if (!table) {
        console.error('Players table not found');
        return;
    }

    const rows = Array.from(table.getElementsByTagName('tr')).slice(1); // Skip header
    const totalItems = rows.filter(row => !row.classList.contains('details-row')).length;
    const totalPages = Math.ceil(totalItems / itemsPerPage);

    // Update pagination buttons
    const pageNumbers = document.getElementById('pageNumbers');
    pageNumbers.innerHTML = '';

    function addPageButton(pageNum, text = pageNum) {
        const button = document.createElement('button');
        button.className = 'page-link' + (pageNum === currentPage ? ' active' : '');
        button.textContent = text;
        if (typeof pageNum === 'number') {
            button.onclick = () => {
                currentPage = pageNum;
                updatePagination();
            };
        } else {
            button.disabled = true;
            button.className += ' ellipsis';
        }
        pageNumbers.appendChild(button);
    }

    // Logic for showing page numbers with ellipsis
    if (totalPages <= 7) {
        // Show all pages if 7 or fewer
        for (let i = 1; i <= totalPages; i++) {
            addPageButton(i);
        }
    } else {
        // Always show first page
        addPageButton(1);

        if (currentPage <= 3) {
            // Near start
            for (let i = 2; i <= 5; i++) addPageButton(i);
            addPageButton('...', '...');
            addPageButton(totalPages);
        } else if (currentPage >= totalPages - 2) {
            // Near end
            addPageButton('...', '...');
            for (let i = totalPages - 4; i <= totalPages; i++) addPageButton(i);
        } else {
            // Middle
            addPageButton('...', '...');
            for (let i = currentPage - 1; i <= currentPage + 1; i++) addPageButton(i);
            addPageButton('...', '...');
            addPageButton(totalPages);
        }
    }

    // Update prev/next buttons state
    document.getElementById('prevPage').disabled = currentPage === 1;
    document.getElementById('nextPage').disabled = currentPage === totalPages;

    // Show/hide rows based on current page
    let visibleCount = 0;
    let currentRow = 0;

    rows.forEach(row => {
        if (row.classList.contains('details-row')) {
            // Always match detail row visibility to its parent row
            const parentVisible = row.previousElementSibling.style.display !== 'none';
            row.style.display = parentVisible ? '' : 'none';
        } else {
            currentRow++;
            const shouldBeVisible = currentRow > (currentPage - 1) * itemsPerPage && 
                                  currentRow <= currentPage * itemsPerPage;
            row.style.display = shouldBeVisible ? '' : 'none';
            if (shouldBeVisible) visibleCount++;
        }
    });
}

function changePage(delta) {
    const table = document.getElementById('playersTable');
    if (!table) return;

    const rows = Array.from(table.getElementsByTagName('tr')).slice(1);
    const totalItems = rows.filter(row => !row.classList.contains('details-row')).length;
    const totalPages = Math.ceil(totalItems / itemsPerPage);

    const newPage = currentPage + delta;
    if (newPage >= 1 && newPage <= totalPages) {
        currentPage = newPage;
        updatePagination();
    }
}

// Export functions that might need to be called from the main file
window.updatePagination = updatePagination;
window.changePage = changePage;