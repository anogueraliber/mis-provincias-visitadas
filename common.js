/* Parte común de todas las pantallas: almacenamiento, barra de navegación y copia de seguridad única. */
(function (g) {
'use strict';
var KEY = 'misViajes.v1';
var NS = ['mundo', 'es', 'fr', 'it', 'gr', 'tr', 'mk'];
var PAGES = {
  mundo: { n: 'Mundo', f: '🌍', u: 'mundo.html' },
  es: { n: 'España', f: '🇪🇸', u: 'index.html?p=es' },
  fr: { n: 'Francia', f: '🇫🇷', u: 'index.html?p=fr' },
  it: { n: 'Italia', f: '🇮🇹', u: 'index.html?p=it' },
  gr: { n: 'Grecia', f: '🇬🇷', u: 'index.html?p=gr' },
  tr: { n: 'Turquía', f: '🇹🇷', u: 'index.html?p=tr' },
  mk: { n: 'Macedonia del Norte', f: '🇲🇰', u: 'index.html?p=mk' }
};
var data = {};

function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
function parse(s) { try { var o = JSON.parse(s || '{}'); return o && typeof o === 'object' ? o : {}; } catch (e) { return {}; } }

function load() {
  var raw = lsGet(KEY);
  data = raw ? parse(raw) : {};
  NS.forEach(function (n) { if (!data[n] || typeof data[n] !== 'object') data[n] = {}; });
  if (!raw) { // primera vez: se recogen los datos de las versiones anteriores (una clave por pantalla)
    var es = parse(lsGet('misProvinciasVisitadas.v1')), mu = parse(lsGet('misPaisesVisitados.v1'));
    Object.keys(es).forEach(function (id) { data.es[id] = es[id]; });
    Object.keys(mu).forEach(function (id) { var r = mu[id]; if (r && (r.s === 'l' || r.s === 'p')) r.s = 'v'; data.mundo[id] = r; });
    save();
  }
}
function save() { lsSet(KEY, JSON.stringify(data)); }

/* ---------- Barra de pestañas ---------- */
function nav(active) {
  var st = document.createElement('style');
  st.textContent = '#nav{display:flex;gap:6px;overflow-x:auto;-webkit-overflow-scrolling:touch;margin:0 -16px 10px;padding:6px 16px;position:sticky;top:0;z-index:20;background:var(--bg)}' +
    '#nav a{flex:none;display:inline-flex;align-items:center;gap:6px;padding:8px 12px;border:1px solid var(--line);border-radius:999px;background:var(--card);color:var(--text);text-decoration:none;font-size:.95rem;min-height:40px}' +
    '#nav a[aria-current=page]{background:var(--navon,#1f7a4d);border-color:var(--navon,#1f7a4d);color:#fff}' +
    '#toast{position:fixed;left:16px;right:16px;bottom:calc(16px + env(safe-area-inset-bottom));max-width:520px;margin:0 auto;background:#1d2330;color:#fff;padding:10px 14px;border-radius:12px;z-index:30;display:none;font-size:.95rem}';
  document.head.appendChild(st);
  var el = document.getElementById('nav'); el.textContent = '';
  NS.forEach(function (k) {
    var a = document.createElement('a'); a.href = PAGES[k].u; a.textContent = PAGES[k].f + ' ' + PAGES[k].n;
    if (k === active) a.setAttribute('aria-current', 'page');
    el.appendChild(a);
  });
  var t = document.createElement('div'); t.id = 'toast'; document.body.appendChild(t);
}
var tt;
function toast(msg) { var t = document.getElementById('toast'); if (!t) return; t.textContent = msg; t.style.display = 'block'; clearTimeout(tt); tt = setTimeout(function () { t.style.display = 'none'; }, 3800); }

/* ---------- Copia de seguridad: un único archivo con todo ---------- */
function saveFile(obj, name) {
  var text = JSON.stringify(obj, null, 2), mobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  try { // en móvil: menú de compartir → «Guardar en Archivos» pregunta si reemplazar el archivo anterior
    var file = new File([text], name, { type: 'application/json' });
    if (mobile && navigator.canShare && navigator.canShare({ files: [file] })) { navigator.share({ files: [file] }).catch(function () {}); return; }
  } catch (e) {}
  var blob = new Blob([text], { type: 'application/json' }), a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = name;
  document.body.appendChild(a); a.click(); a.remove(); setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
}
function guardar() {
  fetch('datos/nombres.json').then(function (r) { return r.json(); }).catch(function () { return {}; }).then(function (names) {
    var out = { app: 'mis-viajes', version: 3, exportado: new Date().toISOString(), datos: {} };
    NS.forEach(function (ns) {
      var o = {};
      Object.keys(data[ns]).forEach(function (id) {
        var r = data[ns][id]; if (!r || !(r.v || r.s || r.y || r.n)) return;
        var e = ns === 'mundo' ? { estado: r.s === 'v' ? 'ido' : r.s === 'w' ? 'quiero' : '' } : { visitada: !!r.v };
        e.anio = r.y || ''; e.notas = r.n || ''; e.nombre = (names[ns] || {})[id] || ''; o[id] = e;
      });
      out.datos[ns] = o;
    });
    saveFile(out, 'mis-viajes.json');
  });
}
function rec(ns, e) {
  var y = String(e.anio || '').replace(/\D/g, '').slice(0, 4), n = String(e.notas || '').slice(0, 2000);
  if (ns === 'mundo') { var s = e.estado === 'ido' ? 'v' : e.estado === 'quiero' ? 'w' : (e.estado === 'vivo' || e.estado === 'vivida') ? 'v' : ''; return (s || y || n) ? { s: s, y: y, n: n } : null; }
  return (e.visitada || y || n) ? { v: e.visitada ? 1 : 0, y: y, n: n } : null;
}
function section(src, ns, dst) { var c = 0; Object.keys(src || {}).forEach(function (id) { var r = rec(ns, src[id] || {}); if (r) { dst[id] = r; c++; } }); return c; }

/* Importa copias de esta versión (mis-viajes) y de las anteriores (provincias / países) */
function importar(file) {
  var rd = new FileReader();
  rd.onload = function () {
    var j; try { j = JSON.parse(rd.result); } catch (e) { j = null; }
    if (!j || typeof j !== 'object') return alert('El archivo no es una copia válida de esta aplicación.');
    var nd = JSON.parse(JSON.stringify(data)), msg = '', ok = true, aliasP = Promise.resolve({});
    if (j.app === 'mis-viajes' && j.datos) {
      NS.forEach(function (ns) { if (!j.datos[ns]) return; nd[ns] = {}; var c = section(j.datos[ns], ns, nd[ns]); msg += (msg ? ', ' : '') + PAGES[ns].n + ': ' + c; });  // solo se reemplazan las pantallas que trae el archivo
    } else if (j.app === 'mis-provincias-visitadas' && j.provincias) {
      var keepCities = {}; Object.keys(nd.es).forEach(function (id) { if (id.indexOf('c_') === 0) keepCities[id] = nd.es[id]; });
      nd.es = {}; var c1 = section(j.provincias, 'es', nd.es), c2 = 0;
      if (j.ciudades) { // ids antiguos c_<nombre> → código INE
        aliasP = fetch('datos/es/ciudades.json').then(function (r) { return r.json(); }).then(function (d) { var m = {}; d.ciudades.forEach(function (c) { if (c.old) m[c.old] = c.id; }); return m; }).catch(function () { return {}; });
        var tmp = {}; c2 = section(j.ciudades, 'es', tmp); nd.__tmp = tmp;
      } else Object.keys(keepCities).forEach(function (id) { nd.es[id] = keepCities[id]; });
      msg = 'España: ' + c1 + ' provincias' + (j.ciudades ? ' y ' + c2 + ' ciudades' : '');
    } else if (j.app === 'mis-paises-visitados' && j.paises) {
      nd.mundo = {}; msg = 'Mundo: ' + section(j.paises, 'mundo', nd.mundo);
    } else ok = false;
    if (!ok) return alert('El archivo no es una copia válida de esta aplicación.');
    aliasP.then(function (alias) {
      if (nd.__tmp) { Object.keys(nd.__tmp).forEach(function (id) { nd.es[alias[id] || id] = nd.__tmp[id]; }); delete nd.__tmp; }
      if (!confirm('Se reemplazarán tus datos actuales por los de la copia (' + msg + ' marcados). ¿Continuar?')) return;
      data = nd; save(); location.reload();
    });
  };
  rd.readAsText(file);
}

g.V = { NS: NS, PAGES: PAGES, load: load, save: save, ns: function (n) { return data[n]; }, nav: nav, toast: toast, guardar: guardar, importar: importar,
        all: function () { return data; } };
load();
})(window);
