# Plan: Spending Charts on Dashboard

## Overview

Add two visual charts to the dashboard below the transaction grid:
- **Doughnut chart** — category-wise expense breakdown
- **Bar chart** — monthly income vs expense for the last 6 months

Both charts sit side-by-side in one full-width panel. Data comes from the existing `transactions` JS array — no new API or server changes needed. Chart.js is loaded via CDN.

---

## Sub-Task 1: Load Chart.js via CDN in `base.html`

**Intent:** Make Chart.js available on every page without any build step.

**Expected Outcomes:**
- `Chart` global is available in dashboard JS after page load

**Todo List:**
1. Add `<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>` inside `<head>` in `base.html`

**Relevant Context:**
- [`templates/base.html`](templates/base.html) — currently only has the CSS link in `<head>`

**Status:** [x] done

---

## Sub-Task 2: Add Charts Panel HTML in `dashboard.html`

**Intent:** Add a new full-width panel below the existing `dashboard-grid` section containing two `<canvas>` elements — one for the doughnut chart and one for the bar chart.

**Expected Outcomes:**
- A `.charts-panel` with two canvases (`#chart-category` and `#chart-monthly`) renders below the transaction grid
- Both canvases are side-by-side on desktop, stacked on mobile

**Todo List:**
1. After the closing `</section>` of `.dashboard-grid` (before the edit modal `<div>`), add a new `<section class="charts-panel panel">` containing:
   - A panel heading: eyebrow "INSIGHTS", h2 "Spending overview"
   - A `.charts-grid` div with two `<canvas>` elements: `id="chart-category"` and `id="chart-monthly"`

**Relevant Context:**
- [`templates/dashboard.html`](templates/dashboard.html:27) — insert after line 27, before the edit modal div
- Match existing panel/eyebrow/h2 heading style from other panels

**Status:** [x] done

---

## Sub-Task 3: Add `renderCharts()` JS in `dashboard.html`

**Intent:** Write a `renderCharts()` function that reads the existing `transactions` array, computes category totals and monthly income/expense, then draws/updates both Chart.js charts. Call it from the end of `render()` so charts always stay in sync.

**Expected Outcomes:**
- Doughnut chart shows expense totals per category (only `type === 'expense'` transactions)
- Bar chart shows income vs expense per month for the last 6 calendar months
- Charts update automatically when transactions are added, edited, or deleted
- If no data exists, charts render empty/zero gracefully

**Todo List:**
1. Declare `let categoryChart = null, monthlyChart = null;` at the top of the script block
2. Write `renderCharts()`:
   - **Doughnut data**: reduce `transactions` where `type === 'expense'` grouped by `category` → labels + amounts
   - **Bar data**: build last-6-months labels (`YYYY-MM`), sum income and expense per month from transaction `date` field
   - If `categoryChart` already exists call `.destroy()` before recreating (avoids Chart.js canvas reuse warning)
   - Create doughnut on `#chart-category` with `type: 'doughnut'`, use project color palette (greens, red, yellow)
   - Create bar on `#chart-monthly` with `type: 'bar'`, two datasets: Income (green) and Expense (red), `plugins.legend` enabled
3. At the end of `render()`, call `renderCharts()`

**Relevant Context:**
- [`templates/dashboard.html`](templates/dashboard.html:60) — `render()` function, add `renderCharts()` call at its end
- Existing CSS color vars: `--green: #1f7a5a`, `--red: #ba554d`, `--yellow: #f1c75b` — use these hex values directly in Chart.js dataset colors
- Transaction `date` field format is `YYYY-MM-DD` — slice first 7 chars for month key

**Status:** [x] done

---

## Sub-Task 4: Add Chart CSS in `style.css`

**Intent:** Style the charts panel and responsive grid so both charts are side-by-side on desktop and stacked on mobile.

**Expected Outcomes:**
- `.charts-panel` displays full-width below the dashboard grid with consistent padding/border
- `.charts-grid` is a 2-column grid on desktop, 1-column on mobile (≤800px)
- Canvas height is constrained so charts don't grow too tall

**Todo List:**
1. Add `.charts-panel` — `margin-top:22px` (spacing from grid above)
2. Add `.charts-grid` — `display:grid; grid-template-columns:1fr 1fr; gap:28px; align-items:center`
3. Add `.charts-grid canvas` — `max-height:300px`
4. In the `@media (max-width:800px)` rule, add `.charts-grid { grid-template-columns:1fr; }`

**Relevant Context:**
- [`static/style.css`](static/style.css:26) — add new rules before the `@media` blocks; extend existing `@media (max-width:800px)` rule

**Status:** [x] done
