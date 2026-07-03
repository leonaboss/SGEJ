/**
 * SGEJ — Dashboard Reactive Logic
 * Responsabilidad: Polling de conteos, animación count-up, búsqueda en tablas.
 * Lógica pura — no conoce el DOM styling (SoC).
 */

const SgejDashboard = (() => {
  'use strict';

  const COUNTS_API_URL = '/api/dashboard/counts/';
  const POLLING_INTERVAL_MS = 30000;

  const CARD_IDS = {
    despido: 'count-despido',
    inspectoria: 'count-inspectoria',
    oficina: 'count-oficina',
    convenios: 'count-convenios',
    litigios: 'count-litigios',
    sustanciacion: 'count-sustanciacion',
    indices: 'count-indices',
    actuaciones: 'count-actuaciones',
  };

  /**
   * Animación count-up para un elemento numérico.
   */
  function animateCountUp(element, targetValue, durationMs = 600) {
    const startValue = parseInt(element.textContent, 10) || 0;
    if (startValue === targetValue) return;

    const startTime = performance.now();
    const difference = targetValue - startValue;

    function updateFrame(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / durationMs, 1);
      const easeProgress = 1 - Math.pow(1 - progress, 3);
      const currentValue = Math.round(startValue + difference * easeProgress);

      element.textContent = currentValue;

      if (progress < 1) {
        requestAnimationFrame(updateFrame);
      } else {
        element.classList.add('animate-count');
        setTimeout(() => element.classList.remove('animate-count'), 400);
      }
    }

    requestAnimationFrame(updateFrame);
  }

  /**
   * Fetch de conteos desde la API y actualización del DOM.
   */
  async function fetchAndUpdateCounts() {
    try {
      const response = await fetch(COUNTS_API_URL, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin',
      });

      if (!response.ok) return;

      const counts = await response.json();

      Object.entries(CARD_IDS).forEach(([key, elementId]) => {
        const element = document.getElementById(elementId);
        if (element && counts[key] !== undefined) {
          animateCountUp(element, counts[key]);
        }
      });
    } catch (error) {
      console.warn('[SGEJ] Error al obtener conteos:', error.message);
    }
  }

  /**
   * Búsqueda en tabla del historial (client-side para responsividad).
   */
  function initializeTableSearch(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    if (!input || !table) return;

    input.addEventListener('input', function () {
      const query = this.value.toLowerCase().trim();
      const rows = table.querySelectorAll('tbody tr');

      rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
      });
    });
  }

  /**
   * Inicialización: primer fetch + polling periódico.
   */
  function initialize() {
    fetchAndUpdateCounts();
    setInterval(fetchAndUpdateCounts, POLLING_INTERVAL_MS);
    initializeTableSearch('search-historial', 'table-historial');
  }

  return { initialize, fetchAndUpdateCounts };
})();

document.addEventListener('DOMContentLoaded', SgejDashboard.initialize);
