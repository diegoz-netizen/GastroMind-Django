# Rediseño del panel Django (propuesta de Figma Make, en verde)

Prototipo navegable para ver cómo podría verse el panel de `frontend/`. **No cambia nada del código del panel ni del backend**: es una propuesta aparte (Vite + React) para decidir qué se adopta antes de llevarla a `frontend/` por HU.

## Cómo verlo
```bash
cd docs/diseno-panel-v1
npm install
npm run dev
```
Entra con cualquier correo válido y cualquier contraseña (acceso local de presentación). Los datos son de ejemplo y se guardan en el navegador.

## Qué trae
Ingreso, y un panel de escritorio con menú lateral (hamburguesa en pantallas chicas) con: Gestión de carta, Categorías, Insumos, Recetas y costos, Personal y Tomar pedido. Modo claro, oscuro y automático.

## Color
Verde único (`#174e3b` en claro, `#24684f` en oscuro). Se quitó el selector de variantes A/B que traía el diseño original (la B era vino).

## Qué se cambió respecto al zip original
Solo el selector A/B y el color de la variante B; además `vite.config.ts` (el de Make importaba archivos que no vienen en el zip), el título del `index.html` y el nombre del paquete.

## Qué se hace con esto
Si se elige este diseño, se lleva a `frontend/` por HU y se revisa pantalla por pantalla contra lo que ya existe (Insumos, Carta, Recetas y Personal se cruzan con la web de Spring Boot). Si algo no convence, se anota en el PR.
