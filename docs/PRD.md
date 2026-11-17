# 📋 PRD - Product Requirements Document

## 🎯 Product Vision
**QueryX** is a natural-language-to-SQL Business Intelligence tool that lets users ask questions about their data in plain English and get instant visualizations. Built as an AI/Data Science portfolio project demonstrating production-grade architecture, SQL safety, and evaluation practices.

## 👥 Target Users
- **Data Analysts** - Quick ad-hoc queries without writing SQL
- **Developers** - Learning NL-to-SQL patterns and safety architectures
- **Students** - Portfolio project reference for MVC + microservices
- **Product Managers** - Self-service data exploration

## ✨ Core Features

### 🗣️ Natural Language Query (Epic 1)
| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| NL-01 | Ask question in plain English | P0 | Returns SQL, results, chart suggestion in <3s |
| NL-02 | Edit generated SQL before running | P0 | SQL bar editable, Ctrl+Enter executes |
| NL-03 | Works offline (demo mode) | P0 | No API key required, pattern-based generation |
| NL-04 | Real LLM with API key | P1 | Set ANTHROPIC_API_KEY for full NL capability |

### 📊 Chart Studio (Epic 2)
| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| CH-01 | 40 chart types available | P0 | All categories: compare, part-to-whole, distribution, relationship, performance, finance, ML |
| CH-02 | Auto column mapping | P0 | Smart defaults, manual override via dropdowns |
| CH-03 | Chart gallery with examples | P1 | Try example loads demo data + SQL |
| CH-04 | Download PNG | P1 | High-res export works for all types |

### 🛡️ SQL Safety (Epic 3)
| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| SF-01 | AST validation (sqlglot) | P0 | Blocks DDL, DML, multiple statements, unknown tables |
| SF-02 | Read-only DB connection | P0 | `mode=ro` prevents writes at DB level |
| SF-03 | SQLite authorizer | P0 | Only SELECT on allow-listed tables |
| SF-04 | Row limit (500) + timeout (3s) | P0 | Truncation flagged, queries killed |
| SF-05 | Applies to manual SQL too | P0 | Same pipeline for `/api/sql` |

### 📁 Data Management (Epic 4)
| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| DM-01 | Upload CSV → queryable table | P1 | Auto-infers schema, creates temp table |
| DM-02 | Schema introspection | P1 | `/api/schema` returns tables, columns, counts |
| DM-03 | Demo database with 15+ tables | P0 | Covers all 40 chart types |

### 🧪 Evaluation Harness (Epic 5)
| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| EV-01 | Golden set execution accuracy | P1 | Compare generated SQL results to reference |
| EV-02 | Run via `python -m app.evaluate` | P1 | Outputs accuracy score |
| EV-03 | 115+ automated tests | P0 | Safety, DB, API, charts, services, architecture |

### 🏗️ Architecture Modes (Epic 6)
| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| AR-01 | Monolith (single process) | P0 | `start.sh` → port 8000 |
| AR-02 | Microservices (5 services) | P1 | Gateway 8000, query 8001, data 8002, history 8003, chart 8004 |
| AR-03 | Shared internal token auth | P1 | X-Internal-Token for service-to-service |
| AR-04 | Docker Compose support | P1 | `docker compose up` for microservices |

## 📱 Platform Support
| Platform | Support Level | Notes |
|----------|---------------|-------|
| Windows 10/11 | ✅ Full | start.bat, PowerShell |
| Linux (Debian/Ubuntu/Arch) | ✅ Full | start.sh, python3-venv |
| macOS | ✅ Full | start.sh, Homebrew Python |
| Android (Termux) | ⚠️ Experimental | Option A (remote) recommended |
| Docker | ✅ Full | Monolith + microservices compose |

## 🔧 Non-Functional Requirements

| Category | Requirement | Target |
|----------|-------------|--------|
| Performance | Query response (demo mode) | <500ms |
| Performance | Query response (LLM mode) | <3s |
| Performance | Chart render (40 types) | <2s |
| Reliability | Uptime (monolith) | 99.9% local |
| Security | No auth (local dev) | Explicit by design |
| Security | Internal token (micro) | Required for prod |
| Scalability | Microservices horizontal | Independent scaling |
| Maintainability | Test coverage | >90% critical paths |
| Maintainability | Architecture tests | Enforce layering rules |

## 🚫 Out of Scope (v1)
- User authentication/accounts
- Saved dashboards/persisted queries
- Postgres/MySQL connectors (SQLite only)
- Real-time streaming queries
- Multi-tenancy
- Deployment automation (Render/Railway/Fly.io)
- Follow-up/conversational queries
- Few-shot learning from history

## 📈 Success Metrics
- **Portfolio readiness**: All 115 tests pass, architecture tests enforce rules
- **Demo viability**: Runs offline in <30s on fresh machine
- **Code quality**: Zero architecture violations, clean layering
- **Extensibility**: New chart type in <30 min, new feature folder follows pattern

## 🗓️ Milestones
| Milestone | Target | Status |
|-----------|--------|--------|
| Core MVC + services | Week 1 | ✅ Done |
| 40 chart types | Week 2 | ✅ Done |
| SQL safety layers | Week 2 | ✅ Done |
| Microservices mode | Week 3 | ✅ Done |
| Evaluation harness | Week 3 | ✅ Done |
| Documentation suite | Week 4 | 🔄 In Progress |
| Docker + CI/CD | Week 4 | ⏳ Planned |