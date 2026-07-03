/**
 * SGEJ — Modal de Doble Confirmación de Seguridad
 * Sección 4.3 del Plan Maestro.
 * Responsabilidad: Control centralizado de modales de confirmación para acciones críticas.
 */

const SgejModals = (() => {
  'use strict';

  let currentCallback = null;
  let currentResourceName = '';
  let modalInstance = null;

  /**
   * Abre el modal de confirmación de seguridad.
   * @param {string} resourceName - Nombre del recurso a validar.
   * @param {string} actionLabel - Etiqueta de la acción (ej: "Eliminar", "Archivar").
   * @param {Function} onConfirm - Callback ejecutado tras validación exitosa.
   */
  function openSecurityModal(resourceName, actionLabel, onConfirm) {
    const modalEl = document.getElementById('modalConfirmacionSeguridad');
    if (!modalEl) {
      console.error('[SGEJ] Modal de confirmación no encontrado en el DOM.');
      return;
    }

    currentResourceName = resourceName;
    currentCallback = onConfirm;

    const input = document.getElementById('inputNombreValidacionArchivo');
    const confirmBtn = document.getElementById('btnConfirmarAccionCritica');
    const actionLabelEl = document.getElementById('modal-action-label');

    if (input) {
      input.value = '';
      input.placeholder = `Escriba "${resourceName}" para confirmar`;
    }
    if (confirmBtn) {
      confirmBtn.disabled = true;
      confirmBtn.textContent = actionLabel || 'Ejecutar y Registrar Transacción';
    }
    if (actionLabelEl) {
      actionLabelEl.textContent = actionLabel || 'esta acción';
    }

    modalInstance = new bootstrap.Modal(modalEl, { backdrop: 'static' });
    modalInstance.show();
  }

  /**
   * Valida el input contra el nombre del recurso.
   */
  function validateInput() {
    const input = document.getElementById('inputNombreValidacionArchivo');
    const confirmBtn = document.getElementById('btnConfirmarAccionCritica');
    if (!input || !confirmBtn) return;

    const isValid = input.value.trim() === currentResourceName.trim();
    confirmBtn.disabled = !isValid;
  }

  /**
   * Ejecuta la acción confirmada.
   */
  function executeConfirmedAction() {
    if (typeof currentCallback === 'function') {
      currentCallback();
    }
    if (modalInstance) {
      modalInstance.hide();
    }
    currentCallback = null;
    currentResourceName = '';
  }

  /**
   * Inicialización de eventos.
   */
  function initialize() {
    const input = document.getElementById('inputNombreValidacionArchivo');
    if (input) {
      input.addEventListener('input', validateInput);
    }

    const confirmBtn = document.getElementById('btnConfirmarAccionCritica');
    if (confirmBtn) {
      confirmBtn.addEventListener('click', executeConfirmedAction);
    }

    // Delegación de eventos para botones con data-sgej-action
    document.addEventListener('click', function (event) {
      const actionBtn = event.target.closest('[data-sgej-action]');
      if (!actionBtn) return;

      event.preventDefault();
      const action = actionBtn.dataset.sgejAction;
      const resourceName = actionBtn.dataset.sgejResource || '';
      const targetUrl = actionBtn.dataset.sgejUrl || '';
      const actionLabel = actionBtn.dataset.sgejLabel || 'Ejecutar Acción';

      openSecurityModal(resourceName, actionLabel, function () {
        if (action === 'delete' || action === 'archive') {
          const form = document.createElement('form');
          form.method = 'POST';
          form.action = targetUrl;

          const csrfInput = document.createElement('input');
          csrfInput.type = 'hidden';
          csrfInput.name = 'csrfmiddlewaretoken';
          csrfInput.value = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
          form.appendChild(csrfInput);

          const actionInput = document.createElement('input');
          actionInput.type = 'hidden';
          actionInput.name = 'action';
          actionInput.value = action;
          form.appendChild(actionInput);

          document.body.appendChild(form);
          form.submit();
        } else if (action === 'navigate') {
          window.location.href = targetUrl;
        }
      });
    });
  }

  return { initialize, openSecurityModal };
})();

document.addEventListener('DOMContentLoaded', SgejModals.initialize);
