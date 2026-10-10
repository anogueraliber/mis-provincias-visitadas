# Mis lugares visitados

Aplicación web estática (HTML + JSON locales, sin dependencias externas) para llevar un registro personal de lugares visitados.
Sin cuenta, sin GPS, sin anuncios. Los datos se guardan solo en el navegador.

## Pantallas
- **🌍 Mundo** (`mundo.html`): 201 países y estados y 57 territorios. Estados: **Has ido** / **Quiero ir**, con año y notas.
- **🇪🇸 España, 🇫🇷 Francia, 🇮🇹 Italia, 🇬🇷 Grecia** (`index.html?p=es|fr|it|gr`): una sola plantilla con datos por país en `datos/<pais>/`.
  Unidades: provincias (50), *départements* (101, con los de ultramar en recuadros), provincias y ciudades metropolitanas (107) y unidades regionales (74 + Monte Athos).
  Además, las ciudades de más de 20.000 hab. (puntos en el mapa; las de 20.000–50.000 aparecen al hacer zoom).
- **Marcado automático**: marcar una ciudad marca su provincia/*département*/unidad (se ve más clara, «por ciudad»); marcar algo dentro de un país lo pasa a «Has ido» en el mundo
  (los *départements* de ultramar marcan su territorio, no Francia metropolitana). Para quitar una provincia automática hay que desmarcar sus ciudades; «Marcar también a mano» la fija.
- **Guardar / Importar copia**: un único archivo `mis-viajes.json` con todo. En el móvil abre el menú de compartir («Guardar en Archivos» → «Reemplazar»). Se importan también las copias de versiones anteriores.

## Publicar (una vez)
Settings → Pages → Source: **GitHub Actions**. El workflow `.github/workflows/pages.yml` publica en cada push a `main`.
URL: `https://anogueraliber.github.io/mis-provincias-visitadas/`. iPhone: Safari → Compartir → **Añadir a pantalla de inicio**.

## Datos y fuentes
| País | Unidades | Ciudades (>20.000 hab.) |
|---|---|---|
| Mundo | Natural Earth 1:10m (dominio público), `tools/build_mundo.py` | — |
| España | click_that_hood (límites), 50 provincias | lista de municipios del INE (`spanish-cities-info`) + población GeoNames (provisional) |
| Francia | Natural Earth admin-1 | INSEE vía `@etalab/decoupage-administratif` (Licence Ouverte); coordenadas GeoNames |
| Italia | geoBoundaries ADM3 (CC BY 4.0) | ISTAT vía `comuni-json` (CC BY 3.0 IT; **censo 2011**, lista de 2020); coordenadas GeoNames |
| Grecia | geoBoundaries ADM3 (CC BY 4.0) agrupado con la tabla de `@tsevdos/el-utils` (MIT) en 74 unidades regionales + Monte Athos | GeoNames filtrado con municipios y sedes (provisional) |

Regenerar: `python tools/build_mundo.py …`, `tools/build_ciudades_es.py`, `tools/build_grecia_unidades.py` y `tools/build_paises.py <carpeta_trabajo>` (ver la cabecera de cada script; requieren `shapely` y `geonamescache`).
La carpeta de trabajo contiene los volcados descargados: `admin1.geojson`, `gb/ITA-ADM3.m.geojson`, `gr/` (tabla de el-utils y unidades), `npm2/` (paquetes de Etalab y comuni-json) y `atc_fr_it_gr.json` (all-the-cities).
Identificadores: unidades por código oficial (INE, INSEE, sigla de provincia italiana, `GRnn`); ciudades `c_<código INE/INSEE/ISTAT>` (Grecia: `c_g<geonameid>`). Las marcas antiguas de España (`c_<nombre>`) se convierten solas.

## Pendiente: revisar las listas de ciudades con datos oficiales
Las listas son **provisionales** (ver también el issue #1):
- **España**: población de GeoNames, no del INE. Faltan municipios de población dispersa (creo que Siero, Ames, Castrillón o Piélagos superan los 20.000). Hay 134 municipios entre 17.000 y 23.000 que pueden sobrar o faltar.
- **Francia / Italia**: población oficial, pero Italia es del **censo 2011** (la lista de comuni es de 2020) y no se ha comprobado el año de la población francesa. Algunas comunas fusionadas se sitúan en su núcleo principal; unas pocas no tienen punto en el mapa (FR 2, IT 4).
- **Grecia**: ciudades de GeoNames cruzadas con municipios; falta alguno y la población no es oficial. Las unidades regionales se obtuvieron emparejando 332 municipios por nombre con geoBoundaries (se validaron con las 51 ciudades del paquete).
- Para corregirlo hace falta el padrón vigente (INE, INSEE, ISTAT, ELSTAT) o acceso a sus webs desde la sesión de trabajo.
