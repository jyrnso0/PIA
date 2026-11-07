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

Verificación realizada el **6 de noviembre de 2026** en el repositorio [jyrnso0/PIA](https://github.com/jyrnso0/PIA), rama `main`, con 125 commits. El commit más reciente observado es [`669dbfc`](https://github.com/jyrnso0/PIA/commit/669dbfca6c2a77436d0614cfffa808c92a822a3a).

GitHub detectó el workflow en [`.github/workflows/ci.yml`](https://github.com/jyrnso0/PIA/blob/main/.github/workflows/ci.yml) y ejecutó [CI/CD #1](https://github.com/jyrnso0/PIA/actions/runs/42323563043) para `main`, commit `669dbfc`. Los jobs `test` (incluidos Ruff y pytest contra PostgreSQL) y `docker` (build y pruebas de Compose) finalizaron correctamente. El job `deploy` **falló**: el log muestra que el shell no pudo iniciar porque el directorio de trabajo `aulaplus-pia` no existía en el runner; ese job no hacía checkout del repositorio. El log también muestra `RENDER_BASE_URL` vacío. No se ejecutaron el hook ni las comprobaciones HTTP posteriores al despliegue. El workflow se corrigió localmente para añadir checkout en el job; esa corrección todavía requiere publicarse y volver a validarse. La variable de Actions `RENDER_BASE_URL` también debe configurarse con la URL base HTTPS pública.

No se registró ni expuso ningún secreto. El host `https://aulaplus-api.onrender.com`, consultado anteriormente, devolvió **HTTP 503** tanto en `/health` como en `/docs`; el intento más reciente desde este entorno agotó 25 segundos sin recibir respuesta HTTP (código `000`). No se ha confirmado que ese host sea la URL pública canónica del servicio. Los endpoints no pudieron verificarse como disponibles y no se confirma un despliegue operativo ni un resultado positivo de CD. El navegador no pudo cargar las páginas (`ERR_FAILED`), así que no hay capturas válidas de endpoints; la captura existente de Actions muestra la ejecución mientras todavía estaba en curso, no su resultado final.
