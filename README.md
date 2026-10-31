# GastroMind — Backend analítico (Django)

Módulo **Administración** de GastroMind: catálogo, mermas, reportes y motor de IA de compras.
Curso: *Desarrollo de Aplicaciones Empresariales (Django)*.

> Repo principal (Spring Boot + React + documentación): [diegoz-netizen/GastroMind-SpringBoot](https://github.com/diegoz-netizen/GastroMind-SpringBoot)

## Arquitectura

```
React (web-react) ──┬──▶ Spring Boot (GastroMind-SpringBoot) ── login, empleados, pedidos, stock
                    └──▶ Django (este repo)                    ── catálogo, mermas, reportes, IA
                                     │
                                     ▼
                         PostgreSQL (una sola BD compartida)
```

## Reglas para compartir la base de datos con Spring Boot

1. **La estructura de las tablas la define `docs/script_database.sql`** de GastroMind-SpringBoot. Las tablas que ya existen se mapean con modelos `managed = False` (`python manage.py inspectdb` ayuda a generarlos). **Nunca** crear migraciones que alteren tablas que usa Spring.
2. Las migraciones de Django quedan solo para sus tablas propias (`auth`, `admin`, `sessions`) o para tablas nuevas acordadas con el equipo.
3. **Login único:** el JWT lo emite Spring Boot (`POST /api/auth/login`). Django lo valida con la misma clave (HS256, claims `usuario_id` y `restaurante_id`) y rechaza al empleado que no esté `ACTIVO`.
4. **Multi-tenant:** toda consulta se filtra por el `restaurante_id` del token. El cliente nunca lo envía.
5. **Hora en UTC** (`TIME_ZONE = 'UTC'`), igual que el backend de Spring.
6. Credenciales (BD, clave JWT) por variables de entorno o un `.env` que **no se sube**.

## Cómo correrlo

Requisitos: Python 3.12+ y la BD PostgreSQL cargada con `docs/script_database.sql` + `docs/seed_demo.sql` de GastroMind-SpringBoot.

```bash
python -m venv venv
.\venv\Scripts\activate          # Windows (en Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env           # completar: misma BD y MISMO JWT_SECRET que Spring
python manage.py runserver 8000  # Spring usa 8080 y Vite 5173
```

Para probar la API hace falta un token del login de Spring:

```bash
# 1. Login en Spring (puerto 8080)
curl -X POST http://localhost:8080/api/auth/login -H "Content-Type: application/json" \
     -d '{"correo":"admin.central@gastromind.demo","password":"<clave del seed>"}'
# 2. Usar ese token en Django (puerto 8000)
curl http://localhost:8000/api/catalogo/insumos/ -H "Authorization: Bearer <token>"
```

**Con Postman:** importar `docs/postman/GastroMind-Django.postman_collection.json` y ejecutar en orden. *1. Login* guarda el token solo; *2. Insumos* lista, busca, ordena y muestra que un restaurante no ve los insumos de otro (404); *3. Registrar insumo* (HU-05) crea un insumo y prueba los 400 de CA-05 (repetido, sin unidad, costo o stock mínimo 0, LIBRE sin dotación); *4. Seguridad* prueba sin token y con token alterado (401); *6. Costo del platillo* (HU-08) revisa el costo de la carta del seed y que cambia al cambiar la receta. *5. Gestionar la carta* (HU-07) crea un platillo, prueba el precio 0 (400), lo edita, lo desactiva y comprueba que ya no sale en `?estado=ACTIVO` pero sigue en su detalle, que no se puede borrar (405), lo reactiva y que otro restaurante recibe 404. Ojo: la carpeta 3 deja un insumo `Prueba Postman ...` y la 5 un platillo `Platillo Postman ...` en la BD. Spring tiene que apuntar a la misma BD que Django (`gastromind_demo`).

**Admin de Django** (`/admin/`): necesita las tablas propias de Django (`auth_*`, `django_*`). Se crean en la BD compartida con `python manage.py migrate` y después `python manage.py createsuperuser`. Las migraciones de `catalogo` **no tocan** las tablas de Spring (todas sus tablas son `managed = False`).

## Formato de errores (HL-014)

Todos los errores de la API salen igual que en Spring Boot (`config/errores.py`):

```json
{"error": "VALIDACION", "mensaje": "Hay campos con errores.", "campos": {"nombre": "Ya existe un insumo con ese nombre en el restaurante."}}
```

| `error` | HTTP | Cuándo |
|---|---|---|
| `VALIDACION` | 400 | Datos inválidos; `campos` trae un texto por campo |
| `SOLICITUD_INVALIDA` | 400 | Cuerpo mal formado u otro 400 |
| `NO_AUTENTICADO` | 401 | Sin token, token inválido o vencido, empleado inactivo |
| `SIN_PERMISO` | 403 | El rol no puede hacer esa acción |
| `NO_ENCONTRADO` | 404 | No existe o es de otro restaurante |
| `METODO_NO_PERMITIDO` | 405 | Método no soportado en esa ruta |
| `CONFLICTO` | 409 | Choca con el estado actual |
| `ERROR_INTERNO` | 500 | Error inesperado (sin detalles internos; queda en el log) |

## Tests

```bash
python manage.py test --settings=config.settings_test
```

Usan SQLite en memoria (no necesitan PostgreSQL ni `.env`). Los tokens de prueba se arman igual que los emite Spring.

## Qué hay

| Pieza | Archivo | Tema del curso |
|---|---|---|
| Proyecto `config` y app `catalogo` | `config/`, `catalogo/` | S01–S02 |
| Modelos `managed = False` sobre `restaurante`, `rol`, `empleado`, `ingrediente` | `catalogo/models.py` | S03–S04 |
| Admin de insumos (empleados y roles en solo lectura) | `catalogo/admin.py` | S05 |
| Autenticación con el JWT de Spring + exige empleado ACTIVO | `catalogo/authentication.py` | S08 |
| `GET /api/catalogo/insumos/` (y `/{id}/`) filtrado por restaurante, con `?search=` y `?ordering=` | `catalogo/views.py`, `serializers.py`, `urls.py` | S07–S08 |
| **HU-05** `POST /api/catalogo/insumos/`: validaciones de CA-05 (nombre, unidad y costo obligatorios; costo y stock mínimo > 0; nombre único por restaurante; dotación si es `LIBRE`). Solo `ADMINISTRADOR` o `ALMACENERO` (403 al resto) | `catalogo/serializers.py`, `permissions.py`, `views.py` | S06–S08 |
| **HU-07** carta: `GET/POST /api/catalogo/productos/` (`?estado=ACTIVO` = los que salen en la toma de pedidos), `PUT/PATCH /{id}/` edita nombre, precio (> 0), categoría y receta sí/no, `PATCH /{id}/estado/` activa o desactiva. Sin `DELETE` (405): un platillo desactivado se conserva en el historial (CA-07). Escribe solo `ADMINISTRADOR` | `catalogo/views.py`, `serializers.py`, `models.py` | S07–S08 |
| **HU-08** costo del platillo: cada platillo de `/api/catalogo/productos/` trae `costo` (Σ cantidad de la receta × costo unitario del insumo, redondeado al final a 2 decimales), `margen` (precio − costo) y `porcentaje_costo` (% del precio que se va en insumos). Se calculan al vuelo, no se guardan: cambian al cambiar la receta o el costo de un insumo (CA-08). Sin receta → costo 0 | `catalogo/serializers.py` (`costo_de`), `views.py` | S07–S08 |

## Estado

Base creada el 12/10/2026 (Sprint 2). El catálogo (HU-05 a 08) va en Django (decidido el 13/10). HU-05: consulta y alta de insumos; editar y borrar no entran en este sprint.

## Flujo de trabajo

Igual que en el repo principal: una rama por tarea (`feature/HU-xx-...`), Pull Request a `main` con 1 aprobación de otro integrante y merge con *Create a merge commit*. `main` está protegida.

## Equipo

Diego Panez · Victor Santamaría · Piero Guevara

## Frontend React (Laboratorio 09)

La carpeta [`frontend/`](frontend/) tiene una **maqueta en React + Vite** del catálogo (insumos, platillos con su receta y costo) y del personal, con datos escritos a mano que tienen la misma forma que la API. Todavía no consume la API (Semana 12) y no reemplaza a `web-react` de GastroMind-SpringBoot.

```bash
cd frontend
npm install       # dependencias en node_modules/ (no se sube)
npm run dev       # http://localhost:5173/
npm run lint      # oxlint
npm run build     # versión de producción en dist/ (no se sube)
```

Detalle de lo que muestra en [`frontend/README.md`](frontend/README.md).
