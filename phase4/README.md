# Phase 4 — Autonomous Agent + AWS S3 + Conversation Persistence

> The product becomes an agent.  
> No file uploads. No fixed scripts. Claude decides what tools to call,
> fetches live data from AWS S3, detects anomalies, saves everything to
> SQLite, and lets you pick up any past session exactly where you left off.

---

## What Changed From Phase 3

| Phase 3 | Phase 4 |
|---|---|
| User uploads CSV files manually | Agent fetches directly from AWS S3 |
| Fixed sequence: upload → pandas → Claude | Claude decides tool order autonomously |
| One-shot analysis per session | Full conversation persisted to SQLite |
| No history between sessions | Load any past session from sidebar |
| Wall of individual alert cards | Clean anomaly summary report |
| Columns had to be guessed correctly | Improved AI mapping — prefers business ref over system ID |

---

## Architecture

```
User gives instruction in natural language
             │
             ▼
    ┌─────────────────────────────────┐
    │        AGENTIC LOOP             │
    │  Claude decides which tools     │
    │  to call and in what order      │
    └────────────────┬────────────────┘
                     │
       ┌─────────────┼──────────────┐
       ▼             ▼              ▼
  list_s3_files  fetch_s3_file  query_database
  run_reconciliation  detect_anomalies
  generate_report
       │
       ▼
  Pandas computes mismatches
  Claude explains results
       │
       ▼
  SQLite saves:
  - reconciliation_runs
  - anomalies
  - conversations (full message history)
       │
       ▼
  Dashboard + Anomaly Report + Download
  Follow-up chat bar (context preserved)
       │
       ▼
  Past Sessions sidebar → Load any session
```

**Key principle:** Claude is never asked to do math.
Pandas computes. Claude explains. Tools fetch. SQLite remembers.

---

## Agent Tools

| Tool | What It Does |
|---|---|
| `list_s3_files` | Discover available files in a bucket before fetching |
| `fetch_s3_file` | Pull a CSV or Parquet file directly from S3 |
| `run_reconciliation` | Merge both datasets, find all mismatches via pandas |
| `detect_anomalies` | Classify mismatches by severity (HIGH/MEDIUM/LOW) |
| `query_database` | Run SELECT queries on the local SQLite database |
| `generate_report` | Produce a formatted executive summary for CFO/Controller |

---

## How to Run

```bash
# From finreconcile root with venv active
source venv/bin/activate

# Install new dependencies
pip install boto3 pyarrow plotly

# Add AWS credentials to .env
echo "AWS_ACCESS_KEY_ID=your_key" >> .env
echo "AWS_SECRET_ACCESS_KEY=your_secret" >> .env
echo "AWS_REGION=us-east-1" >> .env

# Generate and upload realistic test data to S3
python generate_and_upload.py --bucket your-bucket-name --records 500 --months 3

# Run Phase 4
cd phase4
streamlit run app.py
```

Opens at **http://localhost:8501**

---

## Generating Realistic Test Data

```bash
# Generates 500 records/month × 3 months = 1,500 records per source
# Uploads directly to your S3 bucket
python generate_and_upload.py --bucket your-bucket --records 500 --months 3
```

**S3 structure after running:**
```
s3://your-bucket/
├── stripe/2026_01_january.csv      (500 records)
├── stripe/2026_02_february.csv     (500 records)
├── stripe/2026_03_march.csv        (500 records)
├── quickbooks/2026_01_january.csv  (~490 records with mismatches)
├── quickbooks/2026_02_february.csv (~490 records with mismatches)
└── quickbooks/2026_03_march.csv    (~490 records with mismatches)
```

**Realistic mismatches baked in:**

| Type | Rate | Simulates |
|---|---|---|
| Missing in QuickBooks | ~4% | Stripe sync failure |
| Amount mismatch | ~2% | Manual entry typo or partial payment |
| Date mismatch | ~2% | Entered next business day |
| Missing in Stripe | ~2% | Wire payment recorded only in QB |

---

## How to Use

**Step 1 — Configure S3**
Enter your bucket name, Source A key (e.g. `stripe/2026_03_march.csv`),
Source B key (e.g. `quickbooks/2026_03_march.csv`), and labels in the sidebar.

**Step 2 — Reconcile Now**
Click **Reconcile Now** or type a natural language instruction:
```
"Reconcile March data and alert me on anything over $1,000"
```
The agent autonomously: lists files → fetches both → maps columns → 
runs reconciliation → detects anomalies → explains results.

**Step 3 — Review Dashboard**
- 4 metric cards: match rate, total exposure, records matched, high alerts
- Anomaly Summary Report: top 5 HIGH issues visible, rest in expanders
- Full reconciliation table with status per record
- Download report as timestamped CSV

**Step 4 — Ask Follow-ups**
```
"What's the most likely root cause for the missing records?"
"Generate a CFO summary"
"Which invoices have been missing consistently?"
"Show me a chart"
```
Claude remembers full context — no re-fetching or re-pasting.

**Step 5 — Load Past Sessions**
Close the browser. Come back tomorrow. Click **Load** next to any past
session in the sidebar. Full conversation + dashboard restored exactly
as it was.

---

## Anomaly Report Structure

Replaces the wall of individual alert cards from Phase 3.

```
ANOMALY SUMMARY REPORT
┌──────┐ ┌──────┐ ┌──────┐ ┌──────────────┐
│  12  │ │  8   │ │  5   │ │  $43,200     │
│ HIGH │ │ MED  │ │ LOW  │ │ HIGH EXPOSURE│
└──────┘ └──────┘ └──────┘ └──────────────┘

Top 5 High Severity Issues
┌──────────────┬───────────────────────────────┬──────────┐
│ Invoice      │ Issue                         │ Exposure │
├──────────────┼───────────────────────────────┼──────────┤
│ INV-2026-001 │ Missing in QuickBooks         │ $84,981  │
│ INV-2026-047 │ Amount mismatch $300 diff     │ $8,200   │
│ ...          │ ...                           │ ...      │
└──────────────┴───────────────────────────────┴──────────┘

▶ View all 12 high severity issues    (expander)
▶ 8 Medium Severity Issues            (collapsed)
▶ 5 Low Severity Issues               (collapsed)
```

---

## Conversation Persistence

Every session is automatically saved to SQLite.

**What gets saved:**
- Full message history (every user message + every Claude response)
- Reconciliation results (match rate, exposure, all mismatches)
- Anomaly findings
- Source labels and timestamps

**Saved after:**
- Every reconciliation run
- Every follow-up message
- Every chart request

**Loading a session restores:**
- Complete conversation history in the chat panel
- Full dashboard with metrics and reconciliation table
- Source labels and run metadata
- Ability to continue asking follow-up questions

---

## SQLite Database Schema

```sql
-- Every reconciliation run
reconciliation_runs (
    id, timestamp, source_a, source_b,
    total_records, matched, match_rate,
    total_exposure, results_json
)

-- Every anomaly detected
anomalies (
    id, run_id, timestamp, severity,
    invoice_id, description, amount
)

-- Full conversation history per run
conversations (
    run_id, timestamp, source_a, source_b,
    messages_json, summary_json
)
```

**Inspect your database:**
```bash
sqlite3 phase4/finreconcile_agent.db

.tables
SELECT id, timestamp, match_rate, total_exposure FROM reconciliation_runs;
SELECT severity, COUNT(*) FROM anomalies GROUP BY severity;
.quit
```

---

## Auto-Scheduler

Set a reconciliation to run automatically every N minutes.

1. Configure S3 keys in the sidebar
2. Set interval (15 / 30 / 60 / 120 / 360 mins)
3. Click **▶ Start**
4. Agent runs on schedule — results saved to SQLite automatically
5. Click **⏹ Stop** to disable

---

## AI Column Mapping — Improvement Over Phase 3

Phase 3 sometimes picked internal system IDs (like `py_00110`) as the
join key instead of the business reference (`INV-2026-0110`), causing
0% match rates.

Phase 4 fixes this with an explicit rule in the mapping prompt:

> *"If one file has both a system ID and a business reference, always
> prefer the business reference — it will match across systems."*

The agent now correctly maps `invoice_ref` → `id` for Stripe and
`ref_number` → `id` for QuickBooks, producing accurate results.

---

## Environment Variables Required

```bash
# In finreconcile/.env
ANTHROPIC_API_KEY=sk-ant-...
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
```

---

## Bugs & Fixes Log

| # | Issue | Root Cause | Fix |
|---|---|---|---|
| 1 | 0% match rate on all records | AI mapped `payment_id` (system ID) instead of `invoice_ref` (business ref) as join key | Rewrote column mapping prompt to explicitly prefer business reference columns |
| 2 | 992 alert cards flooding the screen | Every mismatch rendered as individual card — no grouping | Replaced with summary report: 4 metric cards + top 5 table + collapsed expanders |
| 3 | Conversations lost on browser close | `st.session_state` wiped on reload | Added `conversations` table to SQLite, save after every message |
| 4 | No way to access previous runs | Past sessions were display-only with no load capability | Added Load button per session — restores full conversation + dashboard |

---

## Known Limitations (Phase 4)

| Limitation | Fixed In |
|---|---|
| Cannot write transformed data back to S3 | Phase 5 |
| No calculated columns or custom transformations | Phase 5 |
| No user authentication — single user only | Post-MVP |
| Scheduler runs in-process — stops if app restarts | Post-MVP (use Celery/cron) |
| No email alerts for HIGH severity anomalies | Phase 5 |

---

## Screenshots

See the `images/` folder for sample output.

| File | Description |
|---|---|
| `01_agent_console_welcome.png` | App on first load — agent console empty state |
| `02_s3_config_ready.png` | Sidebar configured with bucket and file keys |
| `03_tool_calls_visible.png` | Agent calling tools autonomously (tool call log) |
| `04_dashboard_metrics.png` | 4 metric cards after reconciliation |
| `05_anomaly_summary_report.png` | Clean summary report with top 5 HIGH issues |
| `06_reconciliation_table.png` | Full side-by-side comparison table |
| `07_followup_cfo_summary.png` | Claude generating CFO executive summary |
| `08_past_sessions_load.png` | Past sessions in sidebar with Load buttons |
| `09_session_restored.png` | Conversation fully restored after clicking Load |
| `10_scheduler_active.png` | Auto-scheduler running in sidebar |

---

## Commit

```bash
git add phase4/app.py
git add phase4/README.md
git add phase4/images/
git add generate_and_upload.py
git add README.md    # update Phase 4 from 🔲 to ✅

git commit -m "feat: phase4 autonomous agent with S3, SQLite persistence, load sessions

- agent tool loop: list_s3, fetch_s3, reconcile, anomalies, report, query_db
- AWS S3 direct data fetch — no manual file upload
- conversation persistence to SQLite — survives browser close
- load past sessions from sidebar — full conversation + dashboard restored
- anomaly summary report replaces wall of alert cards
- fixed AI column mapping to prefer business ref over system ID
- auto-scheduler with configurable interval
- realistic data generator: 500 records/month × 3 months"

git push
```

---

*Phase 4 complete — March 2026*  
*Next: Phase 5 — Data transformation, calculated columns, write-back to S3*
