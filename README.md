# Mis provincias visitadas

Aplicación web estática (HTML + GeoJSON local, sin dependencias externas) para marcar las 50 provincias españolas visitadas y las ciudades de más de 50.000 habitantes. Sin cuenta, sin GPS, sin anuncios. Ceuta y Melilla no cuentan.

## Publicar (una sola vez)
1. En GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. El workflow `.github/workflows/pages.yml` publica la web en cada push a `main`.
3. URL: `https://anogueraliber.github.io/mis-provincias-visitadas/`
4. iPhone: abrir en Safari → Compartir → **Añadir a pantalla de inicio**.

## Mapa mundial (`mundo.html`)
Segunda pantalla, enlazada desde la principal («🌍 Mapa mundial»). Estilo Visited: cada país o territorio puede estar en **Has ido**, **Quiero ir**, **Vivo** o **Vivida**, con año y notas opcionales.
- 201 países y estados (incluye Kosovo, Taiwán, Palestina, Sahara Occidental, Somalilandia y Chipre del Norte) y 57 territorios dependientes (Puerto Rico, Groenlandia…, ver `mundo.json`).
- Los diminutos (Mónaco, Vaticano, islas…) salen como puntos tocables. Zoom y desplazamiento como en el mapa de España.
- «Has ido» cuenta también Vivo y Vivida. Datos en un almacenamiento aparte (`misPaisesVisitados.v1`) y copia JSON propia.
- Fronteras de Natural Earth 1:10m (dominio público), regeneradas con `tools/build_mundo.py`. Las zonas disputadas se muestran con una de las representaciones habituales, sin valor político.

## Uso
- Pestañas **Provincias / Ciudades** en la lista. Las ciudades salen como puntos sobre el mapa (se pueden ocultar con «Mostrar ciudades»); al tocar, gana el punto más cercano al dedo. Con zoom se separan las zonas densas.
- Tocar una provincia (o su casilla en la lista) la marca/desmarca. Año y notas: botón «Detalles» o tocar en el mapa.
- Zoom: botones +/−, pellizco o rueda; arrastrar para mover.
- Los datos viven en el `localStorage` del navegador: no se sincronizan ni sobreviven al borrado de datos del sitio. Usar **Exportar copia** / **Importar copia** (JSON).

## Actualizar
Editar los archivos de este repositorio y fusionar en `main`; el workflow vuelve a publicar.
`provincias.geojson` deriva de datos públicos de límites provinciales, simplificados (~110 KB). Las claves de datos son los códigos INE de provincia (`01`–`50`).

## Pendiente: revisar la lista de ciudades con datos oficiales
`ciudades.json` es **provisional**: se generó con GeoNames (`tools/build_ciudades.py`), no con el padrón del INE.
- Las cifras de población no son las oficiales; las ciudades de 45.000–57.000 hab. pueden sobrar o faltar (hay una lista en el campo `cercanas_al_limite` de `ciudades.json`).
- Se descartaron a mano barrios y distritos que GeoNames trae como «ciudades» (Madrid, Barcelona…). Puede haber municipios de población dispersa que no aparezcan (p. ej. Siero, por confirmar).
- Para corregirlo: obtener el padrón municipal vigente del INE (ine.es) con coordenadas (Wikidata o IGN) y regenerar el archivo. Los identificadores (`c_madrid`, …) se basan en el nombre para que las copias de seguridad existentes sigan valiendo.
