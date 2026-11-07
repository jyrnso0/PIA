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

Verificación realizada el **6 de noviembre de 2026** en el repositorio [jyrnso0/PIA](https://github.com/jyrnso0/PIA), rama `main`. El commit de la validación más reciente es [`80c44c8`](https://github.com/jyrnso0/PIA/commit/80c44c8cee3d7adf0252771b23e143c6aeb8886c).

GitHub detectó el workflow en [`.github/workflows/ci.yml`](https://github.com/jyrnso0/PIA/blob/main/.github/workflows/ci.yml) y ejecutó [CI/CD #2](https://github.com/jyrnso0/PIA/actions/runs/42325018490) para `main`, commit `80c44c8`. Los jobs `test` (Ruff y pytest contra PostgreSQL) y `docker` (build y pruebas de Compose) finalizaron correctamente. El job `deploy` **falló** en `Validate Render URL configuration`: el log muestra `RENDER_BASE_URL` vacío. Por esa razón no se ejecutaron el deploy hook ni las comprobaciones HTTP de `/health` y `/docs`. Aunque se indicó que la variable ya estaba configurada, este run demuestra que Actions no la recibió como variable de repositorio. El workflow se está ajustando para que `deploy` ejecute sus comandos desde la raíz del workspace, sin heredar el directorio `aulaplus-pia`.

No se registró ni expuso ningún secreto. En este run no se verificó la URL pública ni se consultaron `/health` y `/docs`, porque la variable `RENDER_BASE_URL` llegó vacía al job. El host `https://aulaplus-api.onrender.com` consultado anteriormente no está confirmado como la URL pública canónica y no se usa como sustituto. No se confirma un despliegue operativo ni un resultado positivo de CD.
