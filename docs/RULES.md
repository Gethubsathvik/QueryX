# 📏 RULES.md - Coding & Architecture Rules

## 🏛️ Architecture Rules (Enforced by Tests)

### Layer Separation
```
✅ ALLOWED IMPORTS:
Controller → service, schemas, core.errors, core.config
Service    → repository, schemas, core, generators, external clients
Repository → schemas, core.config, sqlite3
Client     → schemas, core.config, httpx

❌ FORBIDDEN IMPORTS:
Controller → repository, generators, builders, sqlite3, plotly
Service    → controller, FastAPI, Request, Response
Repository → service, controller
Client     → service, repository
```

### Feature Module Structure (MANDATORY)
```
features/<name>/
├── controller.py    # HTTP endpoints ONLY
├── service.py       # Business logic (no HTTP deps)
├── schemas.py       # Pydantic request/response models
├── repository.py    # Data access (if needed)
├── client.py        # HTTP client for microservices
├── internal.py      # Internal endpoints (microservices)
└── domain.py        # Domain-specific logic
```

### Naming Conventions
| Element | Convention | Example |
|---------|------------|---------|
| Modules | snake_case | `query_executor.py` |
| Classes | PascalCase | `QueryExecutor` |
| Functions | snake_case | `execute_query` |
| Constants | UPPER_SNAKE | `MAX_ROWS = 500` |
| Private | _leading_underscore | `_internal_helper` |
| Type vars | PascalCase + _T | `ResponseT` |

## 🐍 Python Code Style

### Type Hints (REQUIRED)
```python
# ✅ GOOD
async def execute_query(sql: str, params: list[Any] | None = None) -> QueryResult:
    ...

# ❌ BAD
async def execute_query(sql, params=None):
    ...
```

### Async/Await
- All I/O operations **must** be async
- Use `async def` for controllers, services, repositories
- Use `httpx.AsyncClient` for HTTP calls
- Use `asyncio.gather` for parallel operations

### Error Handling
```python
# ✅ GOOD - Custom exceptions
from app.core.errors import QueryXError, ValidationError, SafetyError

raise ValidationError("Invalid SQL: multiple statements")
raise SafetyError("DDL statements not allowed")

# ❌ BAD - Generic exceptions
raise ValueError("bad")
raise Exception("error")
```

### Dependency Injection
```python
# ✅ GOOD - Protocol-based, testable
class DataRepository(Protocol):
    async def query(self, sql: str) -> QueryResult: ...

class DataService:
    def __init__(self, repo: DataRepository):
        self._repo = repo

# ❌ BAD - Hardcoded dependencies
class DataService:
    def __init__(self):
        self._repo = SQLiteRepository()  # Hard to test
```

## 🛡️ SQL Safety Rules (NON-NEGOTIABLE)

### Validator Rules (app/features/data/safety.py)
1. **Single statement only** - Reject multiple statements
2. **Read-only operations** - SELECT, WITH, UNION only
3. **Known tables only** - Reject references to unknown tables
4. **No dangerous keywords** - PRAGMA, ATTACH, DETACH, LOAD_EXTENSION
5. **No DDL/DML** - CREATE, DROP, ALTER, INSERT, UPDATE, DELETE
6. **No table-valued functions** - pragma_*, sqlite_*

### Authorizer Rules
- Only `SQLITE_SELECT` action allowed
- Tables must be in `ALLOWED_TABLES` set
- `sqlite_master` / `sqlite_temp_master` blocked
- All other actions denied

### Connection Rules
- **Always** use `mode=ro` (read-only URI)
- **Never** create writable connections
- Connection pool: max 5 connections

### Runtime Limits
```python
MAX_ROWS = 500        # Hard cap, truncation flagged
QUERY_TIMEOUT = 3.0   # Seconds, query killed
```

## 🧪 Testing Rules

### Test Organization
```
tests/
├── unit/
│   ├── features/          # Per-feature unit tests
│   │   ├── ask/
│   │   ├── data/
│   │   └── ...
│   └── core/              # Core utility tests
├── integration/
│   ├── api/               # Full API tests
│   └── database/          # DB integration tests
├── architecture/
│   ├── test_layering.py   # Enforces import rules
│   └── test_structure.py  # Enforces folder structure
└── charts/
    └── test_all_charts.py # Renders all 40 charts
```

### Test Patterns
```python
# ✅ GOOD - Descriptive names, arrange-act-assert
async def test_execute_query_returns_rows_for_valid_select():
    # Arrange
    repo = SQLiteRepository(test_db)
    service = DataService(repo)
    
    # Act
    result = await service.execute("SELECT 1 as x")
    
    # Assert
    assert result.rows == [{"x": 1}]
    assert not result.truncated

# ✅ GOOD - Parametrized for multiple cases
@pytest.mark.parametrize("sql,should_fail", [
    ("SELECT 1", False),
    ("DROP TABLE users", True),
    ("SELECT * FROM unknown", True),
])
async def test_validator_rejects_unsafe_sql(sql, should_fail):
    ...
```

### Coverage Targets
- **Critical paths** (safety, execution): 100%
- **Services**: >90%
- **Controllers**: >80%
- **Overall**: >85%

## 🔒 Security Rules

### Secrets Management
- **Never** commit secrets (.env, keys, tokens)
- Use `.env.example` for documentation
- `QUERYX_INTERNAL_TOKEN` must be set in production
- Rotate tokens periodically

### Input Validation
- All inputs validated via Pydantic schemas
- SQL validated through safety pipeline
- File uploads: CSV only, size limit 10MB
- Rate limiting: 60 req/min per IP (gateway)

### CORS
```python
# Development only
ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:8000"]
# Production: explicit domains only
```

## 📦 Dependency Rules

### Allowed Direct Dependencies
```
FastAPI, Uvicorn, Pydantic, Pydantic-Settings
SQLite3 (stdlib), sqlglot
Plotly, httpx, python-multipart
pytest, pytest-asyncio, httpx (test)
structlog, python-dotenv
```

### Forbidden Patterns
- ❌ No ORM (SQLAlchemy, etc.) - raw SQL for transparency
- ❌ No pandas/numpy in charts - pure Python stats
- ❌ No CDN dependencies - Plotly bundled in views/vendor/
- ❌ No auto-migration tools - schema managed manually

### Version Pinning
```txt
# requirements.txt - Pin major versions
fastapi>=0.109,<0.110
uvicorn>=0.27,<0.28
pydantic>=2.5,<3.0
sqlglot>=22.0,<23.0
plotly>=5.18,<6.0
```

## 📝 Documentation Rules

### Code Documentation
- **Public APIs**: Docstrings with args, returns, raises
- **Complex logic**: Inline comments explaining *why*
- **Architecture decisions**: ADR in `docs/adr/`

### README Updates
- Update when adding features
- Keep quick-start current
- Document breaking changes

## 🚀 Git Rules

### Branch Naming
```
feature/<short-description>    # New features
fix/<short-description>        # Bug fixes
refactor/<short-description>   # Code improvements
docs/<short-description>       # Documentation
```

### Commit Messages
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `security`

Example:
```
feat(charts): add waterfall chart builder

Implements waterfall chart with positive/negative segments
and running total annotation. Adds test rendering.

Closes #42
```

### PR Requirements
- All tests pass (`pytest`)
- Architecture tests pass (`pytest tests/architecture/`)
- Linting passes (`ruff check .`)
- Type checking passes (`mypy app/`)
- No architecture violations

## 🐳 Docker Rules

### Multi-stage Build
```dockerfile
# Build stage
FROM python:3.11-slim AS builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY app/ ./app/
COPY scripts/ ./scripts/
```

### Security
- Non-root user
- Read-only filesystem where possible
- No secrets in images
- `.dockerignore` excludes .env, .venv, __pycache__, tests/

## 🔄 Microservices Rules

### Service Contracts
- Each service owns its data
- Shared schemas in `app/features/*/schemas.py`
- Version via URL path: `/api/v1/...`
- Backward compatible changes only

### Communication
- Async HTTP via httpx
- Timeouts: 5s connect, 30s read
- Retries: 3x with exponential backoff
- Circuit breaker: 5 failures → 30s open

### Observability
- Structured JSON logs
- Correlation IDs passed via headers
- Health endpoint: `GET /health`
- Metrics: `GET /metrics` (future)

## ⚡ Performance Rules

### Database
- Use indexes on frequently queried columns
- `EXPLAIN QUERY PLAN` for slow queries
- Connection pooling (max 5)
- Prepared statements for repeated queries

### Caching
- Chart metadata cached at startup
- Schema introspection cached (TTL 60s)
- No query result caching (safety)

### Frontend
- Plotly.js bundled (no CDN)
- CSS/JS minified in production
- Lazy-load chart builders