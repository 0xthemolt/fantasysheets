// Pagination state
let currentPage = 1;
const defaultItemsPerPage = 50;
let itemsPerPage = defaultItemsPerPage;
let filteredRows = [];
let isFiltered = false;

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
        applyFiltersAndPagination();
    });

    // Initial pagination setup
    applyFiltersAndPagination();
});

function applyFiltersAndPagination() {
    const table = document.getElementById('playersTable');
    if (!table) {
        console.error('Players table not found');
        return;
    }

    const rows = Array.from(table.getElementsByTagName('tr')).slice(1); // Skip header
    const searchText = document.getElementById('player_handle')?.value?.toLowerCase() || '';
    
    // Get all filter dropdowns
    const filterGroups = document.querySelectorAll('.filter-dropdown');
    const activeFilters = {};
    
    // Collect active filters
    filterGroups.forEach(group => {
        const filterName = group.querySelector('.filter-label').textContent.toLowerCase();
        const checkedFilters = Array.from(group.querySelectorAll('input:checked'))
            .map(input => input.value);
        if (checkedFilters.length > 0) {
            activeFilters[filterName] = checkedFilters;
        }
    });
    
    // Filter rows
    filteredRows = rows.filter(row => {
        if (row.classList.contains('details-row')) return false;
        
        const playerCell = row.querySelector('.player-link');
        if (!playerCell) return false;
        
        const playerHandle = playerCell.textContent.toLowerCase();
        let showRow = playerHandle.includes(searchText);
        
        // Apply active filters
        if (Object.keys(activeFilters).length > 0) {
            for (const [filterName, filters] of Object.entries(activeFilters)) {
                const attributeName = `data-${filterName.replace(/\s+/g, '-')}`;
                const rowValue = row.getAttribute(attributeName);
                if (rowValue) {
                    showRow = showRow && filters.includes(rowValue);
                }
            }
        }
        
        return showRow;
    });

    isFiltered = Object.keys(activeFilters).length > 0 || searchText.length > 0;
    
    applyVisibility();
    updatePaginationControls();
}

function applyVisibility() {
    const table = document.getElementById('playersTable');
    const rows = Array.from(table.getElementsByTagName('tr')).slice(1);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, filteredRows.length);
    
    // Hide all rows first
    rows.forEach(row => {
        row.style.display = 'none';
        if (row.classList.contains('details-row')) {
            const parentRow = row.previousElementSibling;
            if (parentRow && parentRow.style.display !== 'none') {
                const expandButton = parentRow.querySelector('.expand-button');
                if (expandButton && expandButton.getAttribute('aria-expanded') === 'true') {
                    row.style.display = '';
                }
            }
        }
    });
    
    // Show filtered rows for current page
    filteredRows.slice(startIndex, endIndex).forEach(row => {
        row.style.display = '';
    });
}

function updatePaginationControls() {
    const pageNumbers = document.getElementById('pageNumbers');
    const prevButton = document.getElementById('prevPage');
    const nextButton = document.getElementById('nextPage');
    const totalPages = Math.ceil(filteredRows.length / itemsPerPage);
    
    pageNumbers.innerHTML = '';
    
    function addPageButton(pageNum, text = pageNum) {
        const button = document.createElement('button');
        button.className = 'page-link' + (pageNum === currentPage ? ' active' : '');
        button.textContent = text;
        if (typeof pageNum === 'number') {
            button.onclick = () => {
                currentPage = pageNum;
                applyFiltersAndPagination();
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
    
    // Update prev/next buttons
    prevButton.disabled = currentPage === 1;
    nextButton.disabled = currentPage === totalPages;
}

function changePage(delta) {
    const totalPages = Math.ceil(filteredRows.length / itemsPerPage);
    const newPage = currentPage + delta;
    
    if (newPage >= 1 && newPage <= totalPages) {
        currentPage = newPage;
        applyFiltersAndPagination();
    }
}

// Export functions that might need to be called from other files
window.applyFiltersAndPagination = applyFiltersAndPagination;
window.changePage = changePage;