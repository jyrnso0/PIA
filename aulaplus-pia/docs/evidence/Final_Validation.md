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
