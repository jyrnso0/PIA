# Validación del paquete fusionado

Fecha de ejecución: 6 de noviembre de 2026.

| Comprobación | Resultado |
|---|---|
| Ruff (`ruff check src tests scripts`) | Sin errores |
| Pruebas locales con SQLite, Python 3.13 | 101 aprobadas; cobertura de `src`: 99.19 % |
| Pruebas Docker Compose con PostgreSQL 16, Python 3.12 | 101 aprobadas; cobertura de `src`: 99.25 % |
| Umbral de cobertura solicitado | 80 %; alcanzado en ambas ejecuciones |
| Compose | Configuración validada; pruebas usan un servicio PostgreSQL separado |
| Smoke test de Compose | `/health` respondió `{"status":"ok"}`, `/docs` respondió 200 y OpenAPI expuso 35 rutas; contenedores y volumen temporal retirados |
| OpenAPI | La prueba de integración compara el contrato completo servido por la API con `docs/api/openapi.json` |
| Migración de `refund_evidence` | Prueba de actualización aditiva aprobada en SQLite |

Comandos de validación:

```powershell
.\.venv\Scripts\ruff.exe check src tests scripts
.\.venv\Scripts\python.exe -m pytest --cov=src --cov-report=term-missing --cov-fail-under=80
docker compose --profile tests run --rm tests
```

La suite emitió una advertencia deprecada de Starlette/httpx; no afectó el resultado. Esta evidencia corresponde a validaciones locales del paquete, no a una ejecución de GitHub Actions ni a un despliegue público.

## 5.3 Evidencia de CI/CD y despliegue

Verificación realizada el **6 de noviembre de 2026** en el repositorio [jyrnso0/PIA](https://github.com/jyrnso0/PIA), rama `main`, con 124 commits. El commit más reciente observado es [`5115eaf`](https://github.com/jyrnso0/PIA/commit/5115eaf37228fd25eb0dd765dbb7756b207775d7).

La consulta de GitHub Actions devolvió **0 workflows y 0 ejecuciones** para el repositorio. La página web de [Actions](https://github.com/jyrnso0/PIA/actions) mostró 404; ese resultado web, por sí solo, no permite distinguir entre una ruta no disponible y una limitación de acceso. La revisión del árbol de `main` confirmó que el archivo existente está en [`aulaplus-pia/.github/workflows/ci.yml`](https://github.com/jyrnso0/PIA/blob/main/aulaplus-pia/.github/workflows/ci.yml), no en `.github/workflows/ci.yml` en la raíz. Por tanto, no hay una ejecución verificable ni resultados de CI/CD que puedan declararse exitosos o fallidos. El archivo define pruebas, lint, Docker y un paso de despliegue condicionado a `push` en `main`; no se verificó que el despliegue se haya ejecutado.

Se verificó la URL [`https://aulaplus-api.onrender.com`](https://aulaplus-api.onrender.com). El **6 de noviembre de 2026**, `/health` y `/docs` respondieron **HTTP 503** y la página de Render indicó que la aplicación estaba cargando/despertando. En ese momento, ninguno de los dos endpoints estaba disponible; no se confirma un servicio operativo ni si el despliegue fue manual o automático. No se cuenta con una ejecución de Actions ni con respuestas saludables de los endpoints como evidencia de éxito.
