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

## Despliegue

Este repo trae su `Dockerfile` (Python 3.12, servidor de desarrollo en el puerto 8000). **No se despliega solo:** necesita la base PostgreSQL y el mismo `JWT_SECRET` que Spring, así que se levanta junto con los demás servicios desde el `docker-compose.yml` del repo de Spring:

```bash
# con este repo clonado al lado de GastroMind-SpringBoot
cd ../GastroMind-SpringBoot
cp .env.example .env        # completar DB_PASSWORD, JWT_SECRET y DJANGO_SECRET_KEY
docker compose up --build -d
```

Guía completa (variables, comprobación y problemas comunes): [`docs/DESPLIEGUE.md`](https://github.com/diegoz-netizen/GastroMind-SpringBoot/blob/main/docs/DESPLIEGUE.md) del repo de Spring.

Variables que lee este servicio (están en `.env.example`): `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `JWT_SECRET` y `CORS_ALLOWED_ORIGINS`.

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

Los reportes tienen un test por HU (`catalogo/test_reportes_<tema>.py`) sobre la misma base de datos de prueba (`test_reportes_base.py`: restaurante, insumos, pedidos servidos y movimientos con fecha fija).

## Qué hay

| Pieza | Archivo | Tema del curso |
|---|---|---|
| Proyecto `config` y app `catalogo` | `config/`, `catalogo/` | S01–S02 |
| Modelos `managed = False` sobre `restaurante`, `rol`, `empleado`, `ingrediente` | `catalogo/models.py` | S03–S04 |
| Admin de insumos (empleados y roles en solo lectura) | `catalogo/admin.py` | S05 |
| Autenticación con el JWT de Spring + exige empleado ACTIVO | `catalogo/authentication.py` | S08 |
| `GET /api/catalogo/insumos/` (y `/{id}/`) filtrado por restaurante, con `?search=` y `?ordering=` | `catalogo/views.py`, `serializers.py`, `urls.py` | S07–S08 |
| **HU-05** `POST /api/catalogo/insumos/`: validaciones de CA-05 (nombre, unidad y costo obligatorios; costo y stock mínimo > 0; nombre único por restaurante; dotación si es `LIBRE`). Solo `ADMINISTRADOR` o `ALMACENERO` (403 al resto) | `catalogo/serializers.py`, `permissions.py`, `views.py` | S06–S08 |
| **HU-25** `PATCH /api/catalogo/insumos/{id}/clasificacion/`: `RECETA` o `LIBRE`; `LIBRE` exige cantidad y periodo de dotación, y `RECETA` la borra. Solo `ADMINISTRADOR` (403 al resto). No toca stock ni costo. El conteo cíclico va con la HU-30 | `catalogo/serializers.py`, `views.py` | S4 |
| **HU-07** carta: `GET/POST /api/catalogo/productos/` (`?estado=ACTIVO` = los que salen en la toma de pedidos), `PUT/PATCH /{id}/` edita nombre, precio (> 0), categoría y receta sí/no, `PATCH /{id}/estado/` activa o desactiva. Sin `DELETE` (405): un platillo desactivado se conserva en el historial (CA-07). Escribe solo `ADMINISTRADOR` | `catalogo/views.py`, `serializers.py`, `models.py` | S07–S08 |
| **HU-08** costo del platillo: cada platillo de `/api/catalogo/productos/` trae `costo` (Σ cantidad de la receta × costo unitario del insumo, redondeado al final a 2 decimales), `margen` (precio − costo) y `porcentaje_costo` (% del precio que se va en insumos). Se calculan al vuelo, no se guardan: cambian al cambiar la receta o el costo de un insumo (CA-08). Sin receta → costo 0 | `catalogo/serializers.py` (`costo_de`), `views.py` | S07–S08 |
| **Reportes del gerente (base):** todo cuelga de `/api/catalogo/reportes/` y es solo para `ADMINISTRADOR` (403 al resto). Cada reporte acepta `?desde=` y `?hasta=` (AAAA-MM-DD, días de Perú, los dos incluidos); sin ellos va del 1 del mes en curso a hoy. Ventas = platillos `SERVIDO`; costo y merma = salidas `CONSUMO` y `MERMA` del inventario, valorizadas | `catalogo/reportes/comun.py`, `urls.py`, `catalogo/permissions.py` (`EsAdmin`) | S4 |
| **HU-20** `GET reportes/consumo/`: por insumo `RECETA`, consumo teórico (platillos servidos × receta) contra real (`CONSUMO` + `MERMA`, más lo que faltó en el último conteo físico del periodo, HU-30). Trae diferencia y %, y marca `resaltar` si se desvía más de 5 %. Los insumos `LIBRE` no entran: van por dotación y conteo | `catalogo/reportes/consumo.py` | S4 |
| **HU-23** `GET reportes/panel/`: ventas, costo de insumos, merma y margen bruto del periodo, en soles y en % de las ventas, contra el periodo anterior del mismo largo. Trae también las ventas y el costo por semana y los 5 platillos más vendidos con su % de costo | `catalogo/reportes/panel.py` | S4 |
| **HU-22** `/api/catalogo/proveedores/`: el gerente registra proveedores (`POST`, `PATCH`; no se borran) y con `POST {id}/precios/` el precio de cada insumo, su tiempo de entrega y el flete (si ya había uno, se reemplaza). `GET reportes/proveedores/?insumo=&cantidad=` ordena los proveedores del insumo por costo total (precio × cantidad + flete) y marca el `sugerido` (CA-22); `opciones_de()` es la que usa la HU-21. Solo `ADMINISTRADOR`. En el Admin, el proveedor con sus precios en un Inline. Necesita la migración `008` (Spring) | `catalogo/views.py`, `catalogo/reportes/proveedores.py`, `admin.py` | S4 |
| **HU-24** `GET reportes/exportar/?tipo=`: baja en Excel (`.xlsx`, con `openpyxl`) el reporte de `merma` (mismos filtros de la HU-19: periodo, `insumo` y `motivo`), de `consumo` (teórico vs. real, HU-20) o de `inventario` (stock de hoy con su mínimo y valor). Los números salen de las mismas funciones que la pantalla, y cada archivo trae arriba el restaurante, el periodo y los filtros. Tipo desconocido o filtro de otro restaurante → 400. Solo `ADMINISTRADOR` | `catalogo/reportes/exportar.py` | S4 |

## Estado

Base creada el 12/10/2026 (Sprint 2). El catálogo (HU-05 a 08) va en Django (decidido el 13/10). HU-05: consulta y alta de insumos; editar y borrar no entran en este sprint.

**Sprint 4 (desde el 6/11): reportes del gerente.** Van en el paquete `catalogo/reportes/`, un archivo por HU (HU-19 a HU-24), para que dos HU no choquen al mergear. Cada una suma su ruta en `catalogo/reportes/urls.py` y su pestaña en la web (`web-react/src/components/reportes/` del repo GastroMind). El reporte de la HU-20 suma los conteos físicos (HU-30): necesita la migración `009` del repo GastroMind en la BD.

## Flujo de trabajo

Igual que en el repo principal: una rama por tarea (`feature/HU-xx-...`), Pull Request a `main` con 1 aprobación de otro integrante y merge con *Create a merge commit*. `main` está protegida.

## Equipo

Diego Panez · Victor Santamaría · Piero Guevara
