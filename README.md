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

**Con Postman:** importar `docs/postman/GastroMind-Django.postman_collection.json` y ejecutar en orden. *1. Login* guarda el token solo; *2. Insumos* lista, busca, ordena y muestra que un restaurante no ve los insumos de otro (404); *3. Seguridad* prueba sin token y con token alterado (401). Spring tiene que apuntar a la misma BD que Django (`gastromind_demo`).

**Admin de Django** (`/admin/`): necesita las tablas propias de Django (`auth_*`, `django_*`). Se crean en la BD compartida con `python manage.py migrate` y después `python manage.py createsuperuser`. Las migraciones de `catalogo` **no tocan** las tablas de Spring (todas sus tablas son `managed = False`).

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

## Estado

Base creada el 12/10/2026 (Sprint 2). La API de insumos es **de solo lectura**: el alta (POST con las validaciones de CA-05) se agrega cuando el equipo confirme en la Planning que el catálogo va en Django.

## Flujo de trabajo

Igual que en el repo principal: una rama por tarea (`feature/HU-xx-...`), Pull Request a `main` con 1 aprobación de otro integrante y merge con *Create a merge commit*. `main` está protegida.

## Equipo

Diego Panez · Victor Santamaría · Piero Guevara
