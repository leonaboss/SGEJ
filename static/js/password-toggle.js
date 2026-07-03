(function () {
  'use strict';

  function togglePassword(inputId, btn) {
    var input = document.getElementById(inputId);
    if (!input) return;
    var icon = btn.querySelector('i');
    if (input.type === 'password') {
      input.type = 'text';
      icon.className = 'bi bi-eye-slash';
    } else {
      input.type = 'password';
      icon.className = 'bi bi-eye';
    }
  }

  function filterCedula(input) {
    var raw = input.value;
    var filtered = '';
    for (var i = 0; i < raw.length; i++) {
      var ch = raw.charAt(i);
      if (ch === 'V' && filtered.length === 0) {
        filtered += ch;
      } else if (ch === '-' && filtered === 'V') {
        filtered += ch;
      } else if (ch >= '0' && ch <= '9') {
        filtered += ch;
      }
    }
    if (filtered !== raw) {
      input.value = filtered;
    }
  }

  function filterDigits(input) {
    var raw = input.value;
    var filtered = raw.replace(/[^0-9]/g, '');
    if (filtered !== raw) {
      input.value = filtered;
    }
  }

  function preventNonDigit(e) {
    var k = e.key;
    if (k === 'Backspace' || k === 'Delete' || k === 'Tab' || k === 'ArrowLeft' || k === 'ArrowRight' || k === 'Home' || k === 'End') return;
    if (k < '0' || k > '9') e.preventDefault();
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('input[type="password"]').forEach(function (input) {
      if (input.dataset.toggleAdded) return;
      input.dataset.toggleAdded = 'true';

      var wrapper = input.closest('.input-group') || input.parentNode;
      if (wrapper.querySelector('.toggle-password-btn')) return;

      if (!wrapper.classList.contains('input-group')) {
        wrapper = document.createElement('div');
        wrapper.className = 'input-group';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
      }

      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'input-group-text bg-light toggle-password-btn';
      btn.setAttribute('onclick', 'togglePassword("' + input.id + '", this)');
      btn.innerHTML = '<i class="bi bi-eye"></i>';
      wrapper.appendChild(btn);
    });

    document.querySelectorAll('input[name="cedula"]').forEach(function (input) {
      if (input.dataset.cedulaFilter) return;
      input.dataset.cedulaFilter = 'true';
      input.setAttribute('inputmode', 'numeric');
      filterCedula(input);
      input.addEventListener('input', function () { filterCedula(input); });
      input.addEventListener('keydown', function (e) {
        var k = e.key;
        if (k === 'Backspace' || k === 'Delete' || k === 'Tab' || k === 'ArrowLeft' || k === 'ArrowRight' || k === 'Home' || k === 'End') return;
        if (k === 'v' || k === 'V') {
          if (this.value.length > 0 && this.value.indexOf('V') !== -1) e.preventDefault();
          return;
        }
        if (k === '-') {
          if (this.value !== 'V') e.preventDefault();
          return;
        }
        if (k < '0' || k > '9') e.preventDefault();
      });
    });

    document.querySelectorAll('input[name="telefono"]').forEach(function (input) {
      if (input.dataset.phoneFilter) return;
      input.dataset.phoneFilter = 'true';
      input.setAttribute('inputmode', 'numeric');
      filterDigits(input);
      input.addEventListener('input', function () { filterDigits(input); });
      input.addEventListener('keydown', preventNonDigit);
    });
  });

  window.togglePassword = togglePassword;
  window.filterCedula = filterCedula;
  window.filterDigits = filterDigits;
})();
