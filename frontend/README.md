# GastroMind: panel de administración (React + Vite)

Panel web del administrador de GastroMind. Muestra y edita los datos reales del restaurante de la sede.
Usa **Django** (catálogo: insumos, platillos, categorías y reportes, puerto 8000) y **Spring Boot** (login, personal, mesas y pedidos, puerto 8080).
El login lo hace Spring y Django valida el mismo token.

## Pantallas
| Pantalla | Qué hace | API |
|---|---|---|
| Insumos | Stock, costos y mínimos; alta de insumos. La búsqueda y el filtro viajan a la API | Django `/insumos/?search=&ordering=` y `/insumos/stock-bajo/` |
| Gestión de carta | Alta, edición, activar/desactivar platillos | Django `/productos/` |
| Categorías | CRUD; no se borra una categoría con platillos (409) | Django `/categorias/` |
| Recetas y costos | Receta, costo de insumos y % sobre el precio | Django `/productos/` |
| Tomar pedido | Catálogo, mesa y envío del pedido a cocina | Django `/productos/`, Spring `/mesas` y `/pedidos` |
| Personal | Empleados, registro y acceso activo/inactivo | Spring `/empleados` |
| Práctica Lab 12 | Lab 12 Parte 1: listar, buscar, crear, renombrar y eliminar categorías | Django `/categorias/?search=` |

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
├── practica/         Lab 11 Parte 1 (catálogo con carrito, sin conectar al panel)
│                     y Lab 12 Parte 1: ListaPractica.jsx (GET, POST, PATCH, DELETE y ?search=)
├── api.js            Lab 12 Parte 1: instancia de Axios (baseURL y timeout) que usa src/practica
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

## Django y React a la vez (Lab 12)
Son dos aplicaciones distintas que se hablan por HTTP. Se encienden en dos terminales:

```bash
# Terminal 1: la API (desde la raíz del repo, con el venv activo)
python manage.py runserver        # http://127.0.0.1:8000/api/catalogo/

# Terminal 2: el panel
cd frontend
npm run dev                       # http://localhost:5174/
```
El login lo hace Spring (8080), así que también tiene que estar encendido.

**CORS.** El navegador bloquea las peticiones de `localhost:5174` a `127.0.0.1:8000` si Django no lo permite.
Django usa `django-cors-headers` (`corsheaders` en `INSTALLED_APPS` y `CorsMiddleware` arriba en `MIDDLEWARE`)
y lee los orígenes permitidos de `CORS_ALLOWED_ORIGINS` en el `.env`. Para el panel:

```
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174
```
Spring necesita lo mismo en `gastromind.cors.allowed-origins` (en `application-local.properties`, que no se sube).

### Endpoints que usa el panel
| Método | URL | Respuesta |
|---|---|---|
| GET | `/api/catalogo/insumos/?search=&ordering=` | 200 |
| GET | `/api/catalogo/insumos/stock-bajo/?search=&ordering=` | 200 |
| POST | `/api/catalogo/insumos/` | 201 · 400 (validación del serializer) |
| GET | `/api/catalogo/categorias/?search=&ordering=` | 200 |
| POST · PATCH | `/api/catalogo/categorias/` · `/api/catalogo/categorias/{id}/` | 201 · 200 · 400 (nombre vacío o repetido) |
| DELETE | `/api/catalogo/categorias/{id}/` | 204 · 404 · 409 (tiene platillos) |
| GET · POST · PATCH | `/api/catalogo/productos/` y `/api/catalogo/productos/{id}/estado/` | 200 · 201 · 400 · 404 |
| POST | Spring `/api/auth/login` | 200 con el token |
