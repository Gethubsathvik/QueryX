# 🔎 QueryX: Ask Your Data in Plain English

> 🎯 **A natural-language-to-SQL BI tool** — Type a question (or write your own SQL), get the SQL, a result table, and **40 chart types** you can switch between. Built as an AI/Data Science portfolio project with the parts most student projects skip: **SQL safety layers** and an **evaluation harness**.

![stack](https://img.shields.io/badge/FastAPI-SQLite-009688) ![charts](https://img.shields.io/badge/charts-40-blue) ![python](https://img.shields.io/badge/python-3.10%2B-yellow) ![tests](https://img.shields.io/badge/tests-115%2B-green) ![license](https://img.shields.io/badge/license-MIT-orange)

---

## 🤖 ML & NLP FORMULAS USED IN THIS PROJECT

### Schema-Aware Prompt Engineering (NL-to-SQL)
The system constructs a structured prompt with database schema context:

$$\text{Prompt} = \text{SystemPrompt} \oplus \text{SchemaContext} \oplus \text{FewShotExamples} \oplus \text{UserQuestion}$$

Where SchemaContext includes:
- Table names, columns, types, foreign keys
- Sample values per column (for categorical)
- Row counts and statistics

### SQL Self-Repair Loop (One-Shot)
On validation failure, the error is fed back to the model:

$$\text{SQL}_{repaired} = \mathcal{M}(\text{Prompt} \oplus \text{FailedSQL} \oplus \text{ErrorMessage})$$

Max iterations: 1 (configurable)

### Confusion Matrix Metrics (Classification Charts)
$$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$$
$$\text{Precision} = \frac{TP}{TP + FP}$$
$$\text{Recall (Sensitivity)} = \frac{TP}{TP + FN}$$
$$\text{Specificity} = \frac{TN}{TN + FP}$$
$$\text{F1-Score} = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

### Learning Curve (Model Performance vs Training Size)
$$\text{Score}(n) = \text{Model}(D_{train}^{(n)}) \text{ evaluated on } D_{val}$$

Plots training/validation score vs. $n$ samples to diagnose bias/variance.

### ROC Curve (Binary Classification)
$$\text{TPR}(t) = \frac{TP(t)}{P}, \quad \text{FPR}(t) = \frac{FP(t)}{N}$$

Where $t$ is the decision threshold. AUC = area under TPR vs FPR curve.

### Precision-Recall Curve (Imbalanced Data)
$$\text{Precision}(t) = \frac{TP(t)}{TP(t) + FP(t)}, \quad \text{Recall}(t) = \frac{TP(t)}{P}$$

More informative than ROC when positive class is rare.

### PCA Scree Plot (Variance Explained)
$$\text{ExplainedVarianceRatio}_i = \frac{\lambda_i}{\sum_{j=1}^{d} \lambda_j}$$

$$\text{CumulativeVariance}_k = \sum_{i=1}^{k} \text{ExplainedVarianceRatio}_i$$

Where $\lambda_i$ are eigenvalues of covariance matrix.

### Decision Tree Visualization (Recursive Partitioning)
$$\text{NodeSplit} = \arg\max_{f, t} \left[ G(\text{parent}) - \frac{n_L}{n}G(\text{left}) - \frac{n_R}{n}G(\text{right}) \right]$$

Where $f$ = feature, $t$ = threshold, $G$ = Gini impurity.

### Control Chart I-MR (Statistical Process Control)
**Individuals Chart (I):**
$$\bar{X} = \frac{1}{n}\sum_{i=1}^{n} x_i$$
$$\text{UCL} = \bar{X} + 2.66 \cdot \overline{MR}, \quad \text{LCL} = \bar{X} - 2.66 \cdot \overline{MR}$$

**Moving Range Chart (MR):**
$$MR_i = |x_i - x_{i-1}|$$
$$\overline{MR} = \frac{1}{n-1}\sum_{i=2}^{n} MR_i$$
$$\text{UCL}_{MR} = 3.267 \cdot \overline{MR}, \quad \text{LCL}_{MR} = 0$$

Constants $2.66 = 3/d_2$, $3.267 = 3 \cdot d_3/d_2$ for $n=2$ subgroups.

---

## ✨ Features

| Feature | Description | Status |
|---------|-------------|--------|
| 💬 **Natural Language Query** | Ask in plain English → Get SQL + Results + Chart | ✅ |
| ✏️ **Editable SQL Bar** | Modify generated SQL or write your own (`Ctrl+Enter`) | ✅ |
| 📊 **Chart Studio (40 Types)** | Bar, Line, Pie, Sankey, Candlestick, ROC, Decision Tree... | ✅ |
| 🖼️ **Chart Gallery** | Browse all charts, click **Try Example** to load demo data | ✅ |
| 🛡️ **Defense-in-Depth SQL Safety** | AST validator + Read-only DB + Authorizer + Limits | ✅ |
| 📁 **CSV Upload** | Drag & drop CSV → Instantly queryable table | ✅ |
| 🧪 **Evaluation Harness** | Execution accuracy against golden question set | ✅ |
| 🏗️ **MVC + Service Layer** | Feature-based folders, clean architecture | ✅ |
| 🧩 **Microservices Mode** | Gateway + 4 services, Docker Compose ready | ✅ |
| 🌗 **Dark/Light Theme** | Responsive, mobile-friendly, accessible | ✅ |
| 📱 **Cross-Platform** | Windows, Linux, macOS, Android (Termux), Docker | ✅ |

---

## 🚀 Quick Start

> **Needs:** Python 3.10+ • **No API key required** (offline demo mode) • First run installs packages into local `.venv` (needs internet once)

### 🪟 Windows (PowerShell / CMD / Git Bash)

```powershell
# 1️⃣ Install Python from python.org ✅ Tick "Add Python to PATH"
# 2️⃣ Unzip project, open folder in terminal

# 🎯 Monolith (single process, port 8000)
scripts\start.bat

# 🧩 Microservices (5 services, ports 8000-8004)
scripts\start.bat micro

# 🌐 Open browser → http://localhost:8000
```

**Alternative (manual):**
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

**Environment variables (PowerShell):**
```powershell
$env:API_KEY="your_key"     # Enable API_KEY
$env:QUERYX_PORT="8080"               # Custom port
$env:QUERYX_HOST="0.0.0.0"            # Expose to network
```

---

### 🐧 Linux (Debian/Ubuntu/Arch/Fedora)

```bash
# 1️⃣ Install Python + venv
# Debian/Ubuntu:
sudo apt update && sudo apt install python3 python3-venv python3-pip
# Arch:
sudo pacman -S python python-pip
# Fedora:
sudo dnf install python3 python3-venv

# 2️⃣ Run
cd QueryX
chmod +x scripts/start.sh

# 🎯 Monolith
./scripts/start.sh

# 🧩 Microservices
./scripts/start.sh micro

# 🌐 Open browser → http://localhost:8000
```

**Manual start:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

**Environment variables (bash):**
```bash
export API_KEY="your_key"
export QUERYX_PORT=8080
export QUERYX_HOST=0.0.0.0
```

---

### 🍎 macOS (Intel & Apple Silicon)

```bash
# 1️⃣ Install Python (if not present)
brew install python   # or from python.org

# 2️⃣ Run
cd QueryX
chmod +x scripts/start.sh

# 🎯 Monolith
./scripts/start.sh

# 🧩 Microservices
./scripts/start.sh micro

# 🌐 Open browser → http://localhost:8000
```

**Manual start:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

**Note for Apple Silicon:** All dependencies are pure Python or have universal wheels — no Rosetta needed.

---

### 🤖 Android (Termux) — Experimental ⚠️

> **Two options. Option A is recommended for most users.**

#### 🅰️ Option A: Run on Computer, Access from Phone (Easiest)
```bash
# On your computer (Windows/Linux/mac):
# Start with network exposure
QUERYX_HOST=0.0.0.0 ./scripts/start.sh
# Windows PowerShell:
$env:QUERYX_HOST="0.0.0.0"; scripts\start.bat

# Find computer's IP (e.g., 192.168.1.20)
# On phone browser (same Wi-Fi): http://192.168.1.20:8000
```
> ⚠️ Only do this on trusted networks — the app has no authentication.

#### 🅱️ Option B: Run Directly on Android with Termux
```bash
# 1️⃣ Install Termux from F-Droid (not Play Store!)
# https://f-droid.org/packages/com.termux/

# 2️⃣ In Termux:
pkg update && pkg install python git

# 3️⃣ Get project (copy via USB, git clone, or unzip)
cd QueryX

# 4️⃣ Run
./scripts/start.sh

# 5️⃣ Open in phone browser: http://localhost:8000
```

**Known Android issues:**
- 📦 `pydantic-core` may need Rust to build: `pkg install rust binutils`
- 🐛 If pip fails on `pydantic-core`, use **Option A** instead
- 📊 Charts work (pure Python, no NumPy/pandas) — this was intentional!

---

### 🐳 Docker (Any Platform)

```bash
# 🎯 Monolith
docker build -t queryx .
docker run -p 8000:8000 queryx

# 🧩 Microservices (needs API key for LLM)
docker compose up --build
# Or with API key:
API_KEY=your_key docker compose up --build

# 🌐 Open browser → http://localhost:8000
```

**Docker Compose services:**
| Service | Port | Description |
|---------|------|-------------|
| `gateway` | 8000 | Public API entry point |
| `query` | 8001 | Natural language → SQL |
| `data` | 8002 | SQL execution + safety |
| `history` | 8003 | Query history |
| `chart` | 8004 | Chart building (40 types) |

---

### 🔑 Enable Real Natural Language (Claude)

```bash
# Linux/macOS
export API_KEY="your_key"
./scripts/start.sh

# Windows PowerShell
$env:API_KEY="your_key"
scripts\start.bat

# Docker
API_KEY=your_key docker compose up --build
```

Now **any question works**, including on your own CSV:
1. Upload `sample_data/marketing_spend.csv`
2. Ask: *"total spend by channel"*

Model configurable via `QUERYX_MODEL` (default: `claude-sonnet-5-5`). See `.env.example`.

---

## 📊 Using the Chart Studio

### 🎯 Basic Workflow
1. **Ask** a question or **edit the SQL** → Press **Run SQL** (`Ctrl+Enter`)
2. **Chart Studio** → Choose chart type (40 available, grouped by category)
3. **Field Mapping** → Columns auto-picked (`Auto (column)`), override via dropdowns
4. **Options** → Bins, stacking, depth, colors... (dynamic per chart type)
5. **Chart Gallery** → **Try Example** loads demo data+SQL, **Use on My Data** applies to your results
6. **Download PNG** → High-res export

### 📈 The 40 Chart Types

| Category | Charts | Best For |
|----------|--------|----------|
| 📊 **Compare & Trend** | Bar, Horizontal Bar, Grouped Bar, Stacked Bar, Line, Area, Time-series | Trends, comparisons over time |
| 🥧 **Part-to-Whole & Flow** | Pie, Doughnut, Treemap, Sunburst, Marimekko, Funnel, Waterfall, Sankey | Proportions, flows, hierarchies |
| 📉 **Distribution** | Histogram, Box, Violin, Density (KDE), Q-Q, Error Bar, Rug | Statistical distributions |
| 🔗 **Relationship** | Scatter (+trend), Bubble, Heatmap, Correlation Matrix, 3D Scatter, 3D Surface | Correlations, multi-dimensional |
| ⚡ **Performance & Process** | Gantt, Bullet, Radar, Control Chart (I-MR) | KPIs, projects, quality control |
| 💰 **Finance** | Candlestick, OHLC | Financial time series |
| 🤖 **Machine Learning** | Scree (PCA), ROC, Precision-Recall, Confusion Matrix, Learning Curve, Decision Tree | Model evaluation |

> **Demo database includes extra tables** so every chart has data:
> - `daily_prices` (OHLC/Candlestick)
> - `sensor_readings` (Control Chart)
> - `model_predictions` (ROC, PR, Confusion Matrix)
> - `learning_curve` (Learning Curve)
> - `project_tasks` (Gantt)
> - `kpi_targets` (Bullet)
> - Plus e-commerce tables for standard charts

**Statistics implemented in pure Python** (no NumPy/SciPy):
- KDE (Gaussian kernel, Silverman bandwidth)
- PCA (Power iteration for eigenvalues)
- ROC/PR curves (Trapezoidal integration)
- Decision Tree (Recursive Gini splitting)
- Control Charts (I-MR with 3-sigma limits)

### 📐 Mathematical Formulas

#### Kernel Density Estimation (KDE)
$$\hat{f}(x) = \frac{1}{nh} \sum_{i=1}^{n} K\left(\frac{x - x_i}{h}\right)$$

Where:
- $K(u) = \frac{1}{\sqrt{2\pi}} e^{-\frac{u^2}{2}}$ (Gaussian kernel)
- $h = 1.06 \hat{\sigma} n^{-1/5}$ (Silverman's rule of thumb)

#### Principal Component Analysis (PCA)
$$\text{Cov}(X) = \frac{1}{n-1} X^T X$$

Eigenvalues $\lambda$ and eigenvectors $v$ from power iteration:
$$v_{k+1} = \frac{X^T X v_k}{\|X^T X v_k\|}$$
$$\lambda = v^T (X^T X) v$$

#### ROC Curve (AUC)
$$\text{AUC} = \int_0^1 \text{TPR}(FPR) dFPR \approx \sum_{i=1}^{n-1} \frac{(\text{FPR}_{i+1} - \text{FPR}_i)(\text{TPR}_{i+1} + \text{TPR}_i)}{2}$$

#### Precision-Recall Curve
$$\text{Precision} = \frac{TP}{TP + FP}, \quad \text{Recall} = \frac{TP}{TP + FN}$$

#### Gini Impurity (Decision Tree)
$$G = 1 - \sum_{i=1}^{C} p_i^2$$

Split criterion: $\Delta G = G_{parent} - \frac{n_{left}}{n}G_{left} - \frac{n_{right}}{n}G_{right}$

#### Control Chart (I-MR) Limits
$$\bar{X} = \frac{1}{n}\sum x_i, \quad \bar{MR} = \frac{1}{n-1}\sum |x_i - x_{i-1}|$$

$$\text{UCL}_X = \bar{X} + 2.66\bar{MR}, \quad \text{LCL}_X = \bar{X} - 2.66\bar{MR}$$
$$\text{UCL}_{MR} = 3.267\bar{MR}, \quad \text{LCL}_{MR} = 0$$

#### Trapezoidal Integration (AUC calculation)
$$\int_a^b f(x)dx \approx \sum_{i=1}^{n} \frac{f(x_i) + f(x_{i-1})}{2} (x_i - x_{i-1})$$

---

## 🏗️ Architecture

### 📁 Project Structure (Feature-Based MVC + Services)

```
QueryX/
├── app/                          # Main application (monolith)
│   ├── core/                     # ⚙️ Cross-cutting concerns
│   │   ├── config.py             # Pydantic settings
│   │   ├── errors.py             # Custom exceptions + handlers
│   │   └── internal_token.py     # Shared secret for micro mode
│   ├── features/                 # 🎯 Feature modules (each = MVC + service)
│   │   ├── ask/                  # 💬 Natural language → SQL
│   │   │   ├── controller.py     # HTTP endpoints
│   │   │   ├── service.py        # Use case orchestration
│   │   │   ├── generators.py     # LLM + demo engines
│   │   │   └── schemas.py        # Pydantic models
│   │   ├── data/                 # 📊 Query execution + safety
│   │   │   ├── controller.py
│   │   │   ├── service.py
│   │   │   ├── repository.py     # SQLite access
│   │   │   ├── safety.py         # 🛡️ sqlglot validator + authorizer
│   │   │   ├── seed.py           # Demo data
│   │   │   ├── client.py         # HTTP client (micro mode)
│   │   │   └── internal.py       # Internal endpoints
│   │   ├── history/              # 📜 Query history
│   │   ├── charts/               # 📈 40 chart types
│   │   │   ├── controller.py
│   │   │   ├── service.py
│   │   │   ├── catalog.py        # Chart metadata registry
│   │   │   ├── mapping.py        # Column → encoding
│   │   │   ├── builders/         # 40 figure builders
│   │   │   ├── stats.py          # KDE, PCA, ROC, Tree, Control
│   │   │   └── tree.py           # Decision tree viz
│   │   └── evaluation/           # 🧪 Execution accuracy
│   ├── views/                    # 🎨 Frontend (V in MVC)
│   │   ├── index.html
│   │   ├── app.css
│   │   ├── app.js
│   │   └── vendor/plotly.min.js  # Bundled, no CDN
│   └── main.py                   # 🔌 Composition root
├── services/                     # 🧩 Microservices (extracted from features)
│   ├── gateway/                  # Port 8000
│   ├── query/                    # Port 8001
│   ├── data/                     # Port 8002
│   ├── history/                  # Port 8003
│   └── chart/                    # Port 8004
├── scripts/                      # 🚀 Launch scripts
│   ├── start.sh                  # Linux/macOS/Android
│   ├── start.bat                 # Windows
│   └── run_microservices.py      # Process orchestrator
├── tests/                        # 🧪 115+ tests
│   ├── unit/                     # Per-layer unit tests
│   ├── integration/              # API + DB tests
│   ├── architecture/             # 🏛️ Layering rule enforcement
│   └── charts/                   # All 40 chart render tests
├── eval/                         # 📊 Evaluation harness
│   ├── golden.json               # Question + reference SQL pairs
│   └── runner.py
├── data/                         # 💾 SQLite databases (gitignored)
├── sample_data/                  # 📁 Demo CSVs
├── docs/                         # 📚 Additional docs
│   └── USER_GUIDE.md
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### 🔄 Request Flow

**Monolith:**
```
Browser → Controller → Service → Generator/Repository → SQLite (ro) → Results + Chart
```

**Microservices:**
```
Browser → Gateway:8000 → Query:8001 → Data:8002 → Chart:8004
                    ↘ History:8003
```
> Services communicate via HTTP + `X-Internal-Token` shared secret. `/internal/*` never exposed publicly.

### 🛡️ SQL Safety Model (5 Layers — Applies to Generated AND Manual SQL)

| Layer | Implementation | Blocks |
|-------|---------------|--------|
| 1️⃣ **AST Validator** | sqlglot (SQLite dialect) | Multiple statements, DDL/DML, unknown tables, PRAGMA, LOAD_EXTENSION |
| 2️⃣ **Read-Only Connection** | `sqlite3.connect(uri, mode=ro)` | Any write at DB level |
| 3️⃣ **SQLite Authorizer** | Callback: only SELECT on allow-listed tables | Unauthorized table access, `sqlite_master` |
| 4️⃣ **Runtime Limits** | 500 rows + 3s timeout | DoS, runaway queries |
| 5️⃣ **No Auto-Repair** | Reject unsafe SQL with HTTP 400 | Silent data corruption |

---

## 🌐 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ask` | `{"question": "..."}` → SQL, rows, chart suggestion, explanation |
| `POST` | `/api/sql` | `{"sql": "..."}` → Run manual SQL through safety pipeline |
| `GET` | `/api/charts` | Chart catalog: fields, options, example SQL, palette |
| `POST` | `/api/chart` | `{columns, rows, chart, mapping?, options?}` → Plotly figure |
| `POST` | `/api/charts/compatible` | Filter charts compatible with result columns |
| `GET` | `/api/schema` | Tables, columns, row counts |
| `GET` | `/api/examples` | Example questions + active engine |
| `GET` | `/api/history` | Recent questions and SQL |
| `POST` | `/api/upload` | Multipart CSV upload → queryable table |
| `GET` | `/api/health` | Status, engine, mode |

---

## ✅ Tests & Evaluation

```bash
# 🧪 Run all tests (115+)
python -m pytest

# 📊 Run evaluation (needs ANTHROPIC_API_KEY)
python -m app.evaluate

# 🏛️ Architecture tests (enforce layering rules)
python -m pytest tests/architecture/

# 📈 Chart tests (renders all 40 types)
python -m pytest tests/charts/
```

**Test coverage includes:**
- ✅ 30+ adversarial SQL safety tests
- ✅ All 40 chart types rendered from example SQL
- ✅ Architecture tests that **fail if layering rules are broken**
- ✅ Microservices integration tests
- ✅ Evaluation harness: execution accuracy on `eval/golden.json`

---

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | unset | Enable Claude LLM engine |
| `QUERYX_MODEL` | `claude-sonnet-5-5` | Model for generation/repair |
| `QUERYX_ENGINE` | unset | Set `demo` to force offline engine |
| `QUERYX_HOST` | `127.0.0.1` | Bind address |
| `QUERYX_PORT` | `8000` | Port (monolith/gateway) |
| `QUERYX_DATA_DIR` | `./data` | SQLite files directory |
| `QUERYX_MAX_ROWS` | `500` | Result row cap |
| `QUERYX_QUERY_TIMEOUT` | `3` | Query timeout (seconds) |
| `QUERYX_INTERNAL_TOKEN` | dev token | **Change in production!** |

See `.env.example` for full list.

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| `python` not found (Windows) | Reinstall Python ✅ **Tick "Add Python to PATH"** |
| `No module named venv` (Linux) | `sudo apt install python3-venv` |
| Port 8000 busy | `QUERYX_PORT=8080 ./scripts/start.sh` (Win: `set QUERYX_PORT=8080`) |
| Phone can't reach app | Use `QUERYX_HOST=0.0.0.0`, same Wi-Fi, allow port in firewall |
| "Demo mode can't answer that" | Set `ANTHROPIC_API_KEY`, or use SQL bar |
| Chart says "needs X column" | Pick column in dropdown, or change SQL (message names column type) |
| Microservices: everything stops | By design — if one exits, launcher stops rest; check error above |
| `pydantic-core` fails on Android | `pkg install rust binutils` in Termux, or use Option A (remote) |

---

## 🗺️ Roadmap

- 🐘 Postgres/MySQL connectors with read-only roles
- 👤 User accounts + saved dashboards
- 🎯 Few-shot examples from history
- 🌊 Streaming + follow-up questions
- ☁️ Deploy to Render / Railway / Fly.io
- 🔌 Plugin system for custom charts

---

## 📝 Resume Bullets

- Built a **natural-language-to-SQL analytics app** (FastAPI, SQLite, Claude API) with schema-aware prompting, one-shot SQL self-repair, and editable SQL console
- Designed a **3-layer SQL safety model** (sqlglot AST validation, read-only connection, SQLite authorizer) verified with adversarial tests
- Implemented a **40-type chart studio** (Plotly) with pure-Python KDE, PCA, ROC/PR, decision-tree, and control-chart algorithms
- Structured code as **MVC + service layer by feature** and shipped a **gateway-based microservices mode** with Docker Compose; 115 automated tests

---

## 📚 Documentation

| File | Description |
|------|-------------|
| 📋 **PRD.md** | Product Requirements Document |
| 🏗️ **ARCHITECTURE.md** | Detailed technical architecture |
| 📏 **RULES.md** | Coding & architecture rules (enforced by tests) |
| 🎨 **DESIGN.md** | UI/UX, API, DB, chart design |
| ✅ **TASKS.md** | Task tracking & milestone history |
| 🧠 **MEMORY.md** | Decision log, gotchas, patterns |
| 📖 **docs/USER_GUIDE.md** | Step-by-step user guide |

---

## 🤝 Contributing

1. Fork → Create feature branch → Make changes
2. Run tests: `pytest` (must pass 115+ tests)
3. Run architecture tests: `pytest tests/architecture/`
4. Lint: `ruff check .` | Format: `ruff format .`
5. Type check: `mypy app/`
6. PR with clear description

---

## 📄 License

MIT License — See `LICENSE` file.

---

## ⭐ Star History

If QueryX helps your portfolio or teaching, please ⭐ the repo!

---

**Made with ❤️ for AI/Data Science portfolios** — Demonstrating production-grade architecture, safety, and evaluation practices that most tutorials skip.