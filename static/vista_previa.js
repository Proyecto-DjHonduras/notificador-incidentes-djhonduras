// ==========================================================
// Vista previa en vivo de la notificación de WhatsApp.
// Lee los campos del formulario "Crear notificación" y arma un texto
// con el MISMO formato que genera el servidor (generar_texto_whatsapp),
// para que el analista vea cómo se está construyendo la plantilla.
// ==========================================================
(function () {
  var salida = document.getElementById('vistaPrevia');
  var form = document.getElementById('formIncidente');
  if (!salida || !form) return;

  // Helpers para leer campos por su name="".
  function val(nombre) {
    var el = form.querySelector('[name="' + nombre + '"]');
    return el ? el.value.trim() : '';
  }
  // Texto visible de la opción elegida en un <select>.
  function texto(nombre) {
    var el = form.querySelector('[name="' + nombre + '"]');
    if (!el || el.selectedIndex < 0) return '';
    return el.options[el.selectedIndex].text.trim();
  }

  // Formatea "2026-09-27T15:30" (datetime-local) a "27/09/2026 15:30".
  function formatoFecha(valor) {
    if (!valor) return '—';
    var partes = valor.split('T');
    if (partes.length < 2) return valor;
    var f = partes[0].split('-'); // [YYYY, MM, DD]
    var h = partes[1].slice(0, 5); // HH:MM
    if (f.length < 3) return valor;
    return f[2] + '/' + f[1] + '/' + f[0] + ' ' + h;
  }

  function construir() {
    var estado = val('estado');
    var esResuelto = estado === 'resuelto';

    var lineas = [];
    lineas.push(esResuelto ? '✅ *CIERRE DE INCIDENTE* ✅' : '⚠️ *INICIO DE INCIDENTE* ⚠️');
    lineas.push('');

    var ticket = val('ticket') || 'Por generarse';
    var nombre = val('incidente') || '(sin nombre)';
    lineas.push('📌 *Incidente:* ' + ticket + ' - ' + nombre);
    lineas.push('👥 *Afectación a cliente:* ' + (texto('afectacion_cliente') || '—'));
    lineas.push('🔺 *Prioridad:* ' + (val('prioridad') || '—'));
    lineas.push('🔍 *¿Cómo se detectó?:* ' + (texto('como_se_detecto') || '—'));
    lineas.push('📋 *Cómo se detectó el incidente:* ' + (val('reporte_inicial') || '—'));
    lineas.push('');
    lineas.push('🕐 *Hora inicio de falla:* ' + formatoFecha(val('hora_inicio')));
    lineas.push('📌 *Estado:* ' + (texto('estado') || '—'));
    lineas.push('');
    lineas.push('📝 *Descripción:* ' + (val('descripcion') || '—'));
    lineas.push('');

    // Áreas involucradas (desde el campo oculto que llena areas.js).
    lineas.push('*Áreas involucradas:*');
    var areas = val('areas_seleccionadas');
    if (areas) {
      areas.split(',').map(function (s) { return s.trim(); }).filter(Boolean)
        .forEach(function (a) { lineas.push('- ' + a); });
    }
    lineas.push('');

    // Personas involucradas (texto separado por comas).
    lineas.push('*Personas involucradas:*');
    var personas = val('personas_texto');
    if (personas) {
      personas.split(',').map(function (s) { return s.trim(); }).filter(Boolean)
        .forEach(function (p) { lineas.push('- ' + p); });
    }
    lineas.push('');

    // Avances: en la creación aún no hay, se muestra la sección vacía.
    lineas.push('*Avances*');

    // Solución (solo si está resuelto).
    if (esResuelto) {
      lineas.push('');
      lineas.push('✅ *Solución:*');
      lineas.push(val('solucion') || '—');
    }

    salida.textContent = lineas.join('\n');
  }

  // Recalcular ante cualquier cambio o tecleo en el formulario.
  form.addEventListener('input', construir);
  form.addEventListener('change', construir);
  // Y cuando el componente de áreas avise que cambió.
  document.addEventListener('areas:cambio', construir);

  // Primer dibujo.
  construir();
})();
