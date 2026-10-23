# GastroMind — frontend (React + Vite)

Maqueta del catálogo de GastroMind hecha en el **Laboratorio 09 (Introducción a React)** del curso *Desarrollo de Aplicaciones Empresariales*.

Los datos están **escritos a mano** en `src/App.jsx`, con la misma forma que la respuesta de la API: todavía no se llama a Django ni a Spring (eso es en la Semana 12). No reemplaza a la web oficial (`web-react` en GastroMind-SpringBoot).

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
