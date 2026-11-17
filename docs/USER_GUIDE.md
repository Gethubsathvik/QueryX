# QueryX user guide

## 1. How it works (in 30 seconds)
```
You ask a question  ─►  QueryX writes SQL  ─►  safety checks  ─►  read-only database  ─►  table + chart
You edit or type SQL ──────────────────────────┘
```
1. **Ask** in plain English (Claude writes the SQL; without an API key the offline demo engine answers the example chips).
2. The SQL appears in the **SQL box**. It is yours to read, edit and re-run.
3. Every query, generated or typed, is checked (one SELECT only, known tables only), runs on a **read-only** copy of access, and is capped at 500 rows and 3 seconds. Nothing can change your data.
4. The result shows as a **table** and in the **Chart studio**, where you pick any of 40 chart types.

## 2. First run
1. Start it: `scripts\start.bat` (Windows) or `./scripts/start.sh` (Linux/macOS). Open http://localhost:8000.
2. Click an example chip such as **Monthly revenue**. You get the SQL, a line chart and the rows.
3. Press **Chart gallery** and click **Try example** on any chart to see it with matching demo data.

## 3. Customise the query (the SQL bar)
1. Ask a question, or click a table name in the left panel (it fills `SELECT * FROM table LIMIT 100`).
2. Edit the text in the **SQL** box. Click a column name in the left panel to insert it at the cursor.
3. Press **Run SQL** or `Ctrl+Enter` (`Cmd+Enter` on Mac). The chart updates.
4. **Reset to generated** restores what QueryX originally wrote. **Copy** copies the SQL.
5. If something is wrong the message appears under the box (for example `no such column: nope`). Fix it and run again.

### Recipes (all run on the demo data)
| Goal | SQL |
|---|---|
| Change the grouping | `SELECT p.category, ROUND(SUM(oi.quantity*oi.unit_price),2) AS revenue FROM order_items oi JOIN products p ON p.id=oi.product_id GROUP BY p.category` |
| Filter | add `WHERE o.status = 'completed' AND o.order_date >= '2025-01-01'` |
| Top N | add `ORDER BY revenue DESC LIMIT 5` |
| Group by month | `strftime('%Y-%m', o.order_date) AS month ... GROUP BY month ORDER BY month` |
| Two series | return a text column, a second text column and a number: `SELECT month, category, revenue` and pick **Area** or **Stacked bar** |
| Reusable step (CTE) | `WITH per_customer AS (SELECT customer_id, COUNT(*) AS orders FROM orders GROUP BY customer_id) SELECT orders, COUNT(*) AS customers FROM per_customer GROUP BY orders` |
| Rename a column | `SUM(quantity*unit_price) AS sales` (the chart axis uses the new name) |

Tips: date columns are text like `2025-03-14`; revenue is `SUM(quantity * unit_price)` for `status = 'completed'`; end with a name (`AS revenue`) for every calculated column.

### What is blocked (on purpose)
`INSERT`, `UPDATE`, `DELETE`, `DROP`, `PRAGMA`, `ATTACH`, several statements at once, system tables (`sqlite_master`) and unknown tables. You will see `Blocked unsafe SQL: ...`. Blocked SQL is never retried or "fixed" automatically.

## 4. Pick and tune a chart
1. In **Chart studio**, open **Chart type**. The first group, *Fits this result*, lists charts that suit your columns.
2. Columns are chosen automatically; the dropdown reads `Auto (column)`. Choose another column to override, or tick several columns where a chart takes many (box plot, radar, correlation matrix).
3. Options sit beside the pickers: bins, stack series, total bar, sigma limits, tree depth, and so on.
4. **Download PNG** saves the chart.
5. If a chart says it needs a column type, change the SQL to return one (see the table below), or pick the column manually.

### What each chart family needs from the SQL
| Chart | Return these columns |
|---|---|
| Bar, Line, Area, Pie, Waterfall, Funnel | 1 text or date column + 1 number |
| Grouped / Stacked bar, Heatmap, Marimekko, 3D surface | 2 text/date columns + 1 number |
| Histogram, Density, Q-Q, Rug | 1 number (one row per item) |
| Box, Violin, Error bar | 1 text column (group) + 1 number, one row per item |
| Scatter, 3D scatter, Bubble | 2 to 3 numbers (+ a text column for colour) |
| Correlation matrix, Scree (PCA), Radar | 2+ number columns |
| Treemap, Sunburst | 1 to 3 text columns (levels) + 1 number |
| Sankey | source text, target text, value |
| Gantt | task, start date, end date (+ phase) |
| Candlestick, OHLC | date, open, high, low, close |
| Control chart | time/sequence + 1 measurement |
| ROC, Precision-Recall | actual (2 classes) + 1 or more score columns |
| Confusion matrix | actual + predicted (+ optional count) |
| Learning curve | training size + score columns |
| Decision tree | numeric features + one target column (put the target last) |

The gallery's **Try example** shows the exact SQL for each one; copy it and edit it.

## 5. Use your own data
1. Click **Choose File** under *Upload CSV* (up to 5 MB, 100,000 rows). It becomes a table named after the file.
2. Click the table in the left panel and run it, or ask a question about it (needs an API key; otherwise write SQL).

## 6. Turn on real natural language
Set `ANTHROPIC_API_KEY` before starting (see the README), then ask anything, such as "average order value by country in 2025". Check the SQL it wrote before trusting the numbers.

## 7. Troubleshooting
| Message | Meaning and fix |
|---|---|
| `Blocked unsafe SQL` | You used a non-SELECT statement or a table that does not exist |
| `no such column` / `no such table` | Check the spelling against the left panel |
| `Query timed out` | Add a filter or `LIMIT`, or aggregate more |
| `(truncated at the row limit)` | Only the first 500 rows are shown; aggregate in SQL |
| Chart says it needs a numeric column | Return a number column (use `COUNT`, `SUM`, `AVG`) |
| Demo mode cannot answer | Use the SQL bar, or set an API key |
