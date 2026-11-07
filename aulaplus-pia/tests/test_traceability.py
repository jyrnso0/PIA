"""Garantiza que la matriz de trazabilidad no miente: cada prueba citada existe y cada BR tiene pruebas."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from traceability_data import NFR, ROWS  # noqa: E402

ROOT = Path(__file__).resolve().parent


def _existing_tests() -> set[str]:
    names = set()
    for f in ROOT.rglob("test_*.py"):
        names |= set(re.findall(r"^def (test_\w+)", f.read_text(encoding="utf-8"), flags=re.M))
    return names


def test_every_business_rule_is_covered_and_all_cited_tests_exist():
    existing = _existing_tests()
    assert [r[0] for r in ROWS] == [f"BR-{i:04d}" for i in range(1, 21)]
    for row in ROWS:
        assert row[-1], f"{row[0]} sin pruebas"
        missing = [t for t in row[-1] if t not in existing]
        assert not missing, f"{row[0]} cita pruebas inexistentes: {missing}"
    for name, _, tests in NFR:
        assert not [t for t in tests if t not in existing], name
