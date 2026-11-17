"use strict";
const $ = (s) => document.querySelector(s);
const SUGGEST = { bar: "bar", line: "line" };
const state = { catalog: null, byId: {}, last: null, generatedSql: "", chart: "", mapping: {}, options: {},
                compatible: [], seq: 0, galleryCat: "all" };

function esc(s) { const d = document.createElement("div"); d.textContent = String(s ?? ""); return d.innerHTML; }
const attr = (s) => esc(s).replace(/"/g, "&quot;");

async function api(path, opts) {
  const r = await fetch(path, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    const d = data.detail;
    throw new Error(typeof d === "string" ? d : Array.isArray(d) ? d.map((x) => x.msg).join("; ") : `Request failed (${r.status})`);
  }
  return data;
}
const post = (path, body) => api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

/* ---------------------------------------------------------------- sidebar */
async function loadSchema() {
  const { tables } = await api("/api/schema");
  $("#schema").innerHTML = tables.map((t) =>
    `<div class="table-item"><b><span class="tname" data-table="${attr(t.name)}" role="button" tabindex="0">${esc(t.name)}</span> ` +
    `<span class="muted small">(${t.row_count} rows)</span></b><div class="cols">` +
    t.columns.map((c) => `<span class="col" data-col="${attr(c.name)}" role="button" tabindex="0">${esc(c.name)}</span>`).join(", ") +
    `</div></div>`).join("");
}

function insertAtCursor(text) {
  const ta = $("#sql");
  const a = ta.selectionStart ?? ta.value.length, b = ta.selectionEnd ?? ta.value.length;
  ta.value = ta.value.slice(0, a) + text + ta.value.slice(b);
  ta.focus(); ta.selectionStart = ta.selectionEnd = a + text.length;
}

$("#schema").addEventListener("click", (e) => {
  const t = e.target.closest("[data-table]"), c = e.target.closest("[data-col]");
  if (t) { $("#sql").value = `SELECT * FROM ${t.dataset.table} LIMIT 100`; $("#sql").focus(); }
  else if (c) insertAtCursor(c.dataset.col);
});
$("#schema").addEventListener("keydown", (e) => { if (e.key === "Enter") e.target.click(); });

async function loadExamples() {
  const { examples, engine } = await api("/api/examples");
  $("#engine").textContent = "engine: " + engine + (engine === "demo" ? " (offline)" : "");
  $("#examples").innerHTML = examples.map((x) => `<button type="button" class="chip">${esc(x)}</button>`).join("");
  document.querySelectorAll("#examples .chip").forEach((b) => (b.onclick = () => { $("#question").value = b.textContent; ask(); }));
}

async function loadHistory() {
  const { items } = await api("/api/history?limit=10");
  if (!items.length) { $("#history").textContent = "Nothing yet."; return; }
  $("#history").innerHTML = items.map((i, k) => {
    const manual = i.engine === "manual";
    return `<div class="hist-item" data-k="${k}" role="button" tabindex="0">${manual ? '<span class="tag">SQL</span>' : ""}` +
           `${esc(manual ? i.sql.slice(0, 90) : i.question)}</div>`;
  }).join("");
  document.querySelectorAll(".hist-item").forEach((el) => {
    const it = items[+el.dataset.k];
    el.onclick = () => { if (it.engine === "manual") { $("#sql").value = it.sql; runSql(); } else { $("#question").value = it.question; ask(); } };
    el.onkeydown = (e) => { if (e.key === "Enter") el.click(); };
  });
}

/* ---------------------------------------------------------------- ask / run */
function showError(msg) { const e = $("#error"); e.textContent = msg; e.classList.toggle("hidden", !msg); }

function renderTable(cols, rows) {
  const numeric = cols.map((_, i) => rows.length && rows.every((r) => typeof r[i] === "number" || r[i] === null));
  $("#grid").innerHTML = "<thead><tr>" + cols.map((c) => `<th>${esc(c)}</th>`).join("") + "</tr></thead><tbody>" +
    rows.map((r) => "<tr>" + r.map((v, i) => `<td class="${numeric[i] ? "num" : ""}">${v === null ? "<span class='muted'>null</span>" : esc(v)}</td>`).join("") + "</tr>").join("") + "</tbody>";
}

async function applyResult(res, forcedChart) {
  state.last = res;
  state.generatedSql = res.engine === "manual" ? "" : res.sql;
  $("#sql").value = res.sql;
  $("#explanation").textContent = res.engine === "manual" ? "" : res.explanation;
  $("#resetSql").classList.toggle("hidden", !state.generatedSql);
  renderTable(res.columns, res.rows);
  $("#meta").textContent = `${res.row_count} row(s)` + (res.truncated ? " (truncated at the row limit)" : "") +
    ` · ${res.elapsed_ms} ms` + (res.attempts > 1 ? " · auto-repaired SQL" : "") + (res.engine === "manual" ? " · your SQL" : "");
  $("#result").classList.remove("hidden");

  const isMetric = res.chart.type === "metric";
  $("#metricCard").classList.toggle("hidden", !isMetric);
  if (isMetric) {
    $("#metrics").innerHTML = res.columns.map((c, i) =>
      `<div class="metric"><div class="v">${esc(Number(res.rows[0][i]).toLocaleString())}</div><div class="l">${esc(c)}</div></div>`).join("");
  }
  $("#studio").classList.toggle("hidden", !res.row_count);

  try { state.compatible = (await post("/api/charts/compatible", { columns: res.columns, rows: res.rows })).compatible; }
  catch { state.compatible = []; }
  fillChartSelect();
  selectChart(forcedChart || SUGGEST[res.chart.type] || "");
  loadHistory();
}

function busy(btn, on, label) { btn.disabled = on; if (label) btn.textContent = on ? "Working…" : label; }

async function ask() {
  const q = $("#question").value.trim();
  if (q.length < 3) return;
  busy($("#askBtn"), true, "Ask"); showError("");
  try { await applyResult(await post("/api/ask", { question: q })); }
  catch (e) { showError(e.message); }
  finally { busy($("#askBtn"), false, "Ask"); }
}

async function runSql(forcedChart) {
  const sql = $("#sql").value.trim();
  if (!sql) { showError("Type a SQL query first."); return; }
  busy($("#runBtn"), true, "Run SQL"); showError("");
  try { await applyResult(await post("/api/sql", { sql }), forcedChart); }
  catch (e) { showError(e.message); }
  finally { busy($("#runBtn"), false, "Run SQL"); }
}

/* ---------------------------------------------------------------- chart studio */
async function loadCatalog() {
  state.catalog = await api("/api/charts");
  state.catalog.charts.forEach((c) => (state.byId[c.id] = c));
  $("#galleryBtn").textContent = `Chart gallery (${state.catalog.charts.length})`;
  fillChartSelect();
}

function fillChartSelect() {
  if (!state.catalog) return;
  const opt = (c) => `<option value="${c.id}">${esc(c.label)}</option>`;
  let html = `<option value="">Table only</option>`;
  const fit = state.catalog.charts.filter((c) => state.compatible.includes(c.id));
  if (fit.length) html += `<optgroup label="Fits this result (${fit.length})">${fit.map(opt).join("")}</optgroup>`;
  for (const cat of state.catalog.categories) {
    const items = state.catalog.charts.filter((c) => c.category === cat.id);
    html += `<optgroup label="${attr(cat.label)}">${items.map(opt).join("")}</optgroup>`;
  }
  const sel = $("#chartType");
  sel.innerHTML = html;
  sel.value = state.chart;
}

function selectChart(id) {
  state.chart = id; state.mapping = {}; state.options = {};
  $("#chartType").value = id;
  renderControls();
  drawChart();
}

function columnOptions(cols, first) {
  return first + cols.map((c) => `<option value="${attr(c)}">${esc(c)}</option>`).join("");
}

function renderControls() {
  const spec = state.byId[state.chart], cols = state.last ? state.last.columns : [];
  if (!spec) { $("#fields").innerHTML = ""; $("#options").innerHTML = ""; return; }
  $("#fields").innerHTML = spec.fields.map((f) => {
    if (f.multiple) {
      return `<div class="field" data-role="${f.role}" data-multi="1"><span class="lbl">${esc(f.label)}</span>` +
        `<div class="multi">${cols.map((c) => `<label><input type="checkbox" value="${attr(c)}">${esc(c)}</label>`).join("")}</div>` +
        `<span class="muted small hint"></span></div>`;
    }
    const first = `<option value="">Auto</option>` + (f.required ? "" : `<option value="__none__">None</option>`);
    return `<div class="field" data-role="${f.role}"><label>${esc(f.label)}</label>` +
      `<select>${columnOptions(cols, first)}</select></div>`;
  }).join("");
  $("#options").innerHTML = spec.options.map((o) => {
    const v = state.options[o.name] ?? o.default, id = "opt_" + o.name;
    if (o.type === "bool") return `<div class="field check"><input type="checkbox" id="${id}" data-opt="${o.name}" ${v ? "checked" : ""}><label for="${id}">${esc(o.label)}</label></div>`;
    if (o.type === "select") return `<div class="field"><label for="${id}">${esc(o.label)}</label><select id="${id}" data-opt="${o.name}">` +
      o.choices.map((c) => `<option value="${attr(c)}" ${c === v ? "selected" : ""}>${esc(c || "count")}</option>`).join("") + `</select></div>`;
    if (o.type === "number") return `<div class="field"><label for="${id}">${esc(o.label)}</label><input type="number" id="${id}" data-opt="${o.name}" value="${attr(v)}" ` +
      `${o.min != null ? `min="${o.min}"` : ""} ${o.max != null ? `max="${o.max}"` : ""} style="width:110px"></div>`;
    return `<div class="field"><label for="${id}">${esc(o.label)}</label><input type="text" id="${id}" data-opt="${o.name}" value="${attr(v)}" style="width:140px"></div>`;
  }).join("");
}

$("#fields").addEventListener("change", (e) => {
  const field = e.target.closest(".field"); if (!field) return;
  const role = field.dataset.role;
  if (field.dataset.multi) state.mapping[role] = [...field.querySelectorAll("input:checked")].map((i) => i.value);
  else { const v = field.querySelector("select").value; state.mapping[role] = v === "__none__" ? [] : [v]; if (v === "") delete state.mapping[role]; }
  if (field.dataset.multi && !state.mapping[role].length) delete state.mapping[role];
  drawChart();
});
$("#options").addEventListener("change", (e) => {
  const el = e.target.closest("[data-opt]"); if (!el) return;
  state.options[el.dataset.opt] = el.type === "checkbox" ? el.checked : el.type === "number" ? Number(el.value) : el.value;
  drawChart();
});
$("#chartType").onchange = (e) => selectChart(e.target.value);

function reflectAuto(resolved) {
  const spec = state.byId[state.chart];
  document.querySelectorAll("#fields .field").forEach((f) => {
    const role = f.dataset.role, picked = resolved[role] || [], touched = role in state.mapping;
    if (f.dataset.multi) {
      f.querySelectorAll("input").forEach((i) => (i.checked = picked.includes(i.value)));
      f.querySelector(".hint").textContent = touched ? "" : picked.length ? `Auto: ${picked.join(", ")}` : "";
    } else {
      const sel = f.querySelector("select");
      sel.options[0].textContent = picked.length ? `Auto (${picked[0]})` : "Auto";
      if (!touched) sel.value = "";
    }
  });
}

/* Plotly theme taken from the page's CSS variables so charts follow light/dark mode. */
const isObj = (v) => v && typeof v === "object" && !Array.isArray(v);
function merge(a, b) {
  const out = { ...a };
  for (const k of Object.keys(b)) out[k] = isObj(a[k]) && isObj(b[k]) ? merge(a[k], b[k]) : b[k];
  return out;
}
function theme() {
  const cs = getComputedStyle(document.documentElement), v = (n) => cs.getPropertyValue(n).trim();
  const axis = { gridcolor: v("--grid"), zerolinecolor: v("--grid"), linecolor: v("--grid"), automargin: true };
  const panel = v("--panel");
  return {
    font: { color: v("--text"), family: "system-ui,-apple-system,Segoe UI,Roboto,sans-serif", size: 13 },
    paper_bgcolor: panel, plot_bgcolor: panel, margin: { l: 64, r: 24, t: 28, b: 56 },
    xaxis: { ...axis }, yaxis: { ...axis }, legend: { bgcolor: "rgba(0,0,0,0)" },
    scene: { xaxis: { ...axis, backgroundcolor: panel }, yaxis: { ...axis, backgroundcolor: panel }, zaxis: { ...axis, backgroundcolor: panel } },
    polar: { bgcolor: panel, radialaxis: { gridcolor: v("--grid") }, angularaxis: { gridcolor: v("--grid") } },
    hoverlabel: { font: { size: 12 } },
  };
}

function purge() { try { Plotly.purge("plot"); } catch { /* nothing drawn yet */ } }

async function drawChart() {
  const id = state.chart, res = state.last, my = ++state.seq;
  $("#notes").innerHTML = ""; $("#chartMsg").textContent = "";
  if (!id || !res) { purge(); $("#plotWrap").classList.add("hidden"); $("#pngBtn").classList.add("hidden");
    $("#chartMsg").textContent = id ? "" : "Showing the table only. Pick a chart type above, or open the gallery."; return; }
  $("#plotWrap").classList.remove("hidden");
  try {
    const out = await post("/api/chart", { columns: res.columns, rows: res.rows, chart: id, mapping: state.mapping, options: state.options });
    if (my !== state.seq) return; // a newer request superseded this one
    reflectAuto(out.mapping);
    const lay = merge(theme(), out.figure.layout);
    const fixed = typeof lay.width === "number";
    if (!fixed) lay.autosize = true;
    lay.height = lay.height || 460;
    $("#plot").style.width = fixed ? lay.width + "px" : "100%";
    await Plotly.react("plot", out.figure.data, lay, { responsive: !fixed, displaylogo: false, scrollZoom: false });
    $("#pngBtn").classList.remove("hidden");
    const notes = [...out.notes]; if (out.truncated) notes.push("Only the first 5000 rows were used for the chart.");
    $("#notes").innerHTML = notes.map((n) => `<li>${esc(n)}</li>`).join("");
  } catch (e) {
    if (my !== state.seq) return;
    purge(); $("#pngBtn").classList.add("hidden");
    $("#chartMsg").innerHTML = `<span class="error">${esc(e.message)}</span>`;
  }
}

$("#pngBtn").onclick = () => Plotly.downloadImage("plot", { format: "png", filename: "queryx_" + state.chart, scale: 2 });
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => drawChart());

/* ---------------------------------------------------------------- gallery */
function renderGallery() {
  const q = $("#gallerySearch").value.trim().toLowerCase(), cats = state.catalog.categories;
  $("#galleryTabs").innerHTML = [{ id: "all", label: "All" }, ...cats].map((c) =>
    `<button type="button" class="chip ${state.galleryCat === c.id ? "on" : ""}" data-cat="${c.id}">${esc(c.label)}</button>`).join("");
  const catLabel = Object.fromEntries(cats.map((c) => [c.id, c.label]));
  const list = state.catalog.charts.filter((c) => (state.galleryCat === "all" || c.category === state.galleryCat) &&
    (!q || (c.label + " " + c.description).toLowerCase().includes(q)));
  $("#galleryList").innerHTML = list.map((c) =>
    `<div class="gcard"><span class="cat">${esc(catLabel[c.category])}</span><h3>${esc(c.label)}</h3><p>${esc(c.description)}</p>` +
    (state.compatible.includes(c.id) ? `<span class="fit">Fits your current result</span>` : "") +
    `<div class="btns"><button type="button" class="primary" data-example="${c.id}">Try example</button>` +
    (state.last ? `<button type="button" data-use="${c.id}">Use on my data</button>` : "") + `</div></div>`).join("") ||
    `<p class="muted" style="padding:8px 4px">No charts match.</p>`;
}

$("#galleryBtn").onclick = () => { if (!state.catalog) return; renderGallery(); $("#gallery").showModal(); };
$("#galleryClose").onclick = () => $("#gallery").close();
$("#gallery").addEventListener("click", (e) => { if (e.target === $("#gallery")) $("#gallery").close(); });
$("#gallerySearch").oninput = renderGallery;
$("#galleryTabs").addEventListener("click", (e) => { const b = e.target.closest("[data-cat]"); if (b) { state.galleryCat = b.dataset.cat; renderGallery(); } });
$("#galleryList").addEventListener("click", (e) => {
  const ex = e.target.closest("[data-example]"), use = e.target.closest("[data-use]");
  if (ex) {
    $("#gallery").close();
    $("#sql").value = state.byId[ex.dataset.example].example_sql;
    runSql(ex.dataset.example).then(() => $("#studio").scrollIntoView({ behavior: "smooth", block: "start" }));
  } else if (use) { $("#gallery").close(); selectChart(use.dataset.use); $("#studio").scrollIntoView({ behavior: "smooth", block: "start" }); }
});

/* ---------------------------------------------------------------- misc wiring */
function csvCell(v) { const s = v === null ? "" : String(v); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; }

$("#askForm").onsubmit = (e) => { e.preventDefault(); ask(); };
$("#runBtn").onclick = () => runSql();
$("#sql").addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); runSql(); } });
$("#copySql").onclick = () => navigator.clipboard && navigator.clipboard.writeText($("#sql").value);
$("#resetSql").onclick = () => { $("#sql").value = state.generatedSql; showError(""); };
$("#csvBtn").onclick = () => {
  if (!state.last) return;
  const text = [state.last.columns, ...state.last.rows].map((r) => r.map(csvCell).join(",")).join("\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type: "text/csv" })); a.download = "queryx_result.csv"; a.click();
};
$("#csv").onchange = async (e) => {
  const f = e.target.files[0]; if (!f) return;
  const fd = new FormData(); fd.append("file", f);
  try {
    const r = await api("/api/upload", { method: "POST", body: fd });
    $("#uploadMsg").textContent = `Imported ${r.rows} rows into table "${r.table}".`;
    loadSchema();
  } catch (err) { $("#uploadMsg").textContent = err.message; }
  e.target.value = "";
};

loadSchema(); loadExamples(); loadHistory(); loadCatalog();
