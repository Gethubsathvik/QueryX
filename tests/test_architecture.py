"""Guards the layering rules described in docs/ARCHITECTURE.md and docs/RULES.md."""
from pathlib import Path

FEATURES = Path(__file__).resolve().parent.parent / "app" / "features"
NO_HTTP_FILES = {"service.py", "repository.py", "safety.py", "generators.py", "seed.py", "schemas.py"}
ROUTE_FILES = {"controller.py", "internal.py"}


def _files(names):
    return [p for p in FEATURES.rglob("*.py") if p.name in names]


def test_services_and_repositories_contain_no_http_framework_code():
    offenders = [str(p) for p in _files(NO_HTTP_FILES - {"schemas.py"}) if "fastapi" in p.read_text()]
    assert not offenders, offenders


def test_routes_are_only_declared_in_controllers():
    offenders = [str(p) for p in FEATURES.rglob("*.py")
                 if p.name not in ROUTE_FILES and "APIRouter" in p.read_text()]
    assert not offenders, offenders


def test_features_do_not_import_other_features_controllers():
    offenders = []
    for p in FEATURES.rglob("*.py"):
        text = p.read_text()
        if p.name not in ROUTE_FILES and ("from .controller" in text or "import controller" in text):
            offenders.append(str(p))
    assert not offenders, offenders


def test_every_feature_has_the_expected_layers():
    expected = {
        "ask": {"controller.py", "service.py", "schemas.py", "generators.py"},
        "data": {"controller.py", "internal.py", "service.py", "repository.py", "client.py"},
        "history": {"controller.py", "internal.py", "service.py", "repository.py", "client.py"},
        "charts": {"controller.py", "service.py", "catalog.py", "mapping.py"},
    }
    for feature, files in expected.items():
        present = {p.name for p in (FEATURES / feature).glob("*.py")}
        assert files <= present, (feature, files - present)
