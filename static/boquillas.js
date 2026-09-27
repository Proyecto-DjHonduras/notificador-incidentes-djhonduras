// ==========================================================
// Boquillas: mensajes informativos previos.
// - Muestra el mensaje enmarcado entre los banners "📢 Nos permitimos informar que: 📢".
// - Botón "Copiar" para el editor y para cada boquilla del historial.
// - Al guardar, envía el texto (sin los banners) al servidor.
// ==========================================================
(function () {
  var BANNER = '📢 Nos permitimos informar que:';

  var textarea = document.getElementById('boquillaTexto');
  var preview = document.getElementById('boquillaPreview');
  var btnCopiar = document.getElementById('btnCopiar');
  var inputGuardar = document.getElementById('inputGuardarTexto');
  var inputNombre = document.getElementById('inputGuardarNombre');
  var formGuardar = document.getElementById('formGuardar');

  // Arma el mensaje completo: banner arriba y el parlante al FINAL del texto.
  // Queda:  📢 Nos permitimos informar que:
  //         <texto> 📢
  function enmarcar(texto) {
    return BANNER + '\n' + (texto || '') + ' 📢';
  }

  // Copia un texto al portapapeles con aviso breve en el botón.
  function copiar(texto, boton) {
    var etiquetaOriginal = boton ? boton.textContent : '';
    function ok() {
      if (boton) {
        boton.textContent = '✅ Copiado';
        setTimeout(function () { boton.textContent = etiquetaOriginal; }, 1500);
      }
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(texto).then(ok).catch(function () { copiarFallback(texto, ok); });
    } else {
      copiarFallback(texto, ok);
    }
  }

  // Método alternativo si el navegador no permite clipboard (http, permisos).
  function copiarFallback(texto, alTerminar) {
    var tmp = document.createElement('textarea');
    tmp.value = texto;
    tmp.style.position = 'fixed';
    tmp.style.opacity = '0';
    document.body.appendChild(tmp);
    tmp.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(tmp);
    if (alTerminar) alTerminar();
  }

  // ---------- EDITOR ----------
  if (textarea && preview) {
    function refrescar() {
      var t = textarea.value.trim();
      preview.textContent = t ? enmarcar(t) : enmarcar('...');
    }
    textarea.addEventListener('input', refrescar);
    refrescar();

    if (btnCopiar) {
      btnCopiar.addEventListener('click', function () {
        copiar(enmarcar(textarea.value.trim()), btnCopiar);
      });
    }

    // Al guardar, pedimos un NOMBRE y mandamos el texto escrito
    // (los parlantes se agregan al copiar/mostrar, no se guardan).
    if (formGuardar && inputGuardar) {
      formGuardar.addEventListener('submit', function (e) {
        var t = textarea.value.trim();
        if (!t) {
          e.preventDefault();
          alert('Escribe un mensaje antes de guardar.');
          return;
        }
        var nombre = window.prompt('Ponle un nombre a esta boquilla:', '');
        // Si cancela el prompt, no guardamos.
        if (nombre === null) {
          e.preventDefault();
          return;
        }
        if (inputNombre) inputNombre.value = nombre.trim();
        inputGuardar.value = t;
      });
    }
  }

  // ---------- HISTORIAL (copiar cada item) ----------
  var botones = document.querySelectorAll('.btnCopiarItem');
  Array.prototype.forEach.call(botones, function (boton) {
    boton.addEventListener('click', function () {
      var item = boton.closest('.boquilla-item');
      var cont = item ? item.querySelector('.boquilla-item-texto') : null;
      if (!cont) return;
      // data-texto ya trae el mensaje enmarcado (con \n codificados como &#10;).
      var texto = cont.getAttribute('data-texto') || enmarcar(cont.textContent.trim());
      copiar(texto, boton);
    });
  });

  // ---------- RENOMBRAR (doble clic en el nombre o botón "Renombrar") ----------

  // Lee el token CSRF desde cualquier formulario de la página.
  function tokenCsrf() {
    var el = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return el ? el.value : '';
  }

  // Envía el nuevo nombre al servidor por AJAX.
  function guardarNombre(id, nombre, elemento) {
    var datos = new URLSearchParams();
    datos.append('accion', 'renombrar');
    datos.append('boquilla_id', id);
    datos.append('nombre', nombre);
    datos.append('csrfmiddlewaretoken', tokenCsrf());

    fetch(window.location.pathname, {
      method: 'POST',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      body: datos
    }).then(function (r) {
      return r.ok ? r.json() : null;
    }).then(function (data) {
      var texto = (data && typeof data.nombre === 'string') ? data.nombre : nombre;
      elemento.setAttribute('data-nombre', texto);
      elemento.textContent = texto || '(sin nombre)';
    }).catch(function () {
      // Si falla el AJAX, dejamos el texto que se escribió.
      elemento.textContent = nombre || '(sin nombre)';
    });
  }

  // Convierte el <div> del nombre en un input editable.
  function editarNombre(elemento) {
    if (elemento.querySelector('input')) return; // ya está en edición
    var item = elemento.closest('.boquilla-item');
    var id = item ? item.getAttribute('data-id') : null;
    if (!id) return;

    var actual = elemento.getAttribute('data-nombre') || '';
    var input = document.createElement('input');
    input.type = 'text';
    input.value = actual;
    input.className = 'boquilla-nombre-input';
    input.maxLength = 120;

    elemento.textContent = '';
    elemento.appendChild(input);
    input.focus();
    input.select();

    var yaGuardado = false;
    function confirmar() {
      if (yaGuardado) return;
      yaGuardado = true;
      var nuevo = input.value.trim();
      guardarNombre(id, nuevo, elemento);
    }
    function cancelar() {
      if (yaGuardado) return;
      yaGuardado = true;
      elemento.textContent = actual || '(sin nombre)';
    }

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); confirmar(); }
      else if (e.key === 'Escape') { e.preventDefault(); cancelar(); }
    });
    input.addEventListener('blur', confirmar);
  }

  // Doble clic sobre el nombre.
  var nombres = document.querySelectorAll('.boquilla-item-nombre');
  Array.prototype.forEach.call(nombres, function (el) {
    el.addEventListener('dblclick', function () { editarNombre(el); });
  });

  // Botón "Renombrar" de cada item.
  var botonesRenombrar = document.querySelectorAll('.btnRenombrar');
  Array.prototype.forEach.call(botonesRenombrar, function (boton) {
    boton.addEventListener('click', function () {
      var item = boton.closest('.boquilla-item');
      var el = item ? item.querySelector('.boquilla-item-nombre') : null;
      if (el) editarNombre(el);
    });
  });
})();
