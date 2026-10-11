# Mis lugares visitados

Aplicación web estática (HTML + JSON locales, sin dependencias externas) para llevar un registro personal de lugares visitados.
Sin cuenta, sin GPS, sin anuncios. Los datos se guardan solo en el navegador.

## Pantallas
- **🌍 Mundo** (`mundo.html`): 201 países y estados y 57 territorios. Estados: **Has ido** / **Quiero ir**, con año y notas.
- **🇪🇸 España, 🇫🇷 Francia, 🇮🇹 Italia, 🇬🇷 Grecia, 🇹🇷 Turquía, 🇲🇰 Macedonia del Norte** (`index.html?p=es|fr|it|gr|tr|mk`): una sola plantilla con datos por país en `datos/<pais>/`.
  Unidades: provincias (50), *départements* (101, con los de ultramar en recuadros), provincias y ciudades metropolitanas (107), unidades regionales (74 + Monte Athos), provincias turcas (81) y las 8 regiones estadísticas de Macedonia del Norte (no tiene provincias).
  Además, las ciudades de más de 10.000 hab. (puntos en el mapa: las de más de 50.000 se ven siempre, las de 20.000–50.000 con zoom y las menores con más zoom; en la lista hay filtro por tamaño).
  Ciudades por país: España 715, Francia 1.048, Italia 1.217, Grecia 123, Turquía 488, Macedonia del Norte 26.
- **Marcado automático**: marcar una ciudad marca su provincia/*département*/unidad (se ve más clara, «por ciudad»); marcar algo dentro de un país lo pasa a «Has ido» en el mundo
  (los *départements* de ultramar marcan su territorio, no Francia metropolitana). Para quitar una provincia automática hay que desmarcar sus ciudades; «Marcar también a mano» la fija.
- **Guardar / Importar copia**: un único archivo `mis-viajes.json` con todo. En el móvil abre el menú de compartir («Guardar en Archivos» → «Reemplazar»). Se importan también las copias de versiones anteriores.

## Publicar (una vez)
Settings → Pages → Source: **GitHub Actions**. El workflow `.github/workflows/pages.yml` publica en cada push a `main`.
URL: `https://anogueraliber.github.io/mis-provincias-visitadas/`. iPhone: Safari → Compartir → **Añadir a pantalla de inicio**.

## Datos y fuentes
| País | Unidades | Ciudades (>10.000 hab.) |
|---|---|---|
| Mundo | Natural Earth 1:10m (dominio público), `tools/build_mundo.py` | — |
| España | click_that_hood (límites), 50 provincias | lista de municipios del INE (`spanish-cities-info`) + población GeoNames (provisional) |
| Francia | Natural Earth admin-1 | INSEE vía `@etalab/decoupage-administratif` (Licence Ouverte); coordenadas GeoNames |
| Italia | geoBoundaries ADM3 (CC BY 4.0) | ISTAT vía `comuni-json` (CC BY 3.0 IT; **censo 2011**, lista de 2020); coordenadas GeoNames |
| Turquía | geoBoundaries ADM1 (81 provincias, CC BY 4.0); códigos de matrícula de Natural Earth | GeoNames (población, provisional) filtrado con la lista de distritos de `turkey-neighbourhoods`: capitales de provincia y distritos (los de İstanbul, Ankara o İzmir salen como ciudades separadas) |
| Macedonia del Norte | geoBoundaries ADM1 (8 regiones estadísticas, CC BY 4.0) | GeoNames (provisional); Skopie sin sus municipios |
| Grecia | geoBoundaries ADM3 (CC BY 4.0) agrupado con la tabla de `@tsevdos/el-utils` (MIT) en 74 unidades regionales + Monte Athos | GeoNames filtrado con municipios y sedes (provisional) |

Regenerar: `python tools/build_mundo.py …`, `tools/build_grecia_unidades.py` y `tools/build_paises.py <carpeta_trabajo>` (ver la cabecera de cada script; requieren `shapely` y `geonamescache`).
La carpeta de trabajo contiene los volcados descargados: `admin1.geojson`, `gb/ITA-ADM3.m.geojson`, `gb2/` (geoBoundaries ADM1 de Turquía y Macedonia), `tr_ilce.json` (volcado de `turkey-neighbourhoods`), `munis_es.json` (volcado de `spanish-cities-info`), `gr/` (tabla de el-utils y unidades), `npm2/` (paquetes de Etalab y comuni-json) y `atc_fr_it_gr.json` (all-the-cities).
Identificadores: unidades por código oficial (INE, INSEE, sigla de provincia italiana, `GRnn`); ciudades `c_<código INE/INSEE/ISTAT>` (Grecia: `c_g<geonameid>`). Las marcas antiguas de España (`c_<nombre>`) se convierten solas.

## Pendiente: revisar las listas de ciudades con datos oficiales
Las listas son **provisionales** (ver también el issue #1):
- **España**: población de GeoNames, no del INE. Faltan municipios cuyo núcleo principal es bastante menor que el municipio (con 10.000 habitantes de umbral son muchos, sobre todo en Galicia, Asturias, Cantabria y Canarias). Hay 155 entre 8.000 y 12.000 que pueden sobrar o faltar (`datos/es/limite.json`).
- **Francia / Italia**: población oficial, pero Italia es del **censo 2011** (la lista de comuni es de 2020) y no se ha comprobado el año de la población francesa. Algunas comunas fusionadas se sitúan en su núcleo principal; unas pocas no tienen punto en el mapa (FR 16, IT 20), pero salen en la lista.
- **Grecia**: ciudades de GeoNames cruzadas con municipios; falta alguno y la población no es oficial. Las unidades regionales se obtuvieron emparejando 332 municipios por nombre con geoBoundaries (se validaron con las 51 ciudades del paquete).
- **Turquía**: población de GeoNames (no oficial, posiblemente antigua); se incluyen distritos (ilçe) y capitales de provincia, no barrios; puede faltar alguno.
- **Macedonia del Norte**: solo 26 ciudades superan 10.000 según GeoNames y algunas cifras mezclan población urbana y municipal (se descartaron a mano pueblos y sedes de municipios rurales y los municipios de Skopie). Las regiones son estadísticas (8); los 80 municipios no se usan porque los datos disponibles son de antes de 2013 (84).
- Para corregirlo hace falta el padrón vigente (INE, INSEE, ISTAT, ELSTAT, TÜİK, State Statistical Office) o acceso a sus webs desde la sesión de trabajo.

Los archivos `datos/<pais>/limite.json` listan las ciudades cercanas al umbral (±2.000 hab.) para revisarlas; la app no los carga.
