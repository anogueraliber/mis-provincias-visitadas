"""Genera mundo.json (países y territorios del mundo) desde Natural Earth 1:10m (dominio público).
Uso: python tools/build_mundo.py <ne_10m_admin_0_countries.geojson> <ne_10m_admin_0_map_units.geojson> [salida]
Proyección Miller precalculada: el navegador solo dibuja trayectos SVG."""
import json, math, sys

CTRY, UNITS = sys.argv[1], sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 else 'mundo.json'
TOL = 0.06      # simplificación (grados proyectados)
MIN_RING = 0.0009
TINY = 2.5      # dimensión máxima (grados) por debajo de la cual se añade punto tocable

# No son países ni territorios turísticos: zonas en disputa, líneas de armisticio, arrecifes, bases arrendadas...
EXCLUDE = {'BRI','CNM','KAS','SPI','BRT','BJN','SER','SCR','KAB','USG','PGA','IOA'}
# Territorios que Natural Earth agrupa dentro de otro país: se extraen de map_units
EXTRA = ['GUF','GLP','MTQ','REU','MYT','NSV','NJM','BVT','NLY','CCK','CXR','TKL']
REPLACE = {'FRA':'FXX','NOR':'NOW','NLD':'NLX'}  # versión sin sus territorios de ultramar
# Entradas «Country» de Natural Earth que son territorios dependientes; y disputadas que se tratan como países
TERRITORY = {'JEY','GGY','IMN','ALD','HKG','MAC','ABW','CUW','SXM'}
COUNTRY = {'KOS','ISR','PSX','SAH'}
RENAME = {'TWN':'Taiwán','CYN':'Chipre del Norte','FSM':'Micronesia','SWZ':'Esuatini','CZE':'Chequia','ESB':'Dekelia (base británica)','WSB':'Akrotiri (base británica)','MAF':'San Martín (Francia)','SXM':'Sint Maarten (Países Bajos)',
          'NSV':'Svalbard','NJM':'Jan Mayen','NLY':'Caribe neerlandés','PSX':'Palestina','ATA':'Antártida','FXX':'Francia'}
CONT = {'Africa':'África','Asia':'Asia','Europe':'Europa','North America':'América del Norte','South America':'América del Sur',
        'Oceania':'Oceanía','Antarctica':'Antártida','Seven seas (open ocean)':'Océanos e islas remotas'}

def miller(lon, lat):
    lat = max(-89.9, min(89.9, lat))
    return lon, math.degrees(1.25 * math.log(math.tan(math.pi / 4 + 0.4 * math.radians(lat))))

def dp(pts, t):
    if len(pts) < 3: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True; st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop(); (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy); m = -1; mi = -1
        for i in range(a + 1, b):
            x, y = pts[i]; d = math.hypot(x - x1, y - y1) if L == 0 else abs(dy * (x - x1) - dx * (y - y1)) / L
            if d > m: m, mi = d, i
        if m > t: keep[mi] = True; st += [(a, mi), (mi, b)]
    return [p for p, k in zip(pts, keep) if k]

def area(r): return abs(sum(r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1] for i in range(len(r) - 1))) / 2
def num(v): s = ('%.2f' % v).rstrip('0').rstrip('.'); return '0' if s in ('-0', '') else s

def build(f):
    g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    rings = []
    for poly in polys:
        for k, ring in enumerate(poly):
            pr = [miller(x, y) for x, y in ring]; rings.append((area(pr), k == 0, pr))
    if not rings: return None
    outer = [r for r in rings if r[1]]; big = max(outer, key=lambda r: r[0])
    d = ''; xs = []; ys = []
    for a, is_outer, pr in rings:
        if a < MIN_RING and pr is not big[2]: continue
        s = dp(pr, TOL)
        if len(s) < 4 and pr is not big[2]: continue
        if len(s) < 4: s = pr[:4] if len(pr) >= 4 else pr
        d += 'M' + 'L'.join(num(x) + ' ' + num(y) for x, y in s) + 'Z'
    bx = [p[0] for p in big[2]]; by = [p[1] for p in big[2]]
    allx = [p[0] for _, _, pr in rings for p in pr]; ally = [p[1] for _, _, pr in rings for p in pr]
    return d, (min(bx) + max(bx)) / 2, (min(by) + max(by)) / 2, max(max(allx) - min(allx), max(ally) - min(ally)), (min(allx), min(ally), max(allx), max(ally))

ctry = json.load(open(CTRY, encoding='utf-8'))['features']
units = {f['properties']['GU_A3']: f for f in json.load(open(UNITS, encoding='utf-8'))['features']}
feats = []
for f in ctry:
    a3 = f['properties']['ADM0_A3']
    if a3 in EXCLUDE: continue
    feats.append((REPLACE.get(a3, a3), units[REPLACE[a3]] if a3 in REPLACE else f, a3))
have = {x[0] for x in feats}
for a3 in EXTRA:
    if a3 not in have: feats.append((a3, units[a3], a3))
items = []; X0 = Y0 = 1e9; X1 = Y1 = -1e9
for key, f, orig in feats:
    p = f['properties']; r = build(f)
    if not r: continue
    d, cx, cy, size, bb = r
    is_country = key in REPLACE.values() or key in COUNTRY or (
        key not in EXTRA and key not in TERRITORY and p.get('TYPE') in ('Sovereign country', 'Country', 'Sovereignty'))
    name = RENAME.get(key) or RENAME.get(orig) or p.get('NAME_ES') or p['NAME']
    cont = CONT.get(p['CONTINENT'], p['CONTINENT'])
    it = {'id': key, 'n': name, 'c': cont, 't': 'p' if is_country else 't', 'd': d, 'x': round(cx, 2), 'y': round(cy, 2)}
    if size < TINY: it['tiny'] = 1
    items.append(it); X0 = min(X0, bb[0]); Y0 = min(Y0, bb[1]); X1 = max(X1, bb[2]); Y1 = max(Y1, bb[3])
ids = [i['id'] for i in items]; assert len(ids) == len(set(ids)), 'ids duplicados'
items.sort(key=lambda i: i['n'])
json.dump({'v': 1, 'box': [round(X0, 1), round(Y0, 1), round(X1, 1), round(Y1, 1)], 'items': items}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(items), 'entidades;', sum(1 for i in items if i['t'] == 'p'), 'países;', sum(1 for i in items if i['t'] == 't'), 'territorios;', sum(1 for i in items if i.get('tiny')), 'diminutos')
