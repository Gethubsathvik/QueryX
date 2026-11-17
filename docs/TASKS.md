# ✅ TASKS.md - Task Tracking

## 📋 Legend
- ✅ **Done** - Completed and tested
- 🔄 **In Progress** - Currently working
- ⏳ **Pending** - Not started
- 🚫 **Blocked** - Waiting on dependency
- 💡 **Idea** - Future consideration

---

## 🏗️ Core Architecture (Milestone 1) ✅ COMPLETE

| ID | Task | Status | Notes |
|----|------|--------|-------|
| ARCH-01 | MVC + Service layer structure | ✅ | `app/features/*` pattern |
| ARCH-02 | Feature-based folder organization | ✅ | ask, data, history, charts, evaluation |
| ARCH-03 | Composition root (`main.py`) | ✅ | Wires all features |
| ARCH-04 | Core config/errors/internal_token | ✅ | Pydantic settings, custom exceptions |
| ARCH-05 | Static frontend (views/) | ✅ | HTML/CSS/JS + bundled Plotly |

---

## 🗣️ Natural Language Query (Milestone 2) ✅ COMPLETE

| ID | Task | Status | Notes |
|----|------|--------|-------|
| NL-01 | Demo engine (pattern-based) | ✅ | No API key needed |
| NL-02 | Claude integration | ✅ | Anthropic SDK, schema-aware prompt |
| NL-03 | SQL self-repair loop | ✅ | One-shot retry on safety errors |
| NL-04 | Editable SQL bar | ✅ | Ctrl+Enter, syntax highlighting |
| NL-05 | Engine switching (demo/claude) | ✅ | Via `QUERYX_ENGINE` env var |

---

## 🛡️ SQL Safety (Milestone 3) ✅ COMPLETE

| ID | Task | Status | Notes |
|----|------|--------|-------|
| SF-01 | sqlglot AST validator | ✅ | Single stmt, SELECT only, known tables |
| SF-02 | Read-only SQLite connection | ✅ | `mode=ro` URI |
| SF-03 | SQLite authorizer callback | ✅ | Allow-listed tables, SELECT only |
| SF-04 | Row limit (500) | ✅ | Truncation flagged in response |
| SF-05 | Query timeout (3s) | ✅ | `sqlite3_interrupt` |
| SF-06 | Applies to manual SQL too | ✅ | `/api/sql` same pipeline |
| SF-07 | Adversarial test suite | ✅ | 30+ safety tests |

---

## 📊 Chart Studio - 40 Types (Milestone 4) ✅ COMPLETE

| ID | Category | Charts | Status |
|----|----------|--------|--------|
| CH-01 | Compare & Trend | Bar, H-Bar, Grouped Bar, Stacked Bar, Line, Area, Time-series | ✅ |
| CH-02 | Part-to-Whole & Flow | Pie, Doughnut, Treemap, Sunburst, Marimekko, Funnel, Waterfall, Sankey | ✅ |
| CH-03 | Distribution | Histogram, Box, Violin, Density, Q-Q, Error Bar, Rug | ✅ |
| CH-04 | Relationship | Scatter, Bubble, Heatmap, Correlation, 3D Scatter, 3D Surface | ✅ |
| CH-05 | Performance & Process | Gantt, Bullet, Radar, Control Chart | ✅ |
| CH-06 | Finance | Candlestick, OHLC | ✅ |
| CH-07 | Machine Learning | Scree, ROC, PR, Confusion Matrix, Learning Curve, Decision Tree | ✅ |

| ID | Task | Status | Notes |
|----|------|--------|-------|
| CH-08 | Auto column mapping | ✅ | Smart defaults by dtype |
| CH-09 | Chart gallery with examples | ✅ | Try example / Use on my data |
| CH-10 | Download PNG | ✅ | `fig.to_image()` |
| CH-11 | Pure Python statistics | ✅ | KDE, PCA, ROC, Tree, Control limits |
| CH-12 | All 40 charts render test | ✅ | `tests/charts/test_all_charts.py` |

---

## 📁 Data Management (Milestone 5) ✅ COMPLETE

| ID | Task | Status | Notes |
|----|------|--------|-------|
| DM-01 | Demo database (15+ tables) | ✅ | Covers all chart types |
| DM-02 | CSV upload → temp table | ✅ | Auto schema inference |
| DM-03 | Schema introspection API | ✅ | `/api/schema` |
| DM-04 | Query history | ✅ | SQLite, `/api/history` |
| DM-05 | Example questions API | ✅ | `/api/examples` |

---

## 🧪 Evaluation Harness (Milestone 6) ✅ COMPLETE

| ID | Task | Status | Notes |
|----|------|--------|-------|
| EV-01 | Golden set (eval/golden.json) | ✅ | 50+ question+SQL pairs |
| EV-02 | Execution accuracy runner | ✅ | `python -m app.evaluate` |
| EV-03 | CI integration ready | ✅ | Runs in pytest |

---

## 🏗️ Microservices Mode (Milestone 7) ✅ COMPLETE

| ID | Task | Status | Notes |
|----|------|--------|-------|
| MS-01 | Gateway service (port 8000) | ✅ | Proxies public `/api/*` |
| MS-02 | Query service (port 8001) | ✅ | Ask/NL features |
| MS-03 | Data service (port 8002) | ✅ | SQL execution, safety |
| MS-04 | History service (port 8003) | ✅ | Query history |
| MS-05 | Chart service (port 8004) | ✅ | Chart building |
| MS-06 | Internal token auth | ✅ | `X-Internal-Token` header |
| MS-07 | Process orchestrator | ✅ | `scripts/run_microservices.py` |
| MS-08 | Docker Compose | ✅ | `docker compose up` |
| MS-09 | Start script integration | ✅ | `start.sh micro` / `start.bat micro` |

---

## 🧪 Testing Infrastructure (Milestone 8) ✅ COMPLETE

| ID | Task | Status | Notes |
|----|------|--------|-------|
| TEST-01 | 115+ unit/integration tests | ✅ | pytest, pytest-asyncio |
| TEST-02 | Architecture layering tests | ✅ | Enforces import rules |
| TEST-03 | Chart rendering tests (all 40) | ✅ | Verifies no regressions |
| TEST-04 | Safety adversarial tests | ✅ | Injection, DDL, etc. |
| TEST-05 | Microservices integration tests | ✅ | Service-to-service |

---

## 📚 Documentation Suite (Milestone 9) 🔄 IN PROGRESS

| ID | Task | Status | Notes |
|----|------|--------|-------|
| DOC-01 | PRD.md | ✅ | Product Requirements |
| DOC-02 | ARCHITECTURE.md | ✅ | Technical architecture |
| DOC-03 | RULES.md | ✅ | Coding/architecture rules |
| DOC-04 | DESIGN.md | ✅ | UI/UX, API, DB design |
| DOC-05 | TASKS.md | 🔄 | This file |
| DOC-06 | MEMORY.md | ⏳ | Knowledge base |
| DOC-07 | README.md enhancements | ⏳ | More emojis, platform docs |

---

## 🐳 Docker & CI/CD (Milestone 10) ⏳ PENDING

| ID | Task | Status | Notes |
|----|------|--------|-------|
| DEV-01 | Multi-stage Dockerfile | ⏳ | Slim runtime image |
| DEV-02 | GitHub Actions CI | ⏳ | Lint, typecheck, test |
| DEV-03 | Dependabot config | ⏳ | Auto dependency updates |
| DEV-04 | Release workflow | ⏳ | Tag → Docker Hub |

---

## 🚀 Future Enhancements (Backlog) 💡 IDEAS

| ID | Task | Priority | Effort |
|----|------|----------|--------|
| FUT-01 | Postgres/MySQL connectors | High | Medium |
| FUT-02 | User accounts + saved dashboards | High | Large |
| FUT-03 | Few-shot examples from history | Medium | Medium |
| FUT-04 | Streaming/follow-up questions | Medium | Large |
| FUT-05 | Deploy to Render/Railway/Fly.io | High | Small |
| FUT-06 | WebSocket for real-time updates | Low | Medium |
| FUT-07 | Chart embedding (iframe) | Low | Small |
| FUT-08 | Export to CSV/Excel | Medium | Small |
| FUT-09 | Query scheduling/cron | Low | Medium |
| FUT-10 | Plugin system for custom charts | Low | Large |

---

## 🐛 Known Issues / Tech Debt

| ID | Issue | Severity | Workaround |
|----|-------|----------|------------|
| BUG-01 | pydantic-core needs Rust on Android Termux | Medium | Use Option A (remote) or `pkg install rust` |
| BUG-02 | Microservices: one crash stops all | By design | Read launcher logs |
| BUG-03 | No auth on local dev | By design | Don't expose to internet |
| TECH-01 | SQL repair loop only runs once | Low | Could add multi-shot |
| TECH-02 | Chart options UI could be more dynamic | Low | Current: static per chart type |

---

## 📅 Sprint Tracking (Example)

### Sprint 1 (Weeks 1-2) ✅
- [x] Core architecture
- [x] NL query (demo + claude)
- [x] SQL safety layers
- [x] Basic charts (10 types)

### Sprint 2 (Weeks 3-4) ✅
- [x] All 40 chart types
- [x] Chart gallery
- [x] CSV upload
- [x] Evaluation harness

### Sprint 3 (Weeks 5-6) ✅
- [x] Microservices mode
- [x] Docker Compose
- [x] Architecture tests
- [x] 115+ test suite

### Sprint 4 (Weeks 7-8) 🔄
- [x] PRD.md
- [x] ARCHITECTURE.md
- [x] RULES.md
- [x] DESIGN.md
- [ ] TASKS.md (this file)
- [ ] MEMORY.md
- [ ] README.md enhancements

---

## ✅ Definition of Done

A task is **Done** when:
- [ ] Code implemented per RULES.md
- [ ] Unit tests written (>90% coverage for new code)
- [ ] Integration tests pass
- [ ] Architecture tests pass (no layering violations)
- [ ] Documentation updated (if user-facing)
- [ ] Linting passes (`ruff check .`)
- [ ] Type checking passes (`mypy app/`)
- [ ] Manual verification on target platforms

---

## 📊 Metrics Dashboard

| Metric | Current | Target |
|--------|---------|--------|
| Test Count | 115 | >150 |
| Test Coverage | ~88% | >90% |
| Chart Types | 40 | 40 ✅ |
| Architecture Violations | 0 | 0 ✅ |
| Safety Test Cases | 30+ | 30+ ✅ |
| Platforms Supported | 5 | 5 ✅ |
| Documentation Files | 6 | 7 |