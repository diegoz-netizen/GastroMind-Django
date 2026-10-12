# GastroMind — Backend analítico (Django)

Módulo **Administración** de GastroMind: catálogo, mermas, reportes y motor de IA de compras.
Curso: *Desarrollo de Aplicaciones Empresariales (Django)*.

> Repo principal (Spring Boot + React + documentación): [diegoz-netizen/GastroMind](https://github.com/diegoz-netizen/GastroMind)

## Arquitectura

```
React (web-react) ──┬──▶ Spring Boot (repo GastroMind)  ── login, empleados, pedidos, stock
                    └──▶ Django (este repo)             ── catálogo, mermas, reportes, IA
                                     │
                                     ▼
                         PostgreSQL (una sola BD compartida)
```

## Reglas para compartir la base de datos con Spring Boot

1. **La estructura de las tablas la define `docs/script_database.sql`** del repo principal. Las tablas que ya existen se mapean con modelos `managed = False` (`python manage.py inspectdb` ayuda a generarlos). **Nunca** crear migraciones que alteren tablas que usa Spring.
2. Las migraciones de Django quedan solo para sus tablas propias (`auth`, `admin`, `sessions`) o para tablas nuevas acordadas con el equipo.
3. **Login único:** el JWT lo emite Spring Boot (`POST /api/auth/login`). Django lo valida con la misma clave (HS256, claims `usuario_id` y `restaurante_id`) y rechaza al empleado que no esté `ACTIVO`.
4. **Multi-tenant:** toda consulta se filtra por el `restaurante_id` del token. El cliente nunca lo envía.
5. **Hora en UTC** (`TIME_ZONE = 'UTC'`), igual que el backend de Spring.
6. Credenciales (BD, clave JWT) por variables de entorno o un `.env` que **no se sube**.

## Estado

Repo creado el 12/10/2026 (Sprint 2). El proyecto Django todavía no está inicializado.

## Flujo de trabajo

Igual que en el repo principal: una rama por tarea (`feature/HU-xx-...`), Pull Request a `main` con 1 aprobación de otro integrante y merge con *Create a merge commit*. `main` está protegida.

## Equipo

Diego Panez · Victor Santamaría · Piero Guevara
