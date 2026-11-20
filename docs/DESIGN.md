# 🎨 DESIGN.md - Design Documentation

## 🎯 Design Philosophy

### Core Principles
1. **Clarity over cleverness** - Code should be boring and obvious
2. **Safety by default** - Every path through the system is protected
3. **Local-first** - Works offline, no external dependencies for core features
4. **Extensible by convention** - New features follow the same pattern
5. **Testable architecture** - Layer separation enables isolated testing

### Visual Identity
- **Color Scheme**: Dark/light theme with CSS variables
- **Typography**: System fonts (San Francisco, Segoe UI, Roboto)
- **Spacing**: 8px base unit, consistent scale
- **Icons**: Inline SVG, no icon fonts
- **Charts**: Plotly.js (bundled), 40 chart types

## 🖥️ Frontend Architecture

### Single Page Application (Vanilla JS)
```
views/
├── index.html      # Semantic HTML5, accessibility-first
├── app.css         # CSS custom properties, mobile-first
├── app.js          # ES6 modules, no build step
└── vendor/
    └── plotly.min.js  # v2.27+, ~3MB minified
```

### State Management
```javascript
// app.js - Simple state object
const state = {
    sql: '',
    results: null,
    chartConfig: { type: 'bar', mapping: {}, options: {} },
    history: [],
    theme: 'light'
};

// Reactive updates via render functions
function renderResults() { ... }
function renderChart() { ... }
function renderHistory() { ... }
```

### Component Structure
```
index.html
├── Header (logo, theme toggle, engine indicator)
├── Main
│   ├── Query Panel
│   │   ├── NL Input (textarea + ask button)
│   │   ├── SQL Editor (monospace, Ctrl+Enter)
│   │   └── Engine badge (Demo/Claude)
│   ├── Results Panel
│   │   ├── Table (sortable, paginated)
│   │   ├── Chart Studio
│   │   │   ├── Type selector (40 types, grouped)
│   │   │   ├── Field mapping (dropdowns)
│   │   │   ├── Options panel (dynamic)
│   │   │   └── Download PNG
│   │   └── Chart Gallery (modal)
│   └── History Sidebar (collapsible)
└── Footer (version, links)
```

### Responsive Breakpoints
```css
/* Mobile first */
@media (min-width: 640px)  { /* Tablet */ }
@media (min-width: 1024px) { /* Desktop */ }
@media (min-width: 1280px) { /* Wide */ }
```

### Theme System
```css
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f8fafc;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --accent: #0d9488;
    --border: #e2e8f0;
    --danger: #dc2626;
}

[data-theme="dark"] {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --accent: #14b8a6;
    --border: #334155;
}
```

## 📊 Chart Design System

### Chart Categories (40 Types)

| Category | Charts | Use Case |
|----------|--------|----------|
| **Compare & Trend** | Bar, H-Bar, Grouped Bar, Stacked Bar, Line, Area, Time-series | Trends, comparisons over time |
| **Part-to-Whole & Flow** | Pie, Doughnut, Treemap, Sunburst, Marimekko, Funnel, Waterfall, Sankey | Proportions, flows |
| **Distribution** | Histogram, Box, Violin, Density, Q-Q, Error Bar, Rug | Statistical distributions |
| **Relationship** | Scatter, Bubble, Heatmap, Correlation, 3D Scatter, 3D Surface | Correlations, multi-dim |
| **Performance & Process** | Gantt, Bullet, Radar, Control Chart | KPIs, processes, quality |
| **Finance** | Candlestick, OHLC | Financial time series |
| **Machine Learning** | Scree, ROC, PR, Confusion Matrix, Learning Curve, Decision Tree | Model evaluation |

### Chart Metadata Schema
```python
@dataclass
class ChartMeta:
    id: str  # "bar", "line", etc.
    name: str  # "Bar Chart"
    category: str  # "compare", "distribution", etc.
    description: str  # Human-readable description
    required_encodings: list  # ["x", "y"]
    optional_encodings: list  # ["color", "facet", "size"]
    options: list  # ["stacked", "horizontal", "normalize"]
    example_sql: str  # Working example
    palette: str  # "categorical", "sequential", "diverging"
```

### Visual Encoding Rules
- **Categorical**: 10-color qualitative palette (colorblind-safe)
- **Sequential**: Viridis for ordered data
- **Diverging**: RdBu for positive/negative
- **Accessibility**: Pattern fills for colorblind, sufficient contrast

### Builder Interface
```python
def build_chart(
    columns: list[str],
    rows: list[dict],
    mapping: dict[str, str],      # {"x": "category", "y": "value"}
    options: dict[str, Any]       # {"stacked": true, "horizontal": false}
) -> go.Figure:
    # Returns Plotly Figure
    # Must handle missing/invalid data gracefully
    # Must respect options
    # Pure Python, no external deps beyond plotly
```

## 🔧 API Design

### REST Conventions
| Resource | Methods | Description |
|----------|---------|-------------|
| `/api/ask` | POST | Natural language query |
| `/api/sql` | POST | Manual SQL execution |
| `/api/charts` | GET | Chart catalog |
| `/api/chart` | POST | Build chart figure |
| `/api/charts/compatible` | POST | Filter compatible charts |
| `/api/schema` | GET | Database schema |
| `/api/examples` | GET | Example questions |
| `/api/history` | GET | Query history |
| `/api/upload` | POST | CSV upload |
| `/api/health` | GET | Health check |

### Request/Response Patterns
```python
# Request
class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


# Response
class AskResponse(BaseModel):
    sql: str
    engine: Literal["demo", "claude"]
    rows: list[dict[str, Any]]
    columns: list[str]
    chart_suggestion: ChartSuggestion | None
    explanation: str | None
    truncated: bool
    execution_time_ms: float
```

### Error Responses
```python
class ErrorResponse(BaseModel):
    error: str  # Machine-readable code
    message: str  # Human-readable
    details: dict | None = None  # Validation details
    request_id: str  # For tracing


# HTTP Status Codes
# 400 - Validation/Safety error
# 413 - Payload too large
# 429 - Rate limited
# 500 - Internal error
# 503 - Service unavailable (micro mode)
```

## 🗄️ Database Schema

### Core Tables (Demo)
```sql
-- E-commerce
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT, email TEXT, country TEXT, created_at TEXT
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT, category TEXT, price REAL, cost REAL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER, product_id INTEGER,
    quantity INTEGER, order_date TEXT, status TEXT
);

-- Financial
CREATE TABLE daily_prices (
    symbol TEXT, date TEXT, open REAL, high REAL,
    low REAL, close REAL, volume INTEGER
);

-- ML/Monitoring
CREATE TABLE model_predictions (
    id INTEGER PRIMARY KEY,
    y_true INTEGER, y_prob REAL, model_version TEXT
);

CREATE TABLE sensor_readings (
    id INTEGER PRIMARY KEY,
    sensor_id TEXT, timestamp TEXT, value REAL
);

-- Time series / Process
CREATE TABLE project_tasks (
    id INTEGER PRIMARY KEY,
    name TEXT, start_date TEXT, end_date TEXT,
    assignee TEXT, progress REAL
);

CREATE TABLE kpi_targets (
    metric TEXT, target REAL, actual REAL, period TEXT
);
```

### Dynamic Tables (CSV Upload)
- Created as `upload_<uuid>` with inferred schema
- Temporary, cleaned on restart
- Queried like any other table

## 🔐 Security Design

### Threat Model
| Threat | Mitigation |
|--------|------------|
| SQL Injection | AST validation + read-only + authorizer |
| Data Exfiltration | Row limits, timeout, no admin tables |
| DoS | Query timeout, connection limits |
| SSRF (micro) | Internal token, no external calls |
| XSS | CSP, no user HTML, Plotly sanitizes |

### Defense in Depth (Implemented)
```
User Input
    │
    ▼
┌─────────────────────────────────────┐
│ 1. Pydantic Validation              │  (schema, types, length)
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 2. sqlglot AST Validation           │  (structure, tables, keywords)
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 3. Read-Only Connection (URI)       │  (mode=ro, immutable)
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 4. SQLite Authorizer Callback       │  (SELECT only, allow-listed tables)
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 5. Runtime Limits                   │  (500 rows, 3s timeout)
└─────────────────────────────────────┘
    │
    ▼
Results + Truncation Flag
```

## 📱 Mobile Considerations

### Touch Optimizations
- 44px minimum touch targets
- Swipe to close modals
- Pull-to-refresh on results
- Virtual keyboard handling (viewport)

### Performance
- Lazy-load chart builders
- Debounced SQL editor (300ms)
- Paginated tables (50 rows/page)
- Compressed Plotly.js (3MB → 1MB gzipped)

## 🎨 Accessibility (WCAG 2.1 AA)

### Implemented
- Semantic HTML5 landmarks
- ARIA labels on interactive elements
- Focus visible outlines
- Color contrast ratios (4.5:1)
- Keyboard navigation (Tab, Enter, Escape)
- Screen reader announcements for dynamic content
- Reduced motion support

### Chart Accessibility
- Text summaries for all charts
- Data tables as alternative
- High-contrast mode
- Pattern fills for colorblind

## 🌐 Internationalization (Future)

### Design for i18n
```javascript
// app.js - String externalization ready
const i18n = {
    en: { ask: "Ask a question", run: "Run SQL" },
    es: { ask: "Haz una pregunta", run: "Ejecutar SQL" }
};
```

## 🔄 Migration Strategy (Future)

### Database Migrations
- Versioned SQL files in `migrations/`
- Applied on startup (monolith) or per-service (micro)
- Rollback scripts for each migration

### API Versioning
- URL versioning: `/api/v1/`, `/api/v2/`
- Deprecation headers: `Sunset`, `Deprecation`
- 6-month overlap minimum