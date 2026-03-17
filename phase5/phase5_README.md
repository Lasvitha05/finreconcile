# Phase 5 — Data Transformation + Write-back to S3

> The agent can now transform your data, not just analyze it.  
> Add calculated columns, clean data, enrich from a third source,
> aggregate into rollups — then write the result back to S3.
> All triggered by natural language. All previewed before saving.

---

## What Changed From Phase 4

| Phase 4 | Phase 5 |
|---|---|
| Read-only — fetches and analyzes | Read + Write — transforms and saves back to S3 |
| No data modification | 12 predefined transformation operations |
| No aggregations | Monthly rollups + category totals with auto bar chart |
| No preview before write | Always preview before any S3 write |
| Claude could not touch data | Agent decides transformation spec, pandas executes it safely |

---

## Architecture

```
User: "Add a risk score, clean nulls, save as a new file"
              │
              ▼
    Claude calls preview_transform
              │
              ▼
    generate_transform_spec() → Claude returns JSON spec
    (not raw code — structured operations only)
              │
              ▼
    apply_transformation() → pandas executes each op safely
              │
              ▼
    Before/After preview shown in UI
    Download available without saving
              │
              ▼
    User confirms → Claude calls transform_and_save
              │
              ▼
    write_to_s3() → new file OR overwrite (user chooses)
              │
              ▼
    Confirmation card: rows, cols, S3 path, operations applied
```

**Safety principle:** Claude never runs arbitrary Python `exec()`.
It generates a structured JSON spec. The app executes only
predefined pandas operations. Safe, auditable, reversible.

---

## Transformation Operations

| Category | Operation | What It Does |
|---|---|---|
| **Calculated** | `add_risk_score` | Adds risk_score (0–3) and risk_label from anomaly data |
| **Calculated** | `add_variance_pct` | % variance between two numeric columns |
| **Calculated** | `add_flag` | Flag rows where column meets a threshold condition |
| **Calculated** | `add_month_column` | Extract month and month_name from a date column |
| **Clean** | `fill_nulls` | Fill null values with a default (one column or all) |
| **Clean** | `deduplicate` | Remove duplicate rows by column or across all columns |
| **Clean** | `standardize_amounts` | Strip $/, whitespace, round to 2dp |
| **Clean** | `standardize_dates` | Parse and reformat dates to a standard format |
| **Clean** | `trim_strings` | Strip whitespace and uppercase all string columns |
| **Enrich** | `enrich_from_s3` | Left-join with a reference file from S3 |
| **Aggregate** | `monthly_rollup` | Sum/count/avg by month — returns summary table |
| **Aggregate** | `category_totals` | Sum/count/avg by category — returns ranked table |

---

## How to Run

```bash
source venv/bin/activate
cd phase5
streamlit run app.py
```

---

## How to Use — Transformation Flow

**Step 1 — Fetch data first**
Use "Reconcile Now" or type:
```
"Fetch stripe/2026_03_march.csv from bucket my-bucket as Stripe"
```

**Step 2 — Preview a transformation**
In the sidebar Transform Data section, or type:
```
"Add a risk score column to the Stripe dataset based on anomaly severity"
"Clean nulls and standardize the amount column in QuickBooks data"
"Add a variance percentage column comparing Stripe and QuickBooks amounts"
```
A before/after table appears. Nothing is written yet.

**Step 3 — Save to S3**
Enter an output key in the sidebar, or type:
```
"Save the transformed Stripe data to bucket my-bucket at key transformed/stripe_with_risk_march.csv"
```
Choose a new key (non-destructive) or the original key (overwrite).

**Step 4 — Aggregate**
```
"Create a monthly rollup of the Stripe dataset using payment_date and total_amount"
"Show category totals for QuickBooks grouped by memo column"
```
Results shown in a table + bar chart. Downloadable as CSV.

---

## Example Natural Language Instructions

### Add Calculated Columns
```
"Add a risk score column based on reconciliation anomaly severity"
"Add a variance percentage column between total_amount and amount columns"
"Flag any records where the amount is over 50000"
"Add a month column from the payment_date field"
```

### Clean Data
```
"Fill all null values with UNKNOWN"
"Remove duplicate rows based on the invoice_ref column"
"Standardize the total_amount column — remove dollar signs and round to 2 decimal places"
"Standardize all dates to YYYY-MM-DD format"
"Trim and uppercase all string columns"
```

### Enrich
```
"Enrich the Stripe data with the reference file at s3://my-bucket/reference/customers.csv joining on client_name"
```

### Aggregate
```
"Create a monthly rollup using payment_date and total_amount"
"Show me category totals grouped by category column summing total_amount"
```

### Write Back
```
"Save as a new file at transformed/stripe_enriched_march.csv"
"Overwrite the original file at stripe/2026_03_march.csv"
```

---

## Expected Output

### After preview_transform
```
TRANSFORM PREVIEW UI
┌─────────────────────────────────────────────────────┐
│ 👁 Transform Preview                                │
│ Preview of Stripe — review before saving to S3      │
│                                                     │
│ 1. Added risk_score (0-3) and risk_label columns    │
│                                                     │
│  BEFORE                    AFTER                    │
│  ┌──────────────────┐      ┌────────────────────┐   │
│  │ invoice_ref  amt │      │ invoice_ref amt rs │   │
│  │ INV-001    12500 │  →   │ INV-001   12500  0 │   │
│  │ INV-002     8200 │      │ INV-002    8200  3 │   │
│  └──────────────────┘      └────────────────────┘   │
│                                                     │
│  [📥 Download Transformed CSV]                      │
└─────────────────────────────────────────────────────┘
```

### After transform_and_save
```
✅ LAST TRANSFORM SAVED
┌──────┐ ┌──────┐ ┌──────┐
│ 500  │ │  11  │ │  S3  │
│ Rows │ │ Cols │ │ Written│
└──────┘ └──────┘ └──────┘

s3://my-bucket/transformed/stripe_with_risk_march.csv
- Added risk_score (0-3) and risk_label columns
[full table preview]
[📥 Download Transformed Data]
```

### After aggregate_data (monthly rollup)
```
📊 AGGREGATION RESULT
monthly rollup on total_amount: 3 months aggregated

month     total_amount  record_count  avg_amount
2026-01   4,521,234.50  500           9,042.47
2026-02   4,398,871.20  498           8,832.07
2026-03   4,612,445.80  500           9,224.89

[bar chart]
[📥 Download Aggregation CSV]
```

---

## Sidebar — Transform Data Section

Appears automatically once any data is fetched.

```
🔧 TRANSFORM DATA
Dataset to transform: [Stripe ▼]
Instruction: [Add a risk score column...]

[👁 Preview]  Output key: [transformed/out.csv]
              [💾 Save to S3]

[📊 Monthly Rollup]
[📂 Category Totals]
```

---

## Agent Tool Summary (Phase 5 Additions)

| Tool | When Claude Uses It |
|---|---|
| `preview_transform` | Always before writing — shows before/after |
| `transform_and_save` | After preview, when user confirms save |
| `aggregate_data` | When user asks for rollups or summaries |

Combined with Phase 4 tools:
`list_s3_files` → `fetch_s3_file` → `run_reconciliation` →
`detect_anomalies` → `preview_transform` → `transform_and_save`

---

## Bugs & Fixes Log

| # | Issue | Root Cause | Fix |
|---|---|---|---|
| 1 | Agent could run arbitrary pandas code unsafely | No execution boundary | Transformation spec pattern — Claude generates JSON ops, app executes predefined functions only |
| 2 | Transforms wrote to S3 without user seeing result | No preview step | `preview_transform` always called before `transform_and_save` — system prompt enforces this |
| 3 | Aggregation had no visual output | Text-only result | Auto bar chart rendered from aggregation dataframe using plotly |

---

## Known Limitations (Phase 5)

| Limitation | Notes |
|---|---|
| Only 12 predefined transform operations | Covers 90% of real use cases. Custom Python ops intentionally excluded for safety. |
| No multi-step chained transforms in one call | Call preview_transform once per operation type |
| No email alerts after anomaly detection | Can be added with boto3 SES post-MVP |
| No user auth | Single user only — multi-user needs login layer |

---

## Full Phase Roadmap (Complete)

```
Phase 1  ✅  Terminal chatbot + Claude API + conversation memory
Phase 2  ✅  Streamlit UI + multi-line input + session reset
Phase 3  ✅  CSV upload + AI column mapping + pandas engine + dashboard
Phase 4  ✅  Autonomous agent + AWS S3 + SQLite persistence + load sessions
Phase 5  ✅  Data transformation + calculated columns + write-back to S3
```

---

## Screenshots

See the `images/` folder for sample output.

| File | Description |
|---|---|
| `01_transform_sidebar.png` | Transform Data section in sidebar after data is fetched |
| `02_preview_transform.png` | Before/after transform preview in main panel |
| `03_risk_score_added.png` | risk_score and risk_label columns visible in after table |
| `04_transform_saved_confirmation.png` | Confirmation card after write to S3 |
| `05_monthly_rollup.png` | Monthly rollup table + bar chart |
| `06_category_totals.png` | Category totals grouped and ranked |
| `07_enrich_from_s3.png` | Dataset enriched with third reference file |
| `08_agent_tool_chain.png` | Tool call log showing full fetch→reconcile→transform chain |

---

## Commit

```bash
git add phase5/app.py
git add phase5/README.md
git add phase5/images/
git add README.md    # all 5 phases now ✅

git commit -m "feat: phase5 data transformation and write-back to S3

- 12 predefined transformation operations (add columns, clean, enrich, aggregate)
- natural language → JSON transform spec → safe pandas execution (no exec())
- preview_transform always shown before any S3 write
- transform_and_save: new file or overwrite — user chooses
- aggregate_data: monthly rollup + category totals with auto bar chart
- transform sidebar section unlocks after data is fetched
- phase 5 UI: preview panel, save confirmation card, aggregation result"

git push
```

---

*Phase 5 complete — March 2026*  
*Full product: 5 phases from terminal chatbot to autonomous data engineering agent*
