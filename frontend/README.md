# GastroMind: panel de administración (React + Vite)

Panel web del administrador de GastroMind. Muestra y edita los datos reales del restaurante de la sede.
Usa **Django** (catálogo: insumos, platillos, categorías y reportes, puerto 8000) y **Spring Boot** (login, personal, mesas y pedidos, puerto 8080).
El login lo hace Spring y Django valida el mismo token.

## Pantallas
| Pantalla | Qué hace | API |
|---|---|---|
| Insumos | Stock, costos y mínimos; alta de insumos | Django `/insumos/` |
| Gestión de carta | Alta, edición, activar/desactivar platillos | Django `/productos/` |
| Categorías | CRUD; no se borra una categoría con platillos (409) | Django `/categorias/` |
| Recetas y costos | Receta, costo de insumos y % sobre el precio | Django `/productos/` |
| Tomar pedido | Catálogo, mesa y envío del pedido a cocina | Django `/productos/`, Spring `/mesas` y `/pedidos` |
| Personal | Empleados, registro y acceso activo/inactivo | Spring `/empleados` |

Cada rol ve lo que le toca: escribir en insumos lo hacen el administrador y el almacenero; carta, categorías y personal, solo el administrador.

## Estructura
```
src/
├── components/
│   ├── compartido/   Tarjeta (usada por los labs 09 a 11)
│   ├── semana09/     Lab 09: Carta
│   ├── semana10/     Lab 10: PlatilloCard, LineaReceta, Personal, ListaEmpleados…
│   ├── semana11/     Lab 11: PanelInsumos y sus componentes (Insumos, con estado en el padre)
│   └── semana12/     Lab 12 (Ajax): api.js, hooks.js, errores.js y las pantallas conectadas a la API
│                     (Categorias, Carta, Recetas, Personal, Pedidos, Login)
├── practica/         Lab 11 Parte 1 (catálogo con carrito), sin conectar al panel
├── datos.js          datos a mano de los Labs 09 a 11
└── ui.jsx            componentes base del diseño (botones, campos, métricas, avisos...)
```
Diseño: Figma Make "Panel de administración GastroMind", variante **Claro + vino** (DM Sans y Manrope).

## Ejecutar
Hace falta Postgres, Spring (8080) y Django (8000) encendidos (ver `docs/DESPLIEGUE.md` del repo de Spring).

```bash
cd frontend
npm install
npm run dev       # http://localhost:5174/
npm run lint
npm run build
```
