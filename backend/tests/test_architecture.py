"""Enforces docs/ENGINEERING_RULES.md section 3 (layering) and section 5 (no secrets)."""
import ast
import pathlib
import re

SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "dar"
REPO = pathlib.Path(__file__).resolve().parents[2]

LAYERS = ["domain", "app", "adapters", "api"]

# layer -> internal layers it may import
ALLOWED_INTERNAL = {
    "domain": set(),
    "app": {"domain"},
    "adapters": {"domain"},
    "api": {"app", "domain"},
}
# third-party / vendor modules each inner layer must stay free of
FORBIDDEN_VENDORS = {
    "domain": {"fastapi", "httpx", "chromadb", "langchain", "langgraph", "rank_bm25", "uvicorn", "starlette"},
    "app": {"fastapi", "httpx", "chromadb", "langchain", "langgraph", "rank_bm25", "uvicorn", "starlette"},
}


def _imports(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module)
    return found


def _layer_files(layer: str):
    return [p for p in (SRC / layer).rglob("*.py")]


def test_every_layer_exists():
    for layer in LAYERS:
        assert (SRC / layer).is_dir(), f"missing layer package: dar.{layer}"


def test_layers_only_import_allowed_internal_layers():
    violations = []
    for layer in LAYERS:
        for path in _layer_files(layer):
            for module in _imports(path):
                parts = module.split(".")
                if parts[0] == "dar" and len(parts) > 1 and parts[1] in LAYERS:
                    target = parts[1]
                    if target != layer and target not in ALLOWED_INTERNAL[layer]:
                        violations.append(f"{path.name} (dar.{layer}) imports dar.{target}")
                if parts[0] == "dar" and len(parts) > 1 and parts[1] in {"main", "settings"} and layer != "api":
                    violations.append(f"{path.name} (dar.{layer}) imports dar.{parts[1]}")
    assert not violations, violations


def test_inner_layers_are_free_of_vendor_libraries():
    violations = []
    for layer, banned in FORBIDDEN_VENDORS.items():
        for path in _layer_files(layer):
            for module in _imports(path):
                if module.split(".")[0] in banned:
                    violations.append(f"{path.name} (dar.{layer}) imports {module}")
    assert not violations, violations


def test_only_settings_and_main_read_the_environment():
    violations = []
    for path in SRC.rglob("*.py"):
        if path.name in {"settings.py", "main.py"}:
            continue
        text = path.read_text(encoding="utf-8")
        if "os.environ" in text or "os.getenv" in text:
            violations.append(path.name)
    assert not violations, violations


def test_no_key_like_secrets_in_repo_root_files():
    """Root files such as .env.example, Dockerfile and docs are committed; only .env is allowed to hold a key."""
    pattern = re.compile(r"sk-or-[A-Za-z0-9\-_]{16,}|sk-[A-Za-z0-9]{32,}")
    hits = [
        p.name
        for p in REPO.iterdir()
        if p.is_file() and p.name != ".env" and pattern.search(p.read_text(encoding="utf-8", errors="ignore"))
    ]
    assert not hits, f"key-like secret found in committed file(s): {hits} (never print or commit it; keep it only in .env)"


def test_no_key_like_secrets_in_tracked_source():
    pattern = re.compile(r"sk-or-[A-Za-z0-9\-_]{16,}|sk-[A-Za-z0-9]{32,}")
    hits = []
    for root in (REPO / "backend", REPO / "docs", REPO / "scraper", REPO / "frontend"):
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".md", ".json", ".toml", ".ts", ".tsx", ".js", ".yml", ".yaml"}:
                if "node_modules" in path.parts or ".next" in path.parts:
                    continue
                if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
                    hits.append(str(path))
    assert not hits, hits
