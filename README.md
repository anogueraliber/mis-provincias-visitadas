# Mis provincias visitadas

Aplicación web estática (HTML + GeoJSON local, sin dependencias externas) para marcar las 50 provincias españolas visitadas y las ciudades de más de 50.000 habitantes. Sin cuenta, sin GPS, sin anuncios. Ceuta y Melilla no cuentan.

## Publicar (una sola vez)
1. En GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. El workflow `.github/workflows/pages.yml` publica la web en cada push a `main`.
3. URL: `https://anogueraliber.github.io/mis-provincias-visitadas/`
4. iPhone: abrir en Safari → Compartir → **Añadir a pantalla de inicio**.

## Mapa mundial (`mundo.html`)
Segunda pantalla, enlazada desde la principal («🌍 Mapa mundial»). Estilo Visited: cada país o territorio puede estar en **Has ido** o **Quiero ir**, con año y notas opcionales.
- 201 países y estados (incluye Kosovo, Taiwán, Palestina, Sahara Occidental, Somalilandia y Chipre del Norte) y 57 territorios dependientes (Puerto Rico, Groenlandia…, ver `mundo.json`).
- Los diminutos (Mónaco, Vaticano, islas…) salen como puntos tocables. Zoom y desplazamiento como en el mapa de España.
- Datos en un almacenamiento aparte (`misPaisesVisitados.v1`) y copia JSON propia.
- Fronteras de Natural Earth 1:10m (dominio público), regeneradas con `tools/build_mundo.py`. Las zonas disputadas se muestran con una de las representaciones habituales, sin valor político.

## Uso
- Pestañas **Provincias / Ciudades** en la lista. Las ciudades salen como puntos sobre el mapa (se pueden ocultar con «Mostrar ciudades»). Las de más de 50.000 hab. se ven siempre; las de 20.000–50.000 aparecen al hacer zoom (o si las has marcado). Al tocar, gana el punto más cercano al dedo. En la lista de ciudades hay filtro por tamaño.
- Tocar una provincia (o su casilla en la lista) la marca/desmarca. Año y notas: botón «Detalles» o tocar en el mapa.
- Zoom: botones +/−, pellizco o rueda; arrastrar para mover.
- Los datos viven en el `localStorage` del navegador: no se sincronizan ni sobreviven al borrado de datos del sitio. Usar **Guardar** / **Importar copia** (JSON). En el móvil, «Guardar» abre el menú de compartir: elige «Guardar en Archivos» y, si ya existe `mis-provincias.json`, pulsa «Reemplazar» (la web no puede borrar archivos por sí sola).

## Actualizar
Editar los archivos de este repositorio y fusionar en `main`; el workflow vuelve a publicar.
`provincias.geojson` deriva de datos públicos de límites provinciales, simplificados (~110 KB). Las claves de datos son los códigos INE de provincia (`01`–`50`).

## Pendiente: revisar la lista de ciudades con datos oficiales
`ciudades.json` (388 municipios de más de 20.000 hab.; 145 de ellos superan los 50.000) es **provisional**. Se genera con `tools/build_ciudades.py`:
la lista oficial de municipios (código INE y coordenadas, del paquete npm `spanish-cities-info`) cruzada por nombre y cercanía con la población de GeoNames.
- La población **no es la del padrón del INE**. Los 134 municipios entre 17.000 y 23.000 hab. (`cercanas_al_limite`) pueden sobrar o faltar.
- Faltan municipios de población dispersa, cuyo núcleo principal en GeoNames no llega a 15.000 hab. (por ejemplo, creo que Siero, Ames, Castrillón o Piélagos superan los 20.000 y no están). No se puede detectar sin el padrón.
- Algunas coordenadas son las del núcleo urbano según GeoNames, no las del término municipal.
- Para corregirlo: bajar el padrón vigente del INE (ine.es) y regenerar el archivo. Los identificadores son `c_<código INE>`; los antiguos (`c_madrid`, …) se convierten solos al abrir la app y al importar copias viejas.
