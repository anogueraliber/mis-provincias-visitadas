"""Genera tools/intermedios/es_ciudades.json (PROVISIONAL) con los municipios españoles de más de 20.000 habitantes.
Fuentes: lista oficial de municipios con código INE y coordenadas (paquete npm `spanish-cities-info`, volcado a JSON)
         + población de GeoNames (paquete `geonamescache`), cruzada por nombre y cercanía.
Uso: python tools/build_ciudades.py <municipios_ine.json>      (requiere: pip install geonamescache)
Pendiente: sustituir la población por el padrón vigente del INE (ver README e issue #1)."""
import json, math, re, sys, unicodedata, geonamescache

MIN_POP = 20000
BIG = 50000
REVIEW = (17000, 23000)      # franja dudosa alrededor del umbral
MAX_KM = 25                  # distancia máx. entre el centroide del municipio y el punto de GeoNames (municipios extensos)
# Nombre oficial → nombre que usa GeoNames para su núcleo principal, cuando difieren
GN_ALIAS = {'Caravaca de la Cruz': 'Caravaca', 'Ribeira': 'Santa Uxía de Ribeira'}
RENAME = {'Gasteiz / Vitoria':'Vitoria-Gasteiz','Donostia / San Sebastián':'San Sebastián','Palma':'Palma de Mallorca',
          'Cadiz':'Cádiz','La Laguna':'San Cristóbal de La Laguna','Santa Lucía':'Santa Lucía de Tirajana','Arganda':'Arganda del Rey',
          'San Vicent del Raspeig':'San Vicente del Raspeig'}

# Nombre de GeoNames (núcleo principal) → nombre del municipio, cuando son distintos
DISPLAY = {'Sama': 'Langreo', 'Caravaca': 'Caravaca de la Cruz', 'Santa Uxía de Ribeira': 'Ribeira'}

def norm(s):
    s = unicodedata.normalize('NFD', s.lower()); s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"^(el|la|los|las|l'|els|les|a|o|os|as|sa|es|ses) ", '', s.replace("'", "' ").replace('-', ' ').strip()) if False else s
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()
def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))

munis = json.load(open(sys.argv[1], encoding='utf-8'))
prov = {f['properties']['id']: f['properties']['name'] for f in json.load(open('tools/intermedios/es_unidades.geojson', encoding='utf-8'))['features']}
prov.update({'51': 'Ceuta', '52': 'Melilla'})
gn = [c for c in geonamescache.GeonamesCache().get_cities().values() if c['countrycode'] == 'ES']
for c in gn: c['keys'] = {norm(c['name'])} | {norm(a) for a in c.get('alternatenames', []) if a}

out = []; used = set()
for m in munis:
    best = None
    k = {norm(m['name'])} | ({norm(GN_ALIAS[m['name']])} if m['name'] in GN_ALIAS else set())
    for c in gn:
        if abs(c['latitude'] - m['latitude']) > 0.4 or abs(c['longitude'] - m['longitude']) > 0.5: continue
        if not (k & c['keys']): continue
        d = km((m['latitude'], m['longitude']), (c['latitude'], c['longitude']))
        if d <= MAX_KM and (best is None or c['population'] > best['population']): best = c
    if not best or best['population'] < REVIEW[0]: continue
    used.add(best['geonameid'])
    pid = m['ineCode'][:2]
    name = DISPLAY.get(best['name']) or RENAME.get(best['name'], best['name'])
    out.append({'id': 'c_' + m['ineCode'], 'n': name, 'off': m['name'], 'p': pid, 'pn': prov[pid], 'pop': best['population'],
                'lon': round(best['longitude'], 3), 'lat': round(best['latitude'], 3), 'big': best['population'] >= BIG,
                'rev': REVIEW[0] <= best['population'] < REVIEW[1]})
# identificadores antiguos (c_<nombre>) → nuevos, para conservar marcas ya guardadas
old = json.load(open('tools/ids_antiguos.json'))
for oid, (lon, lat, p) in old.items():
    cand = [(km((lat, lon), (c['lat'], c['lon'])), c) for c in out if c['p'] == p or oid in ('c_ceuta', 'c_melilla')]
    if cand:
        d, c = min(cand, key=lambda x: x[0])
        if d < 15: c['old'] = oid
        else: print('SIN ALIAS', oid, round(d, 1))
sel = sorted((c for c in out if c['pop'] >= MIN_POP), key=lambda c: (c['pn'], c['n']))
border = sorted((c for c in out if c['rev']), key=lambda c: c['pop'])
ids = [c['id'] for c in sel]; assert len(ids) == len(set(ids))
for c in sel + border: c.pop('off', None)
json.dump({'fuente': 'INE (municipios, códigos y coordenadas) + GeoNames (población, provisional)', 'umbral': MIN_POP,
           'ciudades': sel, 'cercanas_al_limite': border}, open('tools/intermedios/es_ciudades.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(sel), 'municipios >=', MIN_POP, '|', sum(1 for c in sel if c['big']), '>=', BIG, '|', len(border), 'en franja de revisión |', sum(1 for c in sel if c.get('old')), 'con alias antiguo')
# diagnóstico: puntos GeoNames >= 20000 sin municipio asignado (posibles barrios o fallos de emparejado)
sel_gid = used
print('SIN EMPAREJAR:', '; '.join(f"{c['name']}({c['population']//1000}k)" for c in sorted(gn, key=lambda c: -c['population']) if c['population'] >= MIN_POP and c['geonameid'] not in sel_gid))
