"""Export the API's current OpenAPI contract to docs/api/openapi.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.api.main import create_app

output = ROOT / "docs" / "api" / "openapi.json"
output.write_text(
    json.dumps(create_app().openapi(), ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(f"OpenAPI exported to {output.relative_to(ROOT)}")
