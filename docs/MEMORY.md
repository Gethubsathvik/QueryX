# 🧠 MEMORY.md - Knowledge Base & Decision Log

## 🎯 Purpose
This file serves as the project's long-term memory. It captures:
- **Architectural Decisions** (ADRs) - Why we chose X over Y
- **Gotchas & Workarounds** - Things that bit us
- **Patterns & Conventions** - Established ways of doing things
- **Context for Future Agents** - So you don't have to rediscover

---

## 🏛️ Architectural Decision Records (ADRs)

### ADR-001: MVC + Service Layer per Feature
**Date**: 2024-01-15
**Status**: Accepted
**Context**: Need clear separation for testability and microservices extraction
**Decision**: Each feature gets `controller.py` → `service.py` → `repository.py`
**Consequences**: 
- ✅ Easy to extract services for microservices
- ✅ Clear testing boundaries
- ⚠️ More boilerplate per feature
**Alternatives Considered**: Flat structure, Domain-driven design

### ADR-002: Feature-Based Folder Organization
**Date**: 2024-01-15
**Status**: Accepted
**Context**: Avoid "layer-based" folders that grow unbounded
**Decision**: `app/features/<feature>/` contains all layers
**Consequences**:
- ✅ Colocation of related code
- ✅ Easy to find everything for a feature
- ✅ Natural microservices boundaries

### ADR-003: No ORM - Raw SQL with sqlglot
**Date**: 2024-01-16
**Status**: Accepted
**Context**: Need full control over SQL for safety validation
**Decision**: Use raw SQL + sqlglot for parsing/validation
**Consequences**:
- ✅ Transparent SQL, easy to validate
- ✅ No ORM magic/hidden queries
- ⚠️ More manual mapping
- ⚠️ No migrations tool (manual schema)

### ADR-004: Defense-in-Depth SQL Safety
**Date**: 2024-01-17
**Status**: Accepted
**Context**: NL-to-SQL is inherently unsafe; must protect at multiple levels
**Decision**: 5 layers (Validator → Read-only → Authorizer → Limits → No auto-repair)
**Consequences**:
- ✅ Extremely robust
- ✅ Each layer catches different threats
- ⚠️ More code to maintain

### ADR-005: Pure Python Statistics (No NumPy/Pandas)
**Date**: 2024-01-18
**Status**: Accepted
**Context**: Android Termux support; avoid heavy deps
**Decision**: Implement KDE, PCA, ROC, Decision Tree in pure Python
**Consequences**:
- ✅ Works on Android Termux
- ✅ Zero heavy dependencies
- ✅ Educational value
- ⚠️ Slower for large datasets (not our use case)
- ⚠️ More code to maintain

### ADR-006: Bundled Plotly.js (No CDN)
**Date**: 2024-01-19
**Status**: Accepted
**Context**: Offline-first; air-gapped environments
**Decision**: Download plotly.min.js to `views/vendor/`
**Consequences**:
- ✅ Works completely offline
- ✅ No CSP issues
- ✅ Version pinned
- ⚠️ Manual updates needed

### ADR-007: Dual Monolith/Microservices from Same Codebase
**Date**: 2024-01-20
**Status**: Accepted
**Context**: Show both architectures for portfolio
**Decision**: Feature modules work in both modes via `client.py`/`internal.py`
**Consequences**:
- ✅ Single codebase, two deployment modes
- ✅ Demonstrates architectural flexibility
- ⚠️ Complexity in service extraction
- ⚠️ Internal token management

### ADR-008: Architecture Tests as Enforcement
**Date**: 2024-01-21
**Status**: Accepted
**Context**: Rules in docs get ignored; need automated enforcement
**Decision**: `tests/architecture/test_layering.py` validates imports
**Consequences**:
- ✅ Rules actually enforced
- ✅ CI catches violations
- ⚠️ Test maintenance overhead

---

## ⚠️ Gotchas & Workarounds

### GOTCHA-01: pydantic-core on Android Termux
**Issue**: `pydantic-core` requires Rust to build on ARM
**Workaround**: 
```bash
pkg install rust binutils
# OR use Option A: run on computer, access from phone
```
**Status**: Documented in README, known limitation

### GOTCHA-02: SQLite Authorizer and PRAGMA
**Issue**: Authorizer blocks `PRAGMA table_info` needed for schema introspection
**Fix**: Allow `PRAGMA` in authorizer but only for `table_info` and `index_list`
```python
if action == SQLITE_PRAGMA and arg in ("table_info", "index_list"):
    return SQLITE_OK
```

### GOTCHA-03: sqlglot Dialect for SQLite
**Issue**: sqlglot defaults to generic dialect, misses SQLite specifics
**Fix**: Always parse with `dialect="sqlite"`
```python
sqlglot.parse(sql, dialect="sqlite")
```

### GOTCHA-04: Microservices Startup Order
**Issue**: Services must start in dependency order (data before query)
**Fix**: `run_microservices.py` starts in order, waits for `/health`
```python
STARTUP_ORDER = ["data", "history", "chart", "query", "gateway"]
```

### GOTCHA-05: Internal Token in Development
**Issue**: Default token is insecure; must change for any real deployment
**Fix**: 
```bash
# .env
QUERYX_INTERNAL_TOKEN=$(openssl rand -hex 32)
```
**Note**: Start scripts warn if using default

### GOTCHA-06: Chart Builders and Missing Data
**Issue**: Some charts need specific column types (e.g., OHLC needs 4 numeric)
**Fix**: Builders return `(fig, notes)` where notes explains requirements
```python
def build_candlestick(columns, rows, mapping, options):
    if not has_ohlc_columns(columns):
        return None, "Candlestick needs: open, high, low, close columns"
    ...
```

### GOTCHA-07: Async SQLite in FastAPI
**Issue**: `sqlite3` is sync; blocks event loop
**Fix**: Run in thread pool
```python
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, sync_query, sql)
```

---

## 🔧 Established Patterns

### Pattern: Feature Client for Microservices
```python
# app/features/data/client.py
class DataClient:
    def __init__(self, base_url: str, token: str):
        self._client = httpx.AsyncClient(base_url=base_url)
        self._headers = {"X-Internal-Token": token}
    
    async def execute(self, sql: str) -> QueryResult:
        resp = await self._client.post("/internal/execute", 
            json={"sql": sql}, headers=self._headers)
        return QueryResult(**resp.json())
```

### Pattern: Service Protocol for Testing
```python
# app/features/data/service.py
class DataRepository(Protocol):
    async def query(self, sql: str) -> QueryResult: ...

class DataService:
    def __init__(self, repo: DataRepository):
        self._repo = repo
```

### Pattern: Chart Builder Registration
```python
# app/features/charts/catalog.py
CHART_BUILDERS: dict[str, ChartBuilder] = {}
CHART_METADATA: dict[str, ChartMeta] = {}

def register_chart(id: str, builder: ChartBuilder, meta: ChartMeta):
    CHART_BUILDERS[id] = builder
    CHART_METADATA[id] = meta

# In each builder file:
from .catalog import register_chart
register_chart("bar", build_bar, ChartMeta(...))
```

### Pattern: Safety Pipeline Composition
```python
# app/features/data/safety.py
class SafetyPipeline:
    def __init__(self):
        self.validators = [
            SingleStatementValidator(),
            ReadOnlyValidator(),
            KnownTablesValidator(),
            NoDangerousKeywordsValidator(),
        ]
    
    def validate(self, sql: str) -> ValidationResult:
        for v in self.validators:
            result = v.validate(sql)
            if not result.ok:
                return result
        return ValidationResult(ok=True)
```

### Pattern: Composition Root
```python
# app/main.py
def create_app() -> FastAPI:
    app = FastAPI()
    
    # Core
    config = get_config()
    token = get_internal_token()
    
    # Repositories
    data_repo = SQLiteRepository(config.data_dir)
    history_repo = HistoryRepository(config.data_dir)
    
    # Services
    data_service = DataService(data_repo, config)
    ask_service = AskService(data_service, config)
    chart_service = ChartService()
    history_service = HistoryService(history_repo)
    
    # Controllers (wire routes)
    data_router = create_data_router(data_service)
    ask_router = create_ask_router(ask_service)
    ...
    
    app.include_router(data_router)
    app.include_router(ask_router)
    ...
    
    return app
```

---

## 📝 Useful Commands Reference

### Development
```bash
# Start monolith
./scripts/start.sh          # Linux/macOS
scripts\start.bat           # Windows

# Start microservices
./scripts/start.sh micro
scripts\start.bat micro

# Manual start
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Testing
```bash
# All tests
python -m pytest

# Specific categories
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/architecture/
python -m pytest tests/charts/

# With coverage
python -m pytest --cov=app --cov-report=term-missing
```

### Evaluation
```bash
# Run evaluation (needs ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=your_key
python -m app.evaluate
```

### Docker
```bash
# Monolith
docker build -t queryx .
docker run -p 8000:8000 queryx

# Microservices
docker compose up --build
```

### Linting & Type Checking
```bash
ruff check .
ruff format .
mypy app/
```

---

## 🔑 Key Files Quick Reference

| File | Purpose |
|------|---------|
| `app/main.py` | Composition root (monolith) |
| `app/core/config.py` | All settings via Pydantic |
| `app/core/internal_token.py` | Shared secret for micro mode |
| `app/features/data/safety.py` | SQL safety pipeline |
| `app/features/charts/catalog.py` | Chart registry (40 types) |
| `scripts/run_microservices.py` | Process orchestrator |
| `docker-compose.yml` | Microservices deployment |
| `tests/architecture/test_layering.py` | Architecture enforcement |
| `eval/golden.json` | Evaluation golden set |

---

## 🎓 Lessons Learned

1. **Architecture tests are worth it** - They catch violations that code reviews miss
2. **Pure Python stats work great** - For our data sizes, performance is fine
3. **Feature-based folders scale better** - Than layer-based as project grows
4. **Dual-mode from day one** - Forces clean boundaries
5. **Bundling frontend assets** - Eliminates a whole class of deployment issues
6. **sqlglot is powerful** - But must use SQLite dialect explicitly
7. **Internal token auth is simple and effective** - For service-to-service
8. **Documentation as code** - Keep it in repo, update with features

---

## 🔮 Future Context for Agents

When working on this codebase:
- **Always run architecture tests** after changes: `pytest tests/architecture/`
- **Follow the feature pattern** for new features: controller → service → repo
- **Safety is non-negotiable** - Any SQL execution goes through `safety.py`
- **Charts are pure Python** - No numpy/pandas, implement in `builders/`
- **Test on Android Termux** if changing dependencies
- **Microservices mode** must work after any monolith change
- **Update this MEMORY.md** with new decisions and gotchas