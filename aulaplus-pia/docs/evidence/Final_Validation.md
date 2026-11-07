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

Verificación realizada el **6 de noviembre de 2026** en el repositorio [jyrnso0/PIA](https://github.com/jyrnso0/PIA), rama `main`, commit [`329f9dd`](https://github.com/jyrnso0/PIA/commit/329f9ddf150c846fb94e6137376a7085f4a37147). El workflow publicado es [`.github/workflows/ci.yml`](https://github.com/jyrnso0/PIA/blob/main/.github/workflows/ci.yml).

La ejecución manual [CI/CD #9](https://github.com/jyrnso0/PIA/actions/runs/42329635230) finalizó con **Success**. Los tres jobs pasaron:

| Job | Resultado verificado |
|---|---|
| `test` | Ruff y pytest con PostgreSQL 16 finalizaron correctamente. |
| `docker` | Se construyó la aplicación y pasaron las pruebas de Docker Compose. |
| `deploy` | Se aceptó el deploy hook de Render y las verificaciones posteriores de `/health` y `/docs` finalizaron correctamente. |

La URL pública comprobada es <https://pia-ndd7.onrender.com>. En una comprobación directa el 6 de noviembre de 2026, `/health` respondió HTTP 200 con `{"status":"ok"}` y `/docs` respondió HTTP 200. La ejecución de Actions volvió a verificar ambos endpoints después de solicitar el despliegue.

La captura del resumen exitoso, con los tres jobs en verde, está en [`CI_CD_Run_42329635230_Success.png`](CI_CD_Run_42329635230_Success.png). Las ejecuciones anteriores con errores de configuración quedan como historial y están supersedidas por el resultado exitoso #9. No se registró ni expuso ningún secreto.
