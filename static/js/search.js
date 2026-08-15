/**
 * SGEJ — Search Utility
 * Provee filtrado client-side para tablas.
 */

function initializeTableSearch(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!input || !table) return;

    input.addEventListener('input', function () {
        const query = this.value.toLowerCase().trim();
        const rows = table.querySelectorAll('tbody tr');

        rows.forEach((row) => {
            // Excluir filas especiales si tienen clase
            if (row.querySelector('.sgej-empty-state')) return;

            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(query) ? '' : 'none';
        });
    });
}
