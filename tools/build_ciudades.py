"""Genera ciudades.json (PROVISIONAL, datos GeoNames) a partir de geonamescache y provincias.geojson.
Uso: python tools/build_ciudades.py   (requiere: pip install geonamescache)
Pendiente: sustituir la población por el padrón oficial del INE (ver README)."""
import json, math, re, unicodedata, geonamescache

MIN_POP = 50000
REVIEW = (45000, 57000)  # franja dudosa: la cifra GeoNames puede diferir del INE

# Entradas de GeoNames que son barrios/distritos/núcleos y no municipios
NOT_MUNICIPALITY = {
 'Eixample','Latina','Carabanchel','Puente de Vallecas','Fuencarral','Sant Martí','Ciudad Lineal','Fuencarral-El Pardo',
 'Sants-Montjuïc','Horta-Guinardó','Nou Barris','Hortaleza','San Blas-Canillejas','Tetuán de las Victorias','Madrid Centro',
 'Arganzuela','Sarrià-Sant Gervasi','Chamberí','Sant Andreu','Usera','Chamartín','Villaverde','Retiro','Gràcia',
 'Moncloa-Aravaca','Delicias','Moratalaz','Ciutat Vella','Centro','Algorta','Les Corts','Valdefuentes','Campiña','Aluche',
 'Vicálvaro','Valverde','Villa de Vallecas','Pueblo Nuevo','Grao de Murviedro','Gamonal','Santutxu',"la Nova Esquerra de l'Eixample",
 'Barri de Sant Andreu','Vallecas','Pinar del Rey','Sagrada Família','Las Águilas','la Vila de Gràcia','Ventas','Buenavista',
 'Numancia','Vista Alegre','Sant Gervasi - Galvany','Barri de les Corts','Embajadores','el Raval','Pilar','San Diego',
}
# GeoNames 'Salamanca' aparece dos veces: el distrito de Madrid (admin1 29) y la ciudad (admin1 55)
RENAME = {'Gasteiz / Vitoria':'Vitoria-Gasteiz','Donostia / San Sebastián':'San Sebastián','Palma':'Palma de Mallorca',
 'Cadiz':'Cádiz','La Laguna':'San Cristóbal de La Laguna','Santa Lucía':'Santa Lucía de Tirajana','Arganda':'Arganda del Rey',
 'San Vicent del Raspeig':'San Vicente del Raspeig'}

def slug(s):
    s = unicodedata.normalize('NFD', s.lower()); s = ''.join(c for c in s if not unicodedata.combining(c))
    return 'c_' + re.sub(r'[^a-z0-9]+', '_', s).strip('_')

prov = json.load(open('provincias.geojson', encoding='utf-8'))['features']
def inside(pt, ring):
    x, y = pt; ins = False; j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]; xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi: ins = not ins
        j = i
    return ins
def province_of(lon, lat):
    best = None
    for f in prov:
        for poly in f['geometry']['coordinates']:
            if inside((lon, lat), poly[0]) and not any(inside((lon, lat), h) for h in poly[1:]):
                return f['properties']['id'], f['properties']['name']
            for x, y in poly[0]:
                d = math.hypot((x - lon) * 0.766, y - lat)
                if best is None or d < best[0]: best = (d, f['properties']['id'], f['properties']['name'])
    return best[1], best[2]  # punto costero fuera del polígono simplificado: provincia más cercana

out = []
for c in geonamescache.GeonamesCache().get_cities().values():
    if c['countrycode'] != 'ES' or c['population'] < REVIEW[0] or c['name'] in NOT_MUNICIPALITY: continue
    if c['name'] == 'Salamanca' and c['admin1code'] == '29': continue
    name = RENAME.get(c['name'], c['name'])
    if c['name'] == 'Melilla': pid, pn = '52', 'Melilla'
    elif c['name'] == 'Ceuta': pid, pn = '51', 'Ceuta'
    else: pid, pn = province_of(c['longitude'], c['latitude'])
    out.append({'id': slug(name), 'n': name, 'p': pid, 'pn': pn, 'pop': c['population'],
                'lon': round(c['longitude'], 3), 'lat': round(c['latitude'], 3),
                'rev': REVIEW[0] <= c['population'] < REVIEW[1], 'min': c['population'] >= MIN_POP})
ids = [o['id'] for o in out]; assert len(ids) == len(set(ids)), 'ids duplicados'
out.sort(key=lambda o: (o['pn'], o['n']))
json.dump({'fuente': 'GeoNames (provisional, pendiente de revisar con padron INE)', 'ciudades': [o for o in out if o['min']] ,
           'cercanas_al_limite': [o for o in out if o['rev']]}, open('ciudades.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len([o for o in out if o['min']]), 'ciudades >=', MIN_POP, '|', len([o for o in out if o['rev']]), 'en franja de revision')
