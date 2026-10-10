"""Une los municipios de Grecia (geoBoundaries ADM3, CC BY 4.0) en las 74 unidades regionales + Monte Athos.
La tabla municipio → unidad regional sale del paquete npm @tsevdos/el-utils (volcada a JSON con getAdministrativeUnits/getMunicipalities/getCities,
locale 'en', includeMountAthos). Valida cada unidad con las 51 ciudades del paquete.
Uso: python tools/build_grecia_unidades.py <units_en.json> <GRC-ADM3.geojson> <salida.geojson>   (requiere: pip install shapely)"""
import collections, difflib, json, re, sys, unicodedata
from shapely.geometry import Point, mapping, shape
from shapely.ops import unary_union

d = json.load(open(sys.argv[1], encoding='utf-8')); gbf = json.load(open(sys.argv[2], encoding='utf-8'))['features']
names = [f['properties']['shapeName'] for f in gbf]

def k(s):
    s = unicodedata.normalize('NFD', s.lower()); s = ''.join(c for c in s if not unicodedata.combining(c))
    for a, b in (('ph','f'),('y','i'),('ee','i'),('ei','i'),('oi','i'),('ou','u'),('v','b'),('kh','h'),('ch','h'),('th','t'),('dh','d')): s = s.replace(a, b)
    s = re.sub(r'[^a-z]', '', s); return re.sub(r'(is|os|as|es|us|s|i|o|a|e|u)$', '', s)
gk = {}
for n in names: gk.setdefault(k(n), []).append(n)
# Emparejados a mano (nombre del paquete → nombre en geoBoundaries): fusiones y transliteraciones distintas
MAN = {'Pangaio':'Pangeou','Abdera':'Avdiron','Velventos':'Servia-Velventos','Servia':'Servia-Velventos',
 'Central Corfu and Diapontia Islands':'Corfu','North Corfu':'Corfu','South Corfu':'Corfu','Argostoli':'Cephalonia','Lixouri':'Cephalonia','Sami':'Cephalonia',
 'Archaia Olympia':'Olympia','Kamena Vourla':'Molos-Agios Konstantinos','Aigaleo':'Egaleo','Cythera':'Kythira',
 'Loutraki - Perachora - Agioi Theodoroi':'Loutraki-Agioi Theodoroi','West Lesbos':'Lesbos','Mytilini':'Lesbos','Icaria':'Ikaria',
 'Syros - Ermoupoli':'Syros','Oropedio Lasithiou':'Lasithi Plateau','Ios':'Iiton','East Samos':'Samos','West Samos':'Samos',
 'Ilio':'Ilion','Thermo':'Thermo','Thermi':'Thermi','Irakleia':'Irakleia','Irakleio':'Irakleio','Ilida':'Ilida'}
SKIP = {'Anogeia'}  # sin polígono propio en geoBoundaries; queda dentro de otro municipio de su misma unidad (Rethymno)
unit = {u['id']: u['name'] for u in d['units']}
assign = collections.defaultdict(set)
for m in d['munis']:
    n = m['name']
    if n in SKIP: continue
    g = MAN.get(n)
    if not g:
        b = difflib.get_close_matches(k(n), list(gk), n=1, cutoff=0.82)
        if not b: raise SystemExit('Sin emparejar: ' + n)
        g = gk[b[0]][0]
    assign[g].add(m['regionAndUnit']['unitId'])
athos = [u['id'] for u in d['units'] if u['name'] == 'Mount Athos'][0]; assign['Mount Anthos'].add(athos)
conf = {g: [unit[u] for u in us] for g, us in assign.items() if len(us) > 1}
assert not conf, conf
assert all(n in assign for n in names), [n for n in names if n not in assign]
geom = collections.defaultdict(list)
for f in gbf: geom[list(assign[f['properties']['shapeName']])[0]].append(shape(f['geometry']))
U = {u: unary_union(g) for u, g in geom.items()}
assert len(U) == len(unit), [unit[u] for u in unit if u not in U]
bad = [c['name'] for c in d['cities'] if not U[c['relations']['unitId']].buffer(0.02).contains(Point(c['coordinates']))]
assert not bad, bad   # las 51 ciudades del paquete caen dentro de su unidad
feats = [{'type': 'Feature', 'properties': {'id': 'GR%02d' % u, 'name': unit[u]}, 'geometry': mapping(U[u])} for u in sorted(U)]
json.dump({'type': 'FeatureCollection', 'features': feats}, open(sys.argv[3], 'w'), ensure_ascii=False)
print(len(feats), 'unidades; ciudades de control OK:', len(d['cities']))
