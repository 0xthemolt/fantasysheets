// Make the function globally available
window.initializePagination = function({ tableId, itemsPerPageId, prevPageId, nextPageId, pageNumbersId }) {
    let currentPage = 1;
    const table = document.getElementById(tableId);
    const itemsPerPageSelect = document.getElementById(itemsPerPageId);
    const prevPageButton = document.getElementById(prevPageId);
    const nextPageButton = document.getElementById(nextPageId);
    const pageNumbersDiv = document.getElementById(pageNumbersId);

    // Function to get visible rows (respecting filters)
    function getVisibleRows() {
        return Array.from(table.querySelectorAll('tr:not(:first-child)'))
            .filter(row => row.getAttribute('data-filter-visible') !== 'false');
    }

    // Function to update pagination
    window.updatePagination = function() {
        const itemsPerPage = parseInt(itemsPerPageSelect.value);
        const visibleRows = getVisibleRows();
        const totalPages = Math.ceil(visibleRows.length / itemsPerPage);

        // Hide all rows first
        visibleRows.forEach(row => row.style.display = 'none');

        // Show rows for current page
        const start = (currentPage - 1) * itemsPerPage;
        const end = start + itemsPerPage;
        visibleRows.slice(start, end).forEach(row => row.style.display = '');

        // Update pagination controls
        prevPageButton.disabled = currentPage === 1;
        nextPageButton.disabled = currentPage === totalPages;

        // Update page numbers
        updatePageNumbers(totalPages);
    };

    // Function to reset to first page
    window.resetToFirstPage = function() {
        currentPage = 1;
        updatePagination();
    };

    // Function to update page numbers display
    function updatePageNumbers(totalPages) {
        pageNumbersDiv.innerHTML = '';
        for (let i = 1; i <= totalPages; i++) {
            const pageButton = document.createElement('button');
            pageButton.textContent = i;
            pageButton.classList.add('page-number');
            if (i === currentPage) {
                pageButton.classList.add('active');
            }
            pageButton.addEventListener('click', () => {
                currentPage = i;
                updatePagination();
            });
            pageNumbersDiv.appendChild(pageButton);
        }
    }

    // Event listeners
    itemsPerPageSelect.addEventListener('change', resetToFirstPage);
    prevPageButton.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            updatePagination();
        }
    });
    nextPageButton.addEventListener('click', () => {
        const visibleRows = getVisibleRows();
        const totalPages = Math.ceil(visibleRows.length / parseInt(itemsPerPageSelect.value));
        if (currentPage < totalPages) {
            currentPage++;
            updatePagination();
        }
    });

    // Initial pagination
    updatePagination();
};