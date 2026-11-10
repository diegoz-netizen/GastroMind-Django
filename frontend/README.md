# GastroMind — panel de administración (React + Vite)

Pantalla del **módulo de administración** de GastroMind hecha en las Semanas 09 a 11 del curso *Desarrollo de Aplicaciones Empresariales*: Insumos, Carta y Personal de la Sede Central.

Los datos están **escritos a mano** en `src/datos.js`, con la misma forma que la respuesta de la API (Semana 08). Todavía no se llama a Django ni a Spring: eso es la Semana 12.

## Instalar y ejecutar

Solo hace falta Node.js LTS (incluye npm). No necesita Django, Spring ni la base de datos.

```bash
cd frontend
npm install       # la primera vez: dependencias en node_modules/ (no se sube)
npm run dev       # http://localhost:5173/
npm run lint      # revisa el código con oxlint
npm run build     # versión de producción en dist/ (no se sube)
```

Si el puerto 5173 está ocupado (por ejemplo, por `web-react`), Vite toma el siguiente libre y lo muestra en la terminal.

## Estructura por semana

```
src/
├── main.jsx, App.jsx, App.css, index.css   entrada, menú lateral y estilos
├── datos.js         datos escritos a mano con la forma de la API (como en el PPT S10)
├── components/
│   ├── compartido/   Tarjeta.jsx
│   ├── semana09/     Carta.jsx
│   ├── semana10/     PlatilloCard, LineaReceta, EmpleadoCard, ListaEmpleados,
│   │                 RestauranteCard, PersonaItem, Personal.jsx
│   └── semana11/     PanelInsumos, ListaInsumos, InsumoCard, BuscadorInsumos,
│                     FormularioInsumo, ResumenInsumos, AvisoPanel
└── practica/        Semana 11, Parte 1 (cafetería de la guía; no se muestra en el panel)
```

| Semana | Módulo | Qué se trabaja | Archivos |
|---|---|---|---|
| 09 · Introducción a React | — | Vite, `index.html` → `main.jsx` → `App.jsx`, JSX con expresiones, `map` + `key`, condicionales | `index.html`, `main.jsx`, `semana09/Carta.jsx`, `datos.js` |
| 10 · Componentes, props, estado y eventos | Carta, Personal | Componentes por archivo, props con valor por defecto, `children`, componente dentro de componente, `useState`, `onClick`, buscador controlado, formulario con `onSubmit` y validación | `semana10/*`, `compartido/Tarjeta.jsx` |
| 11 · Comunicación entre componentes | Insumos | Estado elevado al padre (`PanelInsumos`), los hijos avisan con funciones (`onReservar`, `onEliminar`, `onGuardar`, `onCambiar`), datos derivados sin `useState`, `useEffect` con limpieza | `semana11/*`, `practica/*` |

**Compartidos:** `datos.js` lo usan las tres semanas y va en `src/` como en el curso; `Tarjeta.jsx` la usan la 10 y la 11, por eso está en `components/compartido/`. `Carta.jsx` (Semana 09) dibuja cada platillo con `PlatilloCard` de la Semana 10.

## Módulos

- **Insumos** (forma de `GET /api/catalogo/insumos/`, HU-05): indicadores (registrados, bajo el mínimo, agotados, valor del stock), lista con buscador, *Reservar* y *Eliminar*, y el formulario *Nuevo insumo* con las reglas de la API. `PanelInsumos` guarda el estado porque lo usan tres hermanos: la lista, el resumen y el buscador.
- **Carta** (forma de `GET /api/catalogo/productos/`, HU-06 a HU-08): cada platillo con su receta (1:N), su costo de insumos y la barra del % del precio.
- **Personal** (forma de `GET /api/empleados` de Spring, HU-01 y HU-03): empleados con *Activar/Desactivar* (al administrador no se le ofrece), buscador, *Registrar empleado* y el personal por sede.

Lo que se cambia en pantalla vive en el estado: al recargar vuelve a los datos de `datos.js`. *Eliminar* es para practicar `filter()`: en la API real no se borra.
