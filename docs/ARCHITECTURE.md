# 🏗️ ARCHITECTURE.md - Detailed Architecture Documentation

## 🎯 Architectural Goals
1. **Separation of Concerns** - MVC + Service layer per feature
2. **Testability** - Each layer independently testable
3. **Extensibility** - New features follow same pattern
4. **Dual-mode** - Monolith and microservices from same codebase
5. **Safety First** - Defense-in-depth SQL protection

## 📁 Project Structure

```
QueryX/
├── app/                          # Main application (monolith)
│   ├── core/                     # Cross-cutting concerns
│   │   ├── config.py             # Settings via pydantic-settings
│   │   ├── errors.py             # Custom exceptions + handlers
│   │   └── internal_token.py     # Shared secret for micro mode
│   ├── features/                 # Feature-based modules
│   │   ├── ask/                  # Natural language → SQL
│   │   │   ├── controller.py     # HTTP endpoints
│   │   │   ├── service.py        # Use case orchestration
│   │   │   ├── generators.py     # LLM + demo engines
│   │   │   └── schemas.py        # Pydantic models
│   │   ├── data/                 # Query execution + safety
│   │   │   ├── controller.py
│   │   │   ├── service.py
│   │   │   ├── repository.py     # SQLite access
│   │   │   ├── safety.py         # sqlglot validator + authorizer
│   │   │   ├── seed.py           # Demo data
│   │   │   ├── client.py         # HTTP client (micro mode)
│   │   │   └── internal.py       # Internal endpoints
│   │   ├── history/              # Query history
│   │   │   ├── controller.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── client.py
│   │   │   └── internal.py
│   │   ├── charts/               # 40 chart types
│   │   │   ├── controller.py
│   │   │   ├── service.py
│   │   │   ├── catalog.py        # Chart metadata
│   │   │   ├── mapping.py        # Column → encoding
│   │   │   ├── builders/         # 40 figure builders
│   │   │   ├── stats.py          # KDE, PCA, ROC, tree, control
│   │   │   └── tree.py           # Decision tree viz
│   │   └── evaluation/           # Execution accuracy
│   │       └── service.py
│   ├── views/                    # Static frontend (V in MVC)
│   │   ├── index.html
│   │   ├── app.css
│   │   ├── app.js
│   │   └── vendor/plotly.min.js  # Bundled, no CDN
│   └── main.py                   # Composition root
├── services/                     # Microservices (extracted from features)
│   ├── gateway/                  # API Gateway (port 8000)
│   ├── query/                    # Ask service (port 8001)
│   ├── data/                     # Data service (port 8002)
│   ├── history/                  # History service (port 8003)
│   └── chart/                    # Chart service (port 8004)
├── scripts/                      # Launch scripts
│   ├── start.sh                  # Linux/macOS/Android
│   ├── start.bat                 # Windows
│   └── run_microservices.py      # Process orchestrator
├── tests/                        # 115+ tests
│   ├── unit/                     # Unit tests per layer
│   ├── integration/              # API + DB tests
│   ├── architecture/             # Layering rule enforcement
│   └── charts/                   # All 40 chart render tests
├── eval/                         # Evaluation harness
│   ├── golden.json               # Question + reference SQL pairs
│   └── runner.py
├── data/                         # SQLite databases (gitignored)
├── sample_data/                  # Demo CSVs
├── docs/                         # Additional docs
│   └── USER_GUIDE.md
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🔄 Request Flow (Monolith)

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌────────────────┐
│   Browser   │────▶│  Controller  │────▶│   Service   │────▶│  Repository/   │
│  (index.html)│    │  (HTTP only) │    │ (Business   │    │  Generator     │
└─────────────┘     └──────────────┘     │  Logic)     │     └────────────────┘
                                          └──────┬──────┘
                                                 │
                    ┌────────────────────────────┼────────────────────────────┐
                    ▼                            ▼                            ▼
             ┌─────────────┐             ┌──────────────┐             ┌─────────────┐
             │  SQL Gen    │             │  Validator   │             │  Executor   │
             │ (LLM/Demo)  │             │  (sqlglot)   │             │ (SQLite ro) │
             └─────────────┘             └──────────────┘             └─────────────┘
                    │                            │                            │
                    └────────────────────────────┼────────────────────────────┘
                                                 ▼
                                          ┌─────────────┐
                                          │  Results +  │
                                          │  Chart Sug  │
                                          └─────────────┘
```

## 🔄 Request Flow (Microservices)

```
┌─────────┐     ┌──────────┐     ┌────────────┐     ┌────────────┐
│ Browser │────▶│ Gateway  │────▶│  Query Svc │────▶│  Data Svc  │
│         │     │ :8000    │     │  :8001     │     │  :8002     │
└─────────┘     └──────────┘     └────────────┘     └────────────┘
                      │                                       │
                      │              ┌────────────┐           │
                      └─────────────▶│ History Svc│◀──────────┘
                                     │  :8003     │
                                     └────────────┘
                      │                                       │
                      └───────────────────────────────────────┘
                                                  │
                                          ┌───────▼───────┐
                                          │  Chart Svc    │
                                          │    :8004      │
                                          └───────────────┘
```

## 🔐 Security Model

### Internal Token Authentication
```python
# app/core/internal_token.py
INTERNAL_TOKEN = os.getenv("QUERYX_INTERNAL_TOKEN", "dev-token-change-in-prod")

# Header: X-Internal-Token: <token>
# Validated on every /internal/* request
```

### Service-to-Service Communication
- Gateway proxies public `/api/*` routes
- Services expose `/internal/*` for inter-service calls
- `/internal/*` **never** exposed publicly
- Token validated by middleware in each service

### SQL Safety Layers (Defense in Depth)
```
Layer 1: AST Validator (sqlglot)
  ├── Single statement only
  ├── SELECT/WITH/UNION only
  ├── Known tables only
  ├── No PRAGMA/ATTACH/DDL/DML
  ├── No load_extension
  └── No table-valued functions

Layer 2: Read-Only Connection
  └── sqlite3.connect(uri, mode=ro)

Layer 3: SQLite Authorizer
  ├── Only SELECT allowed
  ├── Allow-listed tables only
  └── sqlite_master blocked

Layer 4: Runtime Limits
  ├── 500 row cap (truncation flagged)
  └── 3 second timeout (query killed)
```

## 🎨 Chart Architecture

### Builder Pattern
```python
# app/features/charts/builders/bar.py
def build_bar(columns, rows, mapping, options) -> go.Figure:
    # Pure Python, no external deps beyond plotly
    fig = go.Figure()
    # ... build logic
    return fig
```

### Registry System
```python
# app/features/charts/catalog.py
CHART_BUILDERS = {
    "bar": build_bar,
    "line": build_line,
    # ... 40 types
}

CHART_METADATA = {
    "bar": ChartMeta(
        category="compare",
        required_encodings=["x", "y"],
        optional_encodings=["color", "facet"],
        options=["stacked", "horizontal"],
        example_sql="SELECT category, SUM(value) FROM sales GROUP BY category",
    ),
    # ...
}
```

### Pure Python Statistics
- **KDE**: Gaussian kernel, Silverman bandwidth
- **PCA**: Power iteration for eigenvalues
- **ROC/PR**: Trapezoidal integration
- **Decision Tree**: Recursive splitting (Gini)
- **Control Chart**: I-MR with 3-sigma limits

## 🧩 Feature Module Contract

Each feature **MUST** follow this structure:
```
feature_name/
├── controller.py    # HTTP layer ONLY
├── service.py       # Business logic (no HTTP)
├── repository.py    # Data access (optional)
├── schemas.py       # Pydantic models
├── client.py        # HTTP client for micro mode
├── internal.py      # Internal endpoints (micro mode)
└── *.py             # Domain-specific modules
```

### Layer Rules (Enforced by Tests)
| Layer | Can Import | Cannot Import |
|-------|------------|---------------|
| Controller | service, schemas, core | repository, generators, builders |
| Service | repository, schemas, core, generators | controller, FastAPI |
| Repository | schemas, core | controller, service |
| Client | schemas, core | service, repository |

## ⚙️ Configuration

### Environment Variables
```bash
# Core
ANTHROPIC_API_KEY=              # Enable LLM
QUERYX_MODEL=claude-sonnet-5-5  # Model name
QUERYX_ENGINE=demo              # Force demo engine

# Server
QUERYX_HOST=127.0.0.1
QUERYX_PORT=8000

# Data
QUERYX_DATA_DIR=./data
QUERYX_MAX_ROWS=500
QUERYX_QUERY_TIMEOUT=3

# Microservices
QUERYX_INTERNAL_TOKEN=super-secret-change-me
QUERYX_GATEWAY_URL=http://localhost:8000
QUERYX_QUERY_URL=http://localhost:8001
QUERYX_DATA_URL=http://localhost:8002
QUERYX_HISTORY_URL=http://localhost:8003
QUERYX_CHART_URL=http://localhost:8004
```

## 🚀 Deployment

### Monolith
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Microservices (Local)
```bash
./scripts/start.sh micro
# Or manually:
python scripts/run_microservices.py
```

### Microservices (Docker)
```bash
docker compose up --build
# Services: gateway, query, data, history, chart
```

### Docker (Monolith)
```bash
docker build -t queryx .
docker run -p 8000:8000 queryx
```

## 📊 Observability

### Health Endpoints
- `GET /api/health` - Monolith
- `GET /health` - Each microservice

### Logging
```python
# Structured logging via structlog
logger.info("query.executed", sql=sql, rows=len(rows), duration_ms=ms)
```

### Metrics (Future)
- Prometheus `/metrics` endpoint
- Request latency, error rates, queue depths

## 🔧 Extending the System

### Adding a New Feature
1. Create `app/features/new_feature/`
2. Add `controller.py`, `service.py`, `schemas.py`
3. Register routes in `app/main.py`
4. Add tests in `tests/unit/features/new_feature/`
5. Add architecture test for layering

### Adding a Chart Type
1. Create `app/features/charts/builders/new_chart.py`
2. Add to `CHART_BUILDERS` in `catalog.py`
3. Add metadata in `CHART_METADATA`
4. Add test in `tests/charts/test_new_chart.py`

### Adding a Microservice
1. Create `services/new_service/`
2. Copy structure from existing service
3. Add to `docker-compose.yml`
4. Register in `scripts/run_microservices.py`
5. Add client in relevant feature