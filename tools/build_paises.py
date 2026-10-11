"""Genera datos/<pais>/{unidades,ciudades}.json y datos/nombres.json para las páginas de país.
Países: es, fr, it, gr, tr, mk. Las coordenadas se proyectan aquí (x = lon·cos φ0, y = −lat) y los recuadros de ultramar se desplazan.
Fuentes (volcadas antes a JSON en una carpeta de trabajo, ver README):
  es: tools/intermedios/es_unidades.geojson + es_ciudades.json   (build_ciudades_es.py)
  fr: Natural Earth admin_1 (departamentos) + @etalab/decoupage-administratif (comunas, INSEE) + GeoNames (coordenadas)
  it: geoBoundaries ADM3 (CC BY 4.0, provincias) + comuni-json (ISTAT) + GeoNames (coordenadas)
  gr: tools/build_grecia_unidades.py (74 unidades regionales + Monte Athos) + @tsevdos/el-utils + GeoNames (población)
  tr: geoBoundaries ADM1 (81 provincias) + códigos de matrícula de Natural Earth + lista de distritos de turkey-neighbourhoods + GeoNames (población)
  mk: geoBoundaries ADM1 (8 regiones estadísticas) + GeoNames (ciudades y población)
Uso: python tools/build_paises.py <carpeta_trabajo>      (requiere: shapely, geonamescache)"""
import json, math, os, re, sys, unicodedata
import geonamescache
from shapely.geometry import Point, shape
from shapely.prepared import prep

W = sys.argv[1]
MIN_POP, BIG, REVIEW, TOL = 20000, 50000, (17000, 23000), 0.004
GN = geonamescache.GeonamesCache().get_cities()

def norm(s):
    s = unicodedata.normalize('NFD', s.lower().replace('ı', 'i')); s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', ' ', s.replace("'", ' ')).strip()
def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))
def num(v): s = ('%.3f' % v).rstrip('0').rstrip('.'); return '0' if s in ('-0', '') else s

def dp(pts, t):
    if len(pts) < 3: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True; st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop(); (x1, y1), (x2, y2) = pts[a], pts[b]; dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy); m = -1; mi = -1
        for i in range(a + 1, b):
            x, y = pts[i]; d = math.hypot(x - x1, y - y1) if L == 0 else abs(dy * (x - x1) - dx * (y - y1)) / L
            if d > m: m, mi = d, i
        if m > t: keep[mi] = True; st += [(a, mi), (mi, b)]
    return [p for p, k in zip(pts, keep) if k]
def ring_area(r): return abs(sum(r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1] for i in range(len(r) - 1))) / 2

# --- Definición de países -------------------------------------------------------------------
CFG = {
 'es': dict(nombre='España', unidad='provincias', unidad1='provincia', tab='Provincias', flag='🇪🇸', lat0=40, mundo='ESP',
            grupos=[(['35', '38'], (8.6, 6.1), 'Canarias')]),
 'fr': dict(nombre='Francia', unidad='départements', unidad1='département', tab='Départements', flag='🇫🇷', lat0=46.5, mundo='FXX',
            destinos={'973': (-8.5, 48.6), '971': (-8.5, 45.9), '972': (-8.5, 44.2), '974': (-5.0, 45.9), '976': (-5.0, 44.2)}),
 'it': dict(nombre='Italia', unidad='provincias y ciudades metropolitanas', unidad1='provincia', tab='Provincias', flag='🇮🇹', lat0=42, mundo='ITA'),
 'tr': dict(nombre='Turquía', unidad='provincias (il)', unidad1='provincia', tab='Provincias', flag='🇹🇷', lat0=39, mundo='TUR'),
 'mk': dict(nombre='Macedonia del Norte', unidad='regiones estadísticas', unidad1='región', tab='Regiones', flag='🇲🇰', lat0=41.6, mundo='MKD'),
 'gr': dict(nombre='Grecia', unidad='unidades regionales', unidad1='unidad regional', tab='Unidades', flag='🇬🇷', lat0=38.5, mundo='GRC'),
}

def polys(geom):
    g = shape(geom) if isinstance(geom, dict) else geom
    return list(g.geoms) if g.geom_type in ('MultiPolygon', 'GeometryCollection') else [g]

def build_units(cc, units):
    """units: [{'id','n','geom'}] en lon/lat. Devuelve (unidades.json, función de proyección con desplazamientos)."""
    cfg = CFG[cc]; c0 = math.cos(math.radians(cfg['lat0'])); shift = {}; frames_src = []
    for ids, (dx, dy), _ in cfg.get('grupos', []):
        for i in ids: shift[i] = (dx, dy)
        frames_src.append(ids)
    bbox = {u['id']: shape(u['geom']).bounds for u in units}
    for i, (tx, ty) in cfg.get('destinos', {}).items():
        b = bbox[i]; shift[i] = (tx - (b[0] + b[2]) / 2, ty - (b[1] + b[3]) / 2); frames_src.append([i])
    def proj(lon, lat, uid=None):
        dx, dy = shift.get(uid, (0, 0)); return ((lon + dx) * c0, -(lat + dy))
    items = []; X0 = Y0 = 1e9; X1 = Y1 = -1e9; fr = {}
    for u in units:
        ps = polys(u['geom']); rings = []
        for p in ps:
            ext = list(p.exterior.coords)
            if ring_area(ext) < 0.0004 and len(ps) > 1: continue
            rings.append(ext); rings += [list(h.coords) for h in p.interiors if ring_area(list(h.coords)) > 0.0002]
        if not rings: rings = [list(max(ps, key=lambda p: p.area).exterior.coords)]
        d = ''
        for r in rings:
            s = dp([tuple(p) for p in r], TOL)
            if len(s) < 4: continue
            pts = [proj(x, y, u['id']) for x, y in s]
            d += 'M' + 'L'.join(num(x) + ' ' + num(y) for x, y in pts) + 'Z'
            for x, y in pts:
                X0, X1, Y0, Y1 = min(X0, x), max(X1, x), min(Y0, y), max(Y1, y)
                for g, ids in enumerate(frames_src):
                    if u['id'] in ids:
                        b = fr.setdefault(g, [1e9, 1e9, -1e9, -1e9]); b[0], b[1], b[2], b[3] = min(b[0], x), min(b[1], y), max(b[2], x), max(b[3], y)
        items.append({'id': u['id'], 'n': u['n'], 'd': d})
    frames = [[round(b[0] - .15, 2), round(b[1] - .15, 2), round(b[2] - b[0] + .3, 2), round(b[3] - b[1] + .3, 2)] for b in fr.values()]
    pad = 0.6
    out = {'pais': cfg['nombre'], 'cc': cc, 'unidad': cfg['unidad'], 'unidad1': cfg['unidad1'], 'tab': cfg['tab'], 'flag': cfg['flag'], 'mundo': cfg['mundo'],
           'box': [round(X0 - pad, 2), round(Y0 - pad, 2), round(X1 - X0 + 2 * pad, 2), round(Y1 - Y0 + 2 * pad, 2)], 'frames': frames, 'items': sorted(items, key=lambda i: i['n'])}
    return out, proj

def locate(unit_polys, lon, lat):
    """Unidad que contiene el punto; si cae fuera del polígono simplificado (costa), la más cercana."""
    best = None
    for uid, (pp, geom) in unit_polys.items():
        if pp.contains(Point(lon, lat)): return uid
    for uid, (pp, geom) in unit_polys.items():
        dd = geom.distance(Point(lon, lat))
        if best is None or dd < best[0]: best = (dd, uid)
    return best[1] if best and best[0] < 0.15 else None

def near_units(unit_polys, lon, lat, r=0.06):
    """Unidades cuyo polígono contiene el punto o queda a menos de r grados (los límites están simplificados)."""
    p = Point(lon, lat); return {uid for uid, (pp, geom) in unit_polys.items() if pp.contains(p) or geom.distance(p) < r}

def kfuzzy(s):
    s = norm(s)
    for a, b in (('ph','f'),('y','i'),('ee','i'),('ei','i'),('oi','i'),('ou','u'),('v','b'),('kh','h'),('ch','h'),('th','t'),('dh','d'),('ll','l'),('ss','s')): s = s.replace(a, b)
    s = re.sub(r'[^a-z]', '', s)
    for _ in range(2): s = re.sub(r'(is|os|as|es|us|on|s|n|i|o|a|e|u)$', '', s)
    return s

GENERIC = {'saint', 'sainte', 'san', 'santa', 'santo', 'sant', 'castel', 'porto', 'monte', 'villa', 'borgo', 'campo', 'pont', 'bourg', 'val'}
def first_token(name):
    t = [w for w in norm(name).split() if w not in ('le', 'la', 'les', 'l', 'el', 'il', 'lo', 'los', 'las', 'de', 'di', 'du')]
    return t[0] if t and len(t[0]) >= 4 and t[0] not in GENERIC else None

def tier2(cands, name, unit, log):
    """Municipios fusionados («communes nouvelles», comuni nuevos): se usa el núcleo cuyo primer nombre coincide."""
    ft = first_token(name)
    if not ft: return None
    c2 = [g for g in cands if unit in g['near'] and any(k.split() and k.split()[0] == ft for k in g['keys'])]
    if not c2: return None
    b = max(c2, key=lambda g: g['population']); log.append((name, b['name'])); return b

def gn_candidates(cc):
    """Puntos de GeoNames del país: cities15000 (con nombres alternativos) + all-the-cities (≥1000 hab., para los que GeoNames
    cuenta por debajo de 15.000 como localidad pero son municipios mayores)."""
    codes = {'FR': ('FR', 'GP', 'MQ', 'GF', 'RE', 'YT')}.get(cc.upper(), (cc.upper(),))  # GeoNames da a los DROM su propio código de país
    out = []; seen = set()
    for c in GN.values():
        if c['countrycode'] in codes:
            c = dict(c); c['keys'] = {norm(c['name'])} | {norm(a) for a in c.get('alternatenames', []) if a}; out.append(c); seen.add(c['geonameid'])
    allx = json.load(open(W + '/atc_fr_it_gr.json', encoding='utf-8'))
    extra = [e for k in codes for e in allx.get(k, [])]
    for e in extra:
        if e['id'] in seen: continue
        out.append({'geonameid': e['id'], 'name': e['n'], 'population': e['p'], 'longitude': e['lon'], 'latitude': e['lat'],
                    'keys': {norm(e['n'])} | {norm(a) for a in e['a'].split(',') if a.strip()}})
    return out

def finalize(cc, units, cities, proj, extra=None):
    ud, _ = build_units(cc, units) if proj is None else (None, None)
    return ud

def write(cc, ud, cities, proj, fuente):
    os.makedirs('datos/' + cc, exist_ok=True)
    json.dump(ud, open('datos/%s/unidades.json' % cc, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    pn = {u['id']: u['n'] for u in ud['items']}
    sel = []; border = []
    for c in cities:
        if c['pop'] < REVIEW[0]: continue
        x, y = proj(c['lon'], c['lat'], c['p']) if c.get('lon') is not None else (None, None)
        o = {'id': c['id'], 'n': c['n'], 'p': c['p'], 'pn': pn.get(c['p']) or c['pn'], 'pop': c['pop'], 'big': c['pop'] >= BIG, 'rev': REVIEW[0] <= c['pop'] < REVIEW[1]}
        if x is not None: o['x'], o['y'] = round(x, 3), round(y, 3)
        if c.get('old'): o['old'] = c['old']
        if c['pop'] >= MIN_POP: sel.append(o)
        if o['rev']: border.append(o)
    sel.sort(key=lambda o: (o['pn'], o['n'])); border.sort(key=lambda o: o['pop'])
    assert len({o['id'] for o in sel}) == len(sel)
    json.dump({'fuente': fuente, 'umbral': MIN_POP, 'ciudades': sel, 'cercanas_al_limite': border}, open('datos/%s/ciudades.json' % cc, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(cc, len(ud['items']), 'unidades;', len(sel), 'ciudades >=', MIN_POP, '(', sum(1 for o in sel if o['big']), '>=', BIG, ');', len(border), 'en franja; sin punto:', sum(1 for o in sel if 'x' not in o))
    return {o['id']: o['n'] for o in sel}

NAMES = {}
# --- España -------------------------------------------------------------------------------------
def spain():
    g = json.load(open('tools/intermedios/es_unidades.geojson', encoding='utf-8'))['features']
    units = [{'id': f['properties']['id'], 'n': f['properties']['name'], 'geom': f['geometry']} for f in g]
    ud, proj = build_units('es', units)
    cs = json.load(open('tools/intermedios/es_ciudades.json', encoding='utf-8'))['ciudades']
    cities = [dict(id=c['id'], n=c['n'], p=c['p'], pn=c['pn'], pop=c['pop'], lon=c['lon'], lat=c['lat'], old=c.get('old')) for c in cs]  # Ceuta y Melilla: ciudades sin unidad (no son provincias)
    NAMES['es'] = {**{u['id']: u['n'] for u in ud['items']}, **write('es', ud, cities, proj, 'INE (municipios y coordenadas) + GeoNames (población, provisional)')}

# --- Francia ------------------------------------------------------------------------------------
def france():
    ne = [f for f in json.load(open(W + '/admin1.geojson', encoding='utf-8'))['features'] if f['properties']['adm0_a3'] == 'FRA']
    deps = {d['code']: d['nom'] for d in json.load(open(W + '/npm2/_etalab_decoupage-administratif/package/data/departements.json', encoding='utf-8')) if d['zone'] in ('metro', 'drom')}
    OVER = {'FR-GP': '971', 'FR-MQ': '972', 'FR-GF': '973', 'FR-RE': '974', 'FR-YT': '976'}
    units = []
    for f in ne:
        iso = f['properties']['iso_3166_2']; code = OVER.get(iso) or iso.split('-')[1]
        assert code in deps, (iso, f['properties']['name'])
        units.append({'id': code, 'n': deps[code], 'geom': f['geometry']})
    assert {u['id'] for u in units} == set(deps), set(deps) ^ {u['id'] for u in units}
    ud, proj = build_units('fr', units)
    up = {u['id']: (prep(shape(u['geom'])), shape(u['geom'])) for u in units}
    communes = [c for c in json.load(open(W + '/npm2/_etalab_decoupage-administratif/package/data/communes.json', encoding='utf-8'))
                if c.get('type') == 'commune-actuelle' and c.get('zone') in ('metro', 'drom') and c.get('population', 0) >= REVIEW[0]]
    gnc = gn_candidates('fr')
    for c in gnc: c['near'] = near_units(up, c['longitude'], c['latitude'])
    cities = []; miss = []; t2log = []
    for c in communes:
        keys = {norm(c['nom'])}
        cand = [g for g in gnc if c['departement'] in g['near'] and keys & g['keys']]
        if cand: b = max(cand, key=lambda g: g['population'])
        else:
            b = tier2(gnc, c['nom'], c['departement'], t2log)
            if not b: miss.append((c['nom'], c['population'], c['departement'])); continue
        cities.append(dict(id='c_' + c['code'], n=c['nom'], p=c['departement'], pop=c['population'], lon=b['longitude'], lat=b['latitude']))
    print('FR emparejadas por primer nombre:', t2log)
    if miss: print('FR sin coordenadas (se incluyen sin punto):', miss[:30], len(miss))
    for m in miss: pass
    for c in communes:
        if ('c_' + c['code']) not in {x['id'] for x in cities}:
            cities.append(dict(id='c_' + c['code'], n=c['nom'], p=c['departement'], pop=c['population'], lon=None, lat=None))
    NAMES['fr'] = {**{u['id']: u['n'] for u in ud['items']}, **write('fr', ud, cities, proj, 'INSEE (comunas y población, vía @etalab/decoupage-administratif) + GeoNames (coordenadas)')}

# --- Italia -------------------------------------------------------------------------------------
def italy():
    gb = json.load(open(W + '/gb/ITA-ADM3.m.geojson', encoding='utf-8'))['features']
    cm = json.load(open(W + '/npm2/comuni-json/package/comuni.json', encoding='utf-8'))
    prov = {}
    for c in cm: prov[c['provincia']['nome']] = (c['sigla'], c['provincia']['codice'])
    ALIAS = {'Aosta': "Valle d'Aosta/Vallée d'Aoste", 'Bolzano': 'Bolzano/Bozen', "Forli'-Cesena": 'Forlì-Cesena', 'Massa Carrara': 'Massa-Carrara', 'Reggio di Calabria': 'Reggio Calabria'}
    units = []
    for f in gb:
        n = f['properties']['shapeName']; n2 = ALIAS.get(n, n); assert n2 in prov, n
        units.append({'id': prov[n2][0], 'n': n2.split('/')[0] if n2 != "Valle d'Aosta/Vallée d'Aoste" else 'Aosta', 'geom': f['geometry'], 'istat': prov[n2][1]})
    assert len({u['id'] for u in units}) == 107
    ud, proj = build_units('it', units)
    up = {u['id']: (prep(shape(u['geom'])), shape(u['geom'])) for u in units}
    gnc = gn_candidates('it')
    for c in gnc: c['near'] = near_units(up, c['longitude'], c['latitude'])
    cities = []; miss = []; t2log = []
    for c in cm:
        if c['popolazione'] < REVIEW[0]: continue
        keys = {norm(c['nome'])}; sg = c['sigla']
        cand = [g for g in gnc if sg in g['near'] and keys & g['keys']]
        if cand: b = max(cand, key=lambda g: g['population'])
        else:
            b = tier2(gnc, c['nome'], sg, t2log)
            if not b: miss.append((c['nome'], c['popolazione'], sg)); continue
        cities.append(dict(id='c_' + c['codice'], n=c['nome'], p=sg, pop=c['popolazione'], lon=b['longitude'], lat=b['latitude']))
    print('IT emparejados por primer nombre:', t2log)
    if miss: print('IT sin coordenadas:', miss[:40], len(miss))
    done = {x['id'] for x in cities}
    for c in cm:
        if c['popolazione'] >= REVIEW[0] and 'c_' + c['codice'] not in done:
            cities.append(dict(id='c_' + c['codice'], n=c['nome'], p=c['sigla'], pop=c['popolazione'], lon=None, lat=None))
    NAMES['it'] = {**{u['id']: u['n'] for u in ud['items']}, **write('it', ud, cities, proj, 'ISTAT (comuni y población, vía comuni-json) + GeoNames (coordenadas)')}

# --- Grecia -------------------------------------------------------------------------------------
def greece():
    g = json.load(open(W + '/gr/grecia_unidades.geojson', encoding='utf-8'))['features']
    units = [{'id': f['properties']['id'], 'n': f['properties']['name'], 'geom': f['geometry']} for f in g]
    ud, proj = build_units('gr', units)
    up = {u['id']: (prep(shape(u['geom'])), shape(u['geom'])) for u in units}
    el = json.load(open(W + '/gr/units_en.json', encoding='utf-8'))
    munis = [(kfuzzy(m[f]), 'GR%02d' % m['regionAndUnit']['unitId'], m['name']) for m in el['munis'] for f in ('name', 'seat') if m.get(f)]
    import difflib
    cities = {}; drop = []
    for c in sorted(gn_candidates('gr'), key=lambda c: -c['population']):
        if c['population'] < REVIEW[0]: continue
        near = near_units(up, c['longitude'], c['latitude']); best = None
        for k2 in {kfuzzy(x) for x in c['keys']} | {kfuzzy(c['name'])} | ({kfuzzy('Central Corfu and Diapontia Islands')} if c['name'] == 'Corfu' else set()):
            for mk, mu, mn in munis:
                if mu in near:
                    r = difflib.SequenceMatcher(None, k2, mk).ratio()
                    if r >= 0.86 and (best is None or r > best[0]): best = (r, mu, mn)
        if not best: drop.append((c['name'], c['population'])); continue
        key = (best[1], best[2])
        if key in cities: continue
        cities[key] = dict(id='c_g%d' % c['geonameid'], n=c['name'], p=best[1], pop=c['population'], lon=c['longitude'], lat=c['latitude'])
    cities = list(cities.values())
    print('GR descartadas (no coinciden con ningún municipio o sede):', drop)
    NAMES['gr'] = {**{u['id']: u['n'] for u in ud['items']}, **write('gr', ud, cities, proj, 'GeoNames (provisional) filtrado con municipios y sedes de @tsevdos/el-utils')}

CAPITAL = {'Hatay': 'Antakya', 'Kocaeli': 'İzmit'}   # capitales de provincia con nombre distinto al de la provincia
# --- Turquía ------------------------------------------------------------------------------------
def turkey():
    ne = [f for f in json.load(open(W + '/admin1.geojson', encoding='utf-8'))['features'] if f['properties']['adm0_a3'] == 'TUR']
    gb = json.load(open(W + '/gb2/TUR-ADM1.geojson', encoding='utf-8'))['features']
    il = json.load(open(W + '/tr_ilce.json', encoding='utf-8')); pname = {c['code']: c['name'] for c in il['cities']}
    nes = [(f['properties']['iso_3166_2'].split('-')[1], shape(f['geometry'])) for f in ne]
    units = []
    for f in gb:   # geoBoundaries da los límites; el código de matrícula sale del polígono de Natural Earth que contiene su punto interior
        rp = shape(f['geometry']).representative_point(); code = next(c for c, g in nes if g.contains(rp))
        units.append({'id': code, 'n': pname[code], 'geom': f['geometry']})
    assert len({u['id'] for u in units}) == 81 == len(pname)
    ud, proj = build_units('tr', units)
    up = {u['id']: (prep(shape(u['geom'])), shape(u['geom'])) for u in units}
    official = {c: {norm(d): d for d in il['districts'][c]} for c in il['districts']}
    for c in official: official[c].setdefault(norm(pname[c]), pname[c])   # la capital de provincia lleva el nombre de la provincia
    best = {}
    for g in gn_candidates('tr'):
        if g['population'] < REVIEW[0]: continue
        pt = Point(g['longitude'], g['latitude']); near = near_units(up, g['longitude'], g['latitude'])
        for u in sorted(near, key=lambda u: 0 if up[u][0].contains(pt) else 1):
            cap = norm(pname[u])
            hit = pname[u] if cap in g['keys'] else next((official[u][k] for k in g['keys'] if k in official[u]), None)   # la capital (nombre alternativo = provincia) prima sobre el distrito
            if hit == pname[u]: hit = CAPITAL.get(hit, hit)
            if hit:
                key = (u, hit)
                if key not in best or g['population'] > best[key]['pop']: best[key] = dict(id='c_g%d' % g['geonameid'], n=hit, p=u, pop=g['population'], lon=g['longitude'], lat=g['latitude'])
                break
    cities = list(best.values())
    NAMES['tr'] = {**{u['id']: u['n'] for u in ud['items']}, **write('tr', ud, cities, proj, 'GeoNames (población, provisional) filtrado con la lista de distritos de turkey-neighbourhoods')}

# --- Macedonia del Norte -------------------------------------------------------------------------
NO_CIUDAD = {'Centar Župa', 'Lipkovo', 'Zelino', 'Tearce'}   # municipios rurales a los que GeoNames asigna población municipal
def macedonia():
    gb = json.load(open(W + '/gb2/MKD-ADM1.geojson', encoding='utf-8'))['features']
    NUTS = {'Vardar': ('MK001', 'Vardar'), 'East': ('MK002', 'Este'), 'Southwest': ('MK003', 'Suroeste'), 'Southeast': ('MK004', 'Sureste'),
            'Pelagonia': ('MK005', 'Pelagonia'), 'Polog': ('MK006', 'Polog'), 'Northeast': ('MK007', 'Noreste'), 'Skopje': ('MK008', 'Skopie')}
    units = [{'id': NUTS[f['properties']['shapeName']][0], 'n': NUTS[f['properties']['shapeName']][1], 'geom': f['geometry']} for f in gb]
    assert len(units) == 8
    ud, proj = build_units('mk', units)
    up = {u['id']: (prep(shape(u['geom'])), shape(u['geom'])) for u in units}
    gnc = gn_candidates('mk'); sk = next(g for g in gnc if g['name'] == 'Skopje')
    cities = []; drop = []
    for g in sorted(gnc, key=lambda g: -g['population']):
        if g['population'] < REVIEW[0]: continue
        if g['name'] in NO_CIUDAD: drop.append(g['name']); continue
        if g is not sk and km((g['latitude'], g['longitude']), (sk['latitude'], sk['longitude'])) < 12: drop.append(g['name']); continue   # municipios de la ciudad de Skopie
        u = locate(up, g['longitude'], g['latitude'])
        if u: cities.append(dict(id='c_g%d' % g['geonameid'], n=g['name'], p=u, pop=g['population'], lon=g['longitude'], lat=g['latitude']))
    print('MK descartadas (municipios de Skopie):', drop)
    NAMES['mk'] = {**{u['id']: u['n'] for u in ud['items']}, **write('mk', ud, cities, proj, 'GeoNames (población, provisional); Skopie sin sus municipios')}

for f in (spain, france, italy, greece, turkey, macedonia):
    f()
mundo = json.load(open('mundo.json', encoding='utf-8'))
NAMES['mundo'] = {i['id']: i['n'] for i in mundo['items']}
json.dump(NAMES, open('datos/nombres.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
