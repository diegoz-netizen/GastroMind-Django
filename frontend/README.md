# GastroMind — frontend (React + Vite)

Maqueta del catálogo de GastroMind hecha en los **Laboratorios 09 (Introducción a React) y 10 (Componentes y eventos)** del curso *Desarrollo de Aplicaciones Empresariales*.

Los datos están **escritos a mano** en `src/datos.js` (en el Lab 09 estaban en `App.jsx`), con la misma forma que la respuesta de la API: todavía no se llama a Django ni a Spring (eso es en la Semana 12). No reemplaza a la web oficial (`web-react` en GastroMind-SpringBoot).

## Requisitos

- Node.js LTS (incluye npm)

## Instalar y ejecutar

```bash
cd frontend
npm install       # descarga las dependencias en node_modules/ (no se sube al repo)
npm run dev       # servidor de desarrollo en http://localhost:5173/
```

Si `web-react` ya está usando el puerto 5173, Vite toma el siguiente libre (5174) y lo muestra en la terminal.

Otros comandos:

```bash
npm run lint      # revisa el código con oxlint
npm run build     # genera la versión de producción en dist/ (no se sube al repo)
```

## Qué muestra

**Parte 1 — catálogo de la Sede Central**
- **Insumos** (forma de `GET /api/catalogo/insumos/`, HU-05): costo por unidad y stock. *Agotado* si el stock es 0 y *¡Últimas unidades!* si está bajo el mínimo.
- **Platillos y su receta** (forma de `GET /api/catalogo/productos/`, HU-06 y HU-07): cada platillo con sus insumos (relación 1:N) y su **costo de insumos** calculado en JavaScript, con una barra del % del precio.

**Parte 2 — personal** (modelos `Restaurante` y `Empleado`, registrados en el Admin de Django)
- **Restaurantes** y **Empleados** (forma de `GET /api/empleados` de Spring): *Activo* / *Inactivo*, y *No puede iniciar sesión* si está inactivo.
- **Personal por restaurante**: los empleados de cada restaurante (relación 1:N) con el conteo de activos.

Si un arreglo está vacío se muestra *No hay registros*.

## Componentes (Laboratorio 10)

La interfaz del Lab 09 se reorganizó en componentes funcionales, cada uno en su archivo de `src/components`, que reciben sus datos por props. El estado y los eventos se manejan dentro del componente que los usa (pasar funciones entre componentes es de la Semana 11).

| Componente | Qué hace | Lo que trabaja |
|---|---|---|
| `Tarjeta` | Sección con título; lo de adentro llega como `children` | Composición (como `{% block %}` en los Templates de Django) |
| `InsumoCard` | Un insumo: costo, stock, *Agotado* / *¡Últimas unidades!*. *Reservar 1 kg* suma a un contador propio; se desactiva cuando lo reservado llega al stock (un insumo agotado no se puede reservar) | Props con valor por defecto (`unidad = 'kg'`), `useState`, `onClick` |
| `ListaInsumos` | Los insumos con buscador y el formulario *Nuevo insumo* | `map` + `key`, campo controlado, `onSubmit` + `preventDefault`, validación como `IngredienteSerializer` (nombre obligatorio y único, costo y stock mínimo > 0; nace con stock 0) |
| `PlatilloCard` + `LineaReceta` | Platillo con su receta (1:N) y su costo de insumos, con la barra del % del precio | Componente dentro de componente, total calculado |
| `EmpleadoCard` | Un empleado con *Activar* / *Desactivar* (solo en pantalla). Al administrador no se le ofrece (HL-008) | `useState`, `onClick`, botón desactivado según el rol |
| `ListaEmpleados` | El personal con buscador (nombre o correo) y el formulario *Registrar empleado* | Campo controlado, formulario validado como la HU-01 (nombre obligatorio, correo válido y único) |
| `RestauranteCard` + `PersonaItem` | Cada restaurante con su personal (1:N) y el conteo de activos | Componente dentro de componente |

Lo que se agrega o cambia en pantalla vive en el estado: al recargar vuelve a los datos de `src/datos.js`. Para guardarlo falta llamar a la API (`POST /api/catalogo/insumos/` en Django y `POST /api/empleados` en Spring), que es la Semana 12.

