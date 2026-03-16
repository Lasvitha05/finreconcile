# Phase 3 — CSV Upload + AI Column Mapping + Dashboard

> Terminal → UI → **Real product.**  
> Upload two CSVs, AI maps the columns, pandas finds every mismatch,
> Claude explains them. Charts generated on demand from the chat bar.

---

## What Changed From Phase 2

| Phase 2 | Phase 3 |
|---|---|
| User pastes raw text | User uploads CSV files |
| Claude does the math | Pandas computes mismatches, Claude only explains |
| No visual dashboard | Metric cards + bar chart + on-demand pie charts |
| No file persistence | Sessions saved to JSON on disk |
| Columns had to match | AI auto-maps different column names |

**This is where it stops feeling like a chatbot and starts feeling like a product.**

---

## Architecture

```
CSV Upload (Source A + Source B)
         │
         ▼
Claude maps columns to standard schema
(invoice_id → id, total_amount → amount, etc.)
         │
         ▼
Pandas merges both dataframes on ID column
Finds: amount mismatches, missing records, date gaps
         │
         ▼
Dashboard renders:
  - 4 metric cards (match rate, exposure, matched, issues)
  - Bar chart: mismatch type breakdown
  - Full reconciliation table
  - Download button (CSV report)
         │
         ▼
Claude receives pre-computed results → explains causes + action plan
         │
         ▼
Follow-up chat bar unlocks
  - Text questions → Claude answers
  - Chart keywords  → Pie charts render inline (no Claude call)
         │
         ▼
Session saved to reconciliation_sessions.json
```

**Key principle:** Claude explains results. Pandas computes them.
Claude is never asked to do math — only to interpret it.

---

## How to Run

```bash
# From finreconcile root with venv active
source venv/bin/activate

# Install new dependency
pip install plotly

# Run Phase 3
cd phase3
streamlit run app.py
```

Opens at **http://localhost:8501**

---

## UI Layout

```
┌──────────────────────┬─────────────────────────────────────────────┐
│  SIDEBAR             │  MAIN PANEL                                 │
│                      │                                             │
│  📂 Source A         │  FinReconcile                               │
│  Label: [Stripe]     │  ─────────────────────────────────────────  │
│  [Upload CSV]        │                                             │
│  ✓ 5 rows · 4 cols   │  📊 DASHBOARD                               │
│  [Preview ▼]         │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐      │
│                      │  │ 33%  │ │$8.6K │ │ 2/5  │ │  3   │      │
│  📂 Source B         │  │Match │ │Expos.│ │Matchd│ │Issues│      │
│  Label: [QuickBooks] │  └──────┘ └──────┘ └──────┘ └──────┘      │
│  [Upload CSV]        │                                             │
│  ✓ 5 rows · 4 cols   │  🔍 MISMATCH BREAKDOWN                      │
│  [Preview ▼]         │  [bar chart]                                │
│                      │                                             │
│  ✓ Both files ready  │  📋 FULL RECONCILIATION TABLE               │
│                      │  [dataframe]                                │
│  [🔍 Analyze]        │                                             │
│  [↺ Reset    ]       │  ⬇️ EXPORT                                  │
│                      │  [📥 Download Report CSV]                   │
│  🗂 PAST SESSIONS     │                                             │
│  Stripe vs QB        │  💬 AI ANALYSIS                             │
│  2026-03-16 · 33%    │  [chat messages]                            │
│                      │─────────────────────────────────────────────│
│                      │  Ask a follow-up question...            [→] │
└──────────────────────┴─────────────────────────────────────────────┘
```

---

## How to Use

**Step 1 — Upload**
Upload Source A and Source B CSVs in the sidebar. A preview expander
shows the first 3 rows. Badge turns green when both are uploaded.

**Step 2 — Analyze**
Click **Analyze Mismatches**. Three things happen in sequence:
1. AI maps your column names to the standard schema
2. Pandas computes all mismatches mathematically
3. Claude receives the results and generates the explanation

**Step 3 — Review Dashboard**
- Match rate, total financial exposure, records matched, issues found
- Bar chart breaking down mismatch types
- Full side-by-side reconciliation table with status per record
- Download the full report as a timestamped CSV

**Step 4 — Ask Follow-ups**
Use the chat bar for text questions. Claude remembers full context.
For charts, type any of: `pie chart`, `show me a chart`, `visualize`,
`graph` — pie charts render inline without calling Claude.

**Step 5 — Past Sessions**
Every session is saved to `reconciliation_sessions.json`. The last 5
sessions appear in the sidebar with timestamp and match rate.

---

## Test Files

Two test CSVs are included in this folder. They intentionally use
**different column names** to demonstrate AI column mapping.

**test_stripe.csv** columns: `invoice_id`, `total_amount`, `payment_date`, `client_name`  
**test_quickbooks.csv** columns: `ref_number`, `amount`, `date_recorded`, `customer`

Claude maps both to the standard schema: `id`, `amount`, `date`, `name`

### test_stripe.csv
```
invoice_id,total_amount,payment_date,client_name
INV-001,12500.00,2024-01-05,Acme Corp
INV-002,8200.00,2024-01-08,Beta LLC
INV-003,3400.00,2024-01-12,Gamma Inc
INV-004,6100.00,2024-01-15,Delta Co
INV-006,4750.00,2024-01-20,Zeta Partners
```

### test_quickbooks.csv
```
ref_number,amount,date_recorded,customer
INV-001,12500.00,2024-01-05,Acme Corp
INV-002,7900.00,2024-01-09,Beta LLC
INV-003,3400.00,2024-01-12,Gamma Inc
INV-005,2200.00,2024-01-18,Epsilon Ltd
INV-006,4750.00,2024-01-21,Zeta Partners
```

---

## Expected Output

### Dashboard Metrics

| Metric | Expected Value |
|---|---|
| Match Rate | 33.3% (2 of 6 unique records fully match) |
| Total Exposure | $8,600.00 |
| Records Matched | 2 / 6 |
| Issues Found | 4 |

### Reconciliation Table

| ID | Stripe | QuickBooks | Status |
|---|---|---|---|
| INV-001 | $12,500 | $12,500 | ✅ Match |
| INV-002 | $8,200 | $7,900 | ❌ Amount Mismatch ($300 diff) |
| INV-003 | $3,400 | $3,400 | ✅ Match |
| INV-004 | $6,100 | — | ❌ Missing in QuickBooks |
| INV-005 | — | $2,200 | ❌ Missing in Stripe |
| INV-006 | $4,750 | $4,750 | ⚠️ Date Mismatch (Jan 20 vs Jan 21) |

### AI Column Mapping (auto-detected)

| Stripe Column | → | Standard |
|---|---|---|
| `invoice_id` | → | `id` |
| `total_amount` | → | `amount` |
| `payment_date` | → | `date` |
| `client_name` | → | `name` |

| QuickBooks Column | → | Standard |
|---|---|---|
| `ref_number` | → | `id` |
| `amount` | → | `amount` |
| `date_recorded` | → | `date` |
| `customer` | → | `name` |

---

## On-Demand Pie Charts

Charts are **not shown by default**. Type any of the following in the
chat bar to render them inline:

```
pie chart
show me a chart
visualize this
plot the amounts
graph
```

Two donut charts appear inline in the chat — one per source, showing
amount distribution across all invoices for that source.

**Why on demand?** No visual clutter by default. Finance professionals
often don't need charts — they need the numbers. Charts are available
when explicitly requested.

**Why not ask Claude?** Claude is a text model — it cannot generate
images or charts. The charts are built directly from the pandas
dataframe by the app. Claude is bypassed entirely for chart requests,
saving API tokens and giving instant results.

---

## Session Persistence

Every reconciliation run is saved to `reconciliation_sessions.json`
in the project root. Saved data includes:

```json
{
  "abc12345": {
    "timestamp": "2026-03-16T13:55:00",
    "label_a": "Stripe",
    "label_b": "QuickBooks",
    "column_mapping": { ... },
    "summary": {
      "total_records": 6,
      "matched": 2,
      "match_rate": 33.3,
      "total_exposure": 8600.00
    }
  }
}
```

The last 5 sessions are displayed in the sidebar. This is the
foundation for Phase 4's audit trail feature.

---

## Bugs & Fixes Log

| # | Issue | Root Cause | Fix |
|---|---|---|---|
| 1 | Bot responses showed italic gibberish and text overflow | Claude returns markdown but it was injected into raw HTML `<div>` which browsers don't parse | Replaced custom HTML divs with `st.chat_message()` — Streamlit's native markdown-aware component |
| 2 | Claude said it couldn't generate pie charts | Claude is a text model — it genuinely cannot render visuals | Charts now built from pandas dataframe by the app. Claude is bypassed entirely for chart requests |
| 3 | Pie charts cluttered the dashboard on every load | Charts shown by default regardless of need | `show_pie_charts` session flag — charts only render when user explicitly asks |

---

## Known Limitations (Phase 3)

| Limitation | Fixed In |
|---|---|
| No live database connection — still requires file upload | Phase 4 — connect to AWS/real data sources |
| AI column mapping can fail on very unusual column names | Phase 4 — add manual override fallback |
| Sessions stored in flat JSON — no querying or filtering | Phase 4 — migrate to SQLite |
| Local only — no shareable link | Phase 4+ |
| No user authentication | Post-MVP |

---

## Screenshots

See the `images/` folder for sample output.

| File | Description |
|---|---|
| `01_upload_ready.png` | Both CSVs uploaded, badge green |
| `02_dashboard_metrics.png` | Metric cards and mismatch bar chart |
| `03_reconciliation_table.png` | Full side-by-side comparison table |
| `04_ai_column_mapping.png` | Column mapping expander showing auto-detection |
| `05_claude_analysis.png` | Claude's explanation in chat |
| `06_pie_charts_on_demand.png` | Pie charts rendered after user asked for them |
| `07_past_sessions_sidebar.png` | Past sessions appearing in sidebar |

---

*Phase 3 complete — March 2026*  
*Next: Phase 4 — Live database connection + AWS integration*
