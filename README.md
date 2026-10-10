# Mis provincias visitadas

Aplicación web estática (HTML + GeoJSON local, sin dependencias externas) para marcar las 50 provincias españolas visitadas. Sin cuenta, sin GPS, sin anuncios. Ceuta y Melilla no cuentan.

## Publicar (una sola vez)
1. En GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. El workflow `.github/workflows/pages.yml` publica la web en cada push a `main`.
3. URL: `https://anogueraliber.github.io/mis-provincias-visitadas/`
4. iPhone: abrir en Safari → Compartir → **Añadir a pantalla de inicio**.

## Uso
- Tocar una provincia (o su casilla en la lista) la marca/desmarca. Año y notas: botón «Detalles» o tocar en el mapa.
- Zoom: botones +/−, pellizco o rueda; arrastrar para mover.
- Los datos viven en el `localStorage` del navegador: no se sincronizan ni sobreviven al borrado de datos del sitio. Usar **Exportar copia** / **Importar copia** (JSON).

## Actualizar
Editar los archivos de este repositorio y fusionar en `main`; el workflow vuelve a publicar.
`provincias.geojson` deriva de datos públicos de límites provinciales, simplificados (~110 KB). Las claves de datos son los códigos INE de provincia (`01`–`50`).
