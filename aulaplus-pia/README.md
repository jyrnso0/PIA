# AulaPlus — PIA Componentes de Lógica de Negocios (Equipo 8, Caso 08)

Backend REST para conectar estudiantes con tutores y gestionar reservas, pagos, sesiones, cancelaciones, ausencias, reembolsos, disputas y métricas semanales.

El código fuente está publicado en el [repositorio GitHub del equipo](https://github.com/jyrnso0/PIA). Al 6 de noviembre de 2026, la rama `main` contiene 124 commits; el más reciente es [`5115eaf`](https://github.com/jyrnso0/PIA/commit/5115eaf37228fd25eb0dd765dbb7756b207775d7), fechado el 7 de noviembre de 2026 UTC. La ejecución de CI/CD y el despliegue público no están verificados: GitHub Actions no muestra workflows ni ejecuciones y la URL de prueba indicada en la sección de publicación responde HTTP 503.

## Requisitos

- Python 3.11 o posterior para ejecución local.
- Docker Desktop con el motor Linux/WSL 2 activo para Docker Compose.

## Ejecutar localmente en Windows

Abre PowerShell en la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m uvicorn --factory src.api.main:app_factory --reload
```

Si PowerShell bloquea la activación del entorno, ejecuta el intérprete directamente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn --factory src.api.main:app_factory --reload
```

La aplicación usa SQLite local por defecto. Swagger está en <http://localhost:8000/docs>, OpenAPI en `/openapi.json` y el health check en `/health`.

## Pruebas y lint

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=src --cov-report=term-missing --cov-fail-under=80
.\.venv\Scripts\ruff.exe check src tests scripts
```

La suite incluye pruebas unitarias, integración HTTP, persistencia, trazabilidad y paridad exacta del OpenAPI publicado con el archivo versionado. Por defecto utiliza SQLite temporal. La configuración de CI y Docker ejecuta pruebas con PostgreSQL 16. **No apuntes `TEST_DATABASE_URL` a una base con datos que quieras conservar**: el fixture recrea el esquema de esa base.

Para regenerar el contrato OpenAPI versionado después de modificar la API:

```powershell
.\.venv\Scripts\python.exe scripts/export_openapi.py
```

## Ejecutar con Docker Compose en Windows

Instala Docker Desktop, inicia el motor y comprueba que Docker y Compose respondan:

```powershell
docker --version
docker compose version
docker info
```

Si `docker info` falla, espera a que Docker Desktop termine de iniciar. Docker Desktop requiere WSL 2 para sus contenedores Linux; si no deseas instalarlo, utiliza la ejecución local con SQLite descrita arriba.

Compose toma sus valores predeterminados de `.env.example`. Crea `.env` solo si quieres personalizar variables para Compose; no se necesita copiarlo para la configuración predeterminada:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up --build
```

La API estará en <http://localhost:8000/docs>. PostgreSQL conserva los datos de desarrollo en el volumen `dbdata`. Para ejecutar la suite en una base de pruebas separada dentro del servicio PostgreSQL:

```powershell
docker compose --profile tests run --rm tests
```

Al terminar, detén la ejecución interactiva con `Ctrl+C` y luego ejecuta:

```powershell
docker compose --profile tests down
```

`down` conserva `dbdata`; no uses `down -v` si quieres preservar los datos.

No uses las credenciales de ejemplo en producción. `change_me` es solo un valor local de demostración.

## Arquitectura (DDD + hexagonal)

```text
src/domain          aggregates, Value Objects, Specification, State Machine, eventos y reglas
src/application     Service Layer, puertos y casos de uso
src/infrastructure  SQLAlchemy, repositorios, Unit of Work + outbox y pasarela simulada
src/api             FastAPI, contratos Pydantic, OpenAPI/Swagger y mapeo de errores
tests/              pruebas unitarias, integración, persistencia y trazabilidad
docs/               BRD, 20 historias Gherkin, BPMN, glosario, arquitectura/ADRs, API y entregables
```

## Roles y límites de la demo

La API demuestra autorización con el encabezado `X-Role`: solo `soporte` resuelve disputas y solo `administrador` ve el dashboard y reactiva tutores. Esto no es autenticación real. `FakePaymentGateway` simula cobros y no procesa dinero; no expongas esta demo como sistema de producción.

## CI/CD y publicación

El workflow está en `.github/workflows/ci.yml`, en la raíz del repositorio, y ejecuta lint, pruebas contra PostgreSQL, build y pruebas con Docker Compose. En pushes a `main` y ejecuciones manuales desde esa rama, solicita el despliegue en Render y verifica que `/health` y `/docs` devuelvan HTTP 2xx. Configura la variable de Actions `RENDER_BASE_URL` con la URL base pública del servicio y el secreto `RENDER_DEPLOY_HOOK` en GitHub; no publiques el valor del secreto. La ejecución falla si falta la configuración, si el hook falla o si alguno de los endpoints no responde correctamente. La existencia del workflow no implica que haya una ejecución exitosa: revisa [GitHub Actions](https://github.com/jyrnso0/PIA/actions) y el resumen de cada ejecución.

La URL `https://aulaplus-api.onrender.com` se probó el 6 de noviembre de 2026: tanto `/health` como `/docs` respondieron HTTP 503. No se puede confirmar que esa URL corresponda a un servicio activo ni afirmar que el despliegue se realizó manual o automáticamente. Configura el Blueprint de Render con `render.yaml`, verifica los dos endpoints en la URL real del servicio y actualiza esta evidencia cuando respondan correctamente.

## Documentación

| Documento | Ruta |
|---|---|
| BRD refinado | `docs/BRD.md` |
| Historias con Gherkin (20) | `docs/user_stories.md`, `docs/gherkin/` |
| Glosario | `docs/glossary.md`, `docs/glosario.md` |
| BPMN y trazabilidad (resumen en español) | `docs/BPMN.md`, `docs/architecture/trazabilidad.md` |
| BPMN adaptado, UML, estados y secuencias | `docs/architecture/diagrams/` |
| Arquitectura, patrones, SOLID y ADRs | `docs/architecture/README.md`, `docs/architecture/decision-records.md` |
| OpenAPI | `docs/api/openapi.json` (regenerable con `scripts/export_openapi.py`; UI en `/docs`) |
| Trazabilidad BR→US→código→pruebas | `docs/traceability.md`, `docs/traceability.csv` |
| Evidencias | `docs/evidence/` |
| Evidencia de validación y estado de CI/CD | `docs/evidence/Final_Validation.md` |
| Reporte de arquitectura original (PDF) | `docs/source/Architecture_Report_AulaPlus.pdf` |
| Documentos originales del equipo | `docs/source/` |
