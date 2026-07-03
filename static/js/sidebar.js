/**
 * SGEJ — Sidebar Toggle (Responsive)
 */
const SgejSidebar = (() => {
  'use strict';

  function initialize() {
    const toggleBtn = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sgej-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (!toggleBtn || !sidebar) return;

    function isDesktop() {
      return window.innerWidth >= 992;
    }

    function openSidebar() {
      sidebar.classList.add('show');
      if (overlay && !isDesktop()) overlay.classList.add('show');
    }

    function closeSidebar() {
      sidebar.classList.remove('show');
      if (overlay) overlay.classList.remove('show');
    }

    // Desktop: sidebar visible por defecto
    if (isDesktop()) sidebar.classList.add('show');

    toggleBtn.addEventListener('click', () => {
      if (sidebar.classList.contains('show')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });

    if (overlay) {
      overlay.addEventListener('click', closeSidebar);
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && sidebar.classList.contains('show')) {
        closeSidebar();
      }
    });

    // Re-evaluar al redimensionar la ventana
    let resizeTimer;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        if (isDesktop()) {
          sidebar.classList.add('show');
          if (overlay) overlay.classList.remove('show');
        }
      }, 150);
    });
  }

  return { initialize };
})();

document.addEventListener('DOMContentLoaded', SgejSidebar.initialize);
