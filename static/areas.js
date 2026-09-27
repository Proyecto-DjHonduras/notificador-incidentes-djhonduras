// ==========================================================
// Componente de "Areas involucradas": MULTISELECCIÓN.
// Un botón abre un panel con casillas (checkboxes). El analista puede
// marcar varias áreas a la vez y buscarlas por nombre. Las áreas elegidas
// se muestran como etiquetas (chips) y se guardan, separadas por comas,
// en el campo oculto name="areas_seleccionadas" para enviarlas al servidor.
// ==========================================================
(function () {
  var contenedor = document.getElementById('areasMulti');
  var toggle = document.getElementById('areasToggle');
  var panel = document.getElementById('areasPanel');
  var buscar = document.getElementById('areasBuscar');
  var opciones = document.getElementById('areasOpciones');
  var resumen = document.getElementById('areasResumen');
  var lista = document.getElementById('areasList');
  // El campo oculto real que se envia (lo genera Django).
  var oculto = document.querySelector('input[name="areas_seleccionadas"]');

  if (!contenedor || !toggle || !panel || !opciones || !lista || !oculto) return;

  // Todas las casillas del panel.
  var casillas = Array.prototype.slice.call(
    opciones.querySelectorAll('input[type="checkbox"]')
  );

  // Devuelve la lista de áreas marcadas (en el orden del panel).
  function seleccionadas() {
    return casillas.filter(function (c) { return c.checked; })
                   .map(function (c) { return c.value; });
  }

  // Actualiza el campo oculto, el texto del botón y las etiquetas.
  function sincronizar() {
    var elegidas = seleccionadas();

    // 1) Campo oculto (lo que se envía al servidor), separado por comas.
    oculto.value = elegidas.join(', ');

    // 2) Texto resumen dentro del botón.
    if (elegidas.length === 0) {
      resumen.textContent = 'Selecciona una o varias áreas';
      resumen.classList.add('placeholder');
    } else if (elegidas.length <= 2) {
      resumen.textContent = elegidas.join(', ');
      resumen.classList.remove('placeholder');
    } else {
      resumen.textContent = elegidas.length + ' áreas seleccionadas';
      resumen.classList.remove('placeholder');
    }

    // 3) Etiquetas (chips) con botón para quitar.
    pintarChips(elegidas);

    // 4) Avisamos a la vista previa que hubo un cambio.
    document.dispatchEvent(new CustomEvent('areas:cambio'));
  }

  // Dibuja las etiquetas de áreas elegidas.
  function pintarChips(elegidas) {
    lista.innerHTML = '';
    elegidas.forEach(function (nombre) {
      var li = document.createElement('li');
      li.className = 'tag';
      li.textContent = nombre + ' ';
      var x = document.createElement('span');
      x.textContent = '✕';
      x.className = 'tag-x';
      x.onclick = function () {
        // Desmarcamos la casilla correspondiente y re-sincronizamos.
        var casilla = casillas.filter(function (c) { return c.value === nombre; })[0];
        if (casilla) casilla.checked = false;
        sincronizar();
      };
      li.appendChild(x);
      lista.appendChild(li);
    });
  }

  // Abrir / cerrar el panel.
  function abrir() {
    panel.hidden = false;
    contenedor.classList.add('abierto');
    if (buscar) { buscar.value = ''; filtrar(''); buscar.focus(); }
  }
  function cerrar() {
    panel.hidden = true;
    contenedor.classList.remove('abierto');
  }

  toggle.addEventListener('click', function (e) {
    e.stopPropagation();
    if (panel.hidden) abrir(); else cerrar();
  });

  // Cada vez que se marca/desmarca una casilla, sincronizamos.
  casillas.forEach(function (c) {
    c.addEventListener('change', sincronizar);
  });

  // Filtro de búsqueda dentro del panel.
  function filtrar(texto) {
    texto = (texto || '').toLowerCase().trim();
    var items = opciones.querySelectorAll('li');
    Array.prototype.forEach.call(items, function (li) {
      var nombre = li.textContent.toLowerCase();
      li.style.display = (!texto || nombre.indexOf(texto) !== -1) ? '' : 'none';
    });
  }
  if (buscar) {
    buscar.addEventListener('input', function () { filtrar(buscar.value); });
    // Evita que un Enter en el buscador envíe el formulario.
    buscar.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') e.preventDefault();
    });
  }

  // Cerrar el panel al hacer clic fuera de él.
  document.addEventListener('click', function (e) {
    if (!contenedor.contains(e.target)) cerrar();
  });

  // Precarga: si el campo oculto ya trae áreas (al editar), marcamos sus casillas.
  if (oculto.value.trim()) {
    var iniciales = oculto.value.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
    casillas.forEach(function (c) {
      if (iniciales.indexOf(c.value) !== -1) c.checked = true;
    });
  }

  // Estado inicial.
  sincronizar();
})();
