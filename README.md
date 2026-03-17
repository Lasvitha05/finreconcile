# FinReconcile — Project Documentation

> **AI-Powered Financial Reconciliation Agent**  
> Built with Python + Anthropic Claude API + AWS S3 + Streamlit  
> Author: Lasvitha | Started: March 2026

---

## Table of Contents

1. [Project Vision](#1-project-vision)
2. [Why This Exists](#2-why-this-exists)
3. [Project Roadmap](#3-project-roadmap)
4. [Tech Stack](#4-tech-stack)
5. [Project Structure](#5-project-structure)
6. [Phase 1 — Terminal Chatbot](#6-phase-1--terminal-chatbot)
7. [Phase 2 — Streamlit UI](#7-phase-2--streamlit-ui)
8. [Phase 3 — CSV Upload + Pandas Engine](#8-phase-3--csv-upload--pandas-engine)
9. [Phase 4 — Autonomous Agent + AWS S3](#9-phase-4--autonomous-agent--aws-s3)
10. [Phase 5 — Data Transformation + Write-back](#10-phase-5--data-transformation--write-back)
11. [Bugs & Fixes Log](#11-bugs--fixes-log)
12. [Key Design Decisions](#12-key-design-decisions)
13. [How to Run](#13-how-to-run)
14. [Git Commit Convention](#14-git-commit-convention)

---

## 1. Project Vision

FinReconcile is an AI-powered financial data engineering agent that autonomously reconciles financial records across two data sources, detects mismatches and anomalies, transforms data with calculated columns, and writes results back to AWS S3 — all through natural language instructions.

**The problem it solves:**  
Finance teams spend 3–5 days every month manually reconciling data across systems like Stripe and QuickBooks in Excel. Numbers never match, the process is error-prone, and nobody knows the data is wrong until an executive spots it in a board meeting. FinReconcile replaces that manual process entirely.

**Who pays for it:**  
CFOs and Controllers at Series A–C startups and mid-size companies who feel this pain every single month.

---

## 2. Why This Exists

This project was deliberately chosen over a generic "FinBot" because:

- Generic financial chatbots are commodity — every bootcamp grad is building one
- The real pain in finance is not asking questions, it is the messy data that exists before any question gets answered
- This problem requires ETL + data quality + AI together — a combination that pure AI engineers struggle to build
- Finance teams already budget for reconciliation tools, meaning you are replacing existing spend not creating a new budget line

---

## 3. Project Roadmap

```
Phase 1  ✅  Core chatbot — terminal-based, API connection, conversation memory
Phase 2  ✅  Streamlit UI — proper text input, chat window, reset button
Phase 3  ✅  CSV upload — AI column mapping, pandas engine, dashboard, on-demand charts
Phase 4  ✅  Autonomous agent — AWS S3, tool use, SQLite persistence, load sessions
Phase 5  ✅  Data transformation — calculated columns, clean, enrich, aggregate, write-back to S3
```

Each phase is a standalone working product. No phase breaks the one before it.

---

## 4. Tech Stack

| Tool | Purpose | Version |
|---|---|---|
| Python | Core language | 3.11 |
| anthropic | Official Claude API SDK | 0.84.0 |
| python-dotenv | Load API keys from .env file | 0.21.0 |
| streamlit | UI framework (Phase 2+) | latest |
| pandas | Programmatic reconciliation + transformations | latest |
| boto3 | AWS SDK — S3 fetch and write-back | latest |
| plotly | Interactive charts — bar, donut pie | latest |
| sqlite3 | Local database — built into Python, zero setup | built-in |
| pyarrow | Parquet file support for S3 sources | latest |
| Git + GitHub | Version control + portfolio | — |

---

## 5. Project Structure

```
finreconcile/
│
├── .env                             ← API keys (never commit this to Git)
├── .gitignore                       ← excludes .env, venv, *.db
├── requirements.txt                 ← all installed libraries
├── README.md                        ← this file
├── FinReconcile_Documentation.docx  ← high-level technical documentation
├── generate_and_upload.py           ← realistic test data generator for S3
│
├── phase1/
│   ├── app.py                       ← terminal chatbot, core API logic
│   ├── README.md
│   └── images/
│
├── phase2/
│   ├── app.py                       ← Streamlit UI + conversation memory
│   ├── README.md
│   └── images/
│
├── phase3/
│   ├── app.py                       ← CSV upload + pandas engine + dashboard
│   ├── test_stripe.csv              ← sample test data
│   ├── test_quickbooks.csv          ← sample test data (different column names)
│   ├── README.md
│   └── images/
│
├── phase4/
│   ├── app.py                       ← autonomous agent + AWS S3 + SQLite
│   ├── README.md
│   └── images/
│
└── phase5/
    ├── app.py                       ← transform + write-back to S3
    ├── README.md
    └── images/
```

---

## 6. Phase 1 — Terminal Chatbot

### What It Does
Establishes the core pattern: Claude receives a system prompt defining its role as a financial reconciliation analyst, conversation history is manually passed on every API call to simulate memory, and a loop accepts user input from the terminal.

### Setup & Installation

```bash
mkdir finreconcile && cd finreconcile
python -m venv venv
source venv/bin/activate          # Mac/Linux
# venv\Scripts\activate           # Windows
pip install anthropic python-dotenv streamlit pandas
pip freeze > requirements.txt
mkdir phase1 phase2 phase3 phase4 phase5
echo "ANTHROPIC_API_KEY=your_key_here" > .env
git init
echo "venv/" > .gitignore && echo ".env" >> .gitignore && echo "*.db" >> .gitignore
git add . && git commit -m "project scaffold"
```

> ⚠️ Never commit your `.env` file. Your API key is a secret.

### Code Walkthrough

**Block 1 — Imports**
- `sys.path.append` tells Python to look one folder up — needed because app.py lives inside `phase1/`
- `Anthropic` is the official SDK that connects to Claude's API
- `load_dotenv` reads your `.env` file and loads the API key silently

**Block 2 — Client and Memory Setup**
- `client = Anthropic()` opens the connection to Claude
- `conversation_history = []` is the chatbot's memory — every message stored as a list of dictionaries

**Block 3 — System Prompt**  
The most important part of the project. It is the job description handed to Claude before every conversation — defines role, format, and rules. This single prompt is the core product logic.

**Block 4 — The `chat()` Function**  
Every call: appends user message → sends full history to Claude → extracts reply → appends reply to history → returns reply.

> **Key insight:** Claude has no memory by default. Every API call is stateless. The `conversation_history` list is manually passed on every call to simulate memory. This is how every chatbot works under the hood.

**Block 5 — The `main()` Loop**  
Continuous loop: takes terminal input → calls `chat()` → prints response. `reset` clears history, `quit` exits.

### Execution Flow

```
User types message
       │
       ▼
Appended to conversation_history as {"role": "user"}
       │
       ▼
client.messages.create(system=SYSTEM_PROMPT, messages=conversation_history)
       │
       ▼
Claude returns response → text extracted
       │
       ▼
Reply appended as {"role": "assistant"}
       │
       ▼
Printed to terminal → loop repeats
```

### Sample Run

| Invoice | Stripe | QuickBooks | Status |
|---|---|---|---|
| INV-001 | $12,500 | $12,500 | ✅ Match |
| INV-002 | $8,200 | $7,900 | ❌ $300 mismatch + 1 day date diff |
| INV-003 | $3,400 | $3,400 | ✅ Match |
| INV-004 | $6,100 | — | ❌ Missing in QuickBooks |
| INV-005 | — | $2,200 | ❌ Missing in Stripe |

**Net difference detected:** $4,100  
**Ranked by impact:** INV-004 ($6,100) → INV-005 ($2,200) → INV-002 ($300)

### Run
```bash
cd phase1 && python app.py
# Type 'reset' to clear history | 'quit' to exit
```

---

## 7. Phase 2 — Streamlit UI

### What It Does
Replaces the terminal with a browser-based interface. Sidebar for data entry, main panel for chat, follow-up bar that unlocks after first analysis.

**Problems fixed from Phase 1:**
- Multi-line paste no longer splits into multiple messages (`st.text_area` submits on button click)
- Product is now showable — runs in the browser at `localhost:8501`
- Data entry and conversation are visually separated

### System Prompt Upgrade
Phase 2 introduced a v2 system prompt with explicit `FIRST ANALYSIS` and `FOLLOW-UP QUESTIONS` sections after observing that the Phase 1 prompt produced vague follow-up answers.

> **Key lesson:** The system prompt is the product. A weak prompt produces weak output regardless of UI quality. Iterate on this more than anything else.

### Run
```bash
cd phase2 && streamlit run app.py
```

---

## 8. Phase 3 — CSV Upload + Pandas Engine

### What It Does
The most significant architectural shift. Claude stops doing the math — pandas takes over.

**Workflow:** Upload CSV → AI maps column names to standard schema → pandas computes all mismatches programmatically → Claude receives pre-computed results and explains them.

**Why this matters:** Claude is good at explanation and reasoning, not arithmetic. Offloading computation to pandas makes results faster, cheaper on tokens, and more accurate.

### Key Features
- AI column mapping — handles different column names across systems (e.g. `invoice_id` vs `ref_number`)
- Dashboard: 4 metric cards, mismatch bar chart, full reconciliation table
- On-demand pie charts — triggered by keywords (`pie`, `chart`, `visualize`) — not shown by default
- Session persistence to JSON on disk
- Downloadable CSV reconciliation report

### Test Files Included
Two sample CSVs with intentionally different column names to demonstrate AI mapping:
- `test_stripe.csv` — columns: `invoice_id`, `total_amount`, `payment_date`, `client_name`
- `test_quickbooks.csv` — columns: `ref_number`, `amount`, `date_recorded`, `customer`

### Run
```bash
pip install plotly
cd phase3 && streamlit run app.py
```

---

## 9. Phase 4 — Autonomous Agent + AWS S3

### What It Does
The product becomes genuinely agentic. Claude is given a tool registry and decides what to call and in what order — no fixed pipeline. Data is fetched directly from AWS S3 with no manual file upload required.

### Agent Tools

| Tool | What Claude Uses It For |
|---|---|
| `list_s3_files` | Discover available files before fetching |
| `fetch_s3_file` | Pull CSV or Parquet directly from S3 |
| `run_reconciliation` | Merge datasets, find mismatches via pandas |
| `detect_anomalies` | Classify mismatches HIGH / MEDIUM / LOW |
| `query_database` | SELECT queries on SQLite history |
| `generate_report` | Format executive summary for CFO/Controller |

### Agentic Loop
```
User: "Reconcile January data"
       │
Claude thinks: "I need to list what's in S3 first"
→ calls list_s3_files
→ calls fetch_s3_file twice
→ calls run_reconciliation
→ calls detect_anomalies
→ synthesizes final response
```

### Anomaly Summary Report
Replaces the wall of individual alert cards with a clean structured report: 4 severity metric cards, top 5 HIGH issues visible, rest collapsed in expanders.

### Conversation Persistence
Every session saved to SQLite `conversations` table after every message. Load any past session from the sidebar — full conversation + dashboard restored exactly as it was.

### Generate Test Data for S3
```bash
pip install boto3 pyarrow
python generate_and_upload.py --bucket your-bucket --records 500 --months 3
```
Generates 500 realistic financial records per month × 3 months with ~8% mismatch rate baked in.

### Environment Variables Required
```
ANTHROPIC_API_KEY=sk-ant-...
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
```

### Run
```bash
cd phase4 && streamlit run app.py
```

---

## 10. Phase 5 — Data Transformation + Write-back

### What It Does
Phase 5 completes the data engineering loop. The agent can now modify data, not just analyze it. Twelve transformation operations cover the most common finance data tasks. Results write back to AWS S3 as a new file or overwriting the original.

### Transformation Operations

| Category | Operation | What It Does |
|---|---|---|
| Calculated | `add_risk_score` | Adds risk_score (0–3) and risk_label from anomaly data |
| Calculated | `add_variance_pct` | % variance between two numeric columns |
| Calculated | `add_flag` | Flag rows where column meets a threshold condition |
| Calculated | `add_month_column` | Extract month and month_name from a date column |
| Clean | `fill_nulls` | Fill null values with a default (one column or all) |
| Clean | `deduplicate` | Remove duplicate rows by column or across all |
| Clean | `standardize_amounts` | Strip $/, whitespace, round to 2dp |
| Clean | `standardize_dates` | Parse and reformat dates to standard format |
| Clean | `trim_strings` | Strip whitespace and uppercase string columns |
| Enrich | `enrich_from_s3` | Left-join with a reference file from S3 |
| Aggregate | `monthly_rollup` | Sum/count/avg by month — returns summary table |
| Aggregate | `category_totals` | Sum/count/avg by category — returns ranked table |

### Safety Principle
Claude never runs arbitrary Python `exec()`. It generates a structured JSON transformation spec. The app executes only predefined pandas operations. Safe, auditable, reversible.

### Transformation Flow
```
User: "Add a risk score and fill nulls, save as new file"
       │
       ▼
Claude calls preview_transform
generate_transform_spec() → JSON spec
apply_transformation() → pandas executes safely
       │
       ▼
Before/After preview shown in UI
Download available without committing to S3
       │
       ▼
User confirms → Claude calls transform_and_save
write_to_s3() → new file OR overwrite
Confirmation: rows, cols, S3 path, operations applied
```

### New Agent Tools in Phase 5

| Tool | When Used |
|---|---|
| `preview_transform` | Always before any write — shows before/after |
| `transform_and_save` | After preview, saves result to S3 |
| `aggregate_data` | Monthly rollups or category totals with auto bar chart |

### Example Natural Language Instructions
```
"Add a risk score column based on reconciliation anomaly severity"
"Fill all null values with UNKNOWN"
"Remove duplicate rows based on the invoice_ref column"
"Standardize the total_amount column and remove dollar signs"
"Create a monthly rollup using payment_date and total_amount"
"Save as a new file at transformed/stripe_enriched_march.csv"
```

### Run
```bash
pip install plotly boto3 pyarrow
cd phase5 && streamlit run app.py
```

---

## 11. Bugs & Fixes Log

| # | Phase | Issue | Root Cause | Fix |
|---|---|---|---|---|
| 1 | 1 | `ModuleNotFoundError: anthropic` in VS Code | VS Code used system Python not venv | `Cmd+Shift+P → Python: Select Interpreter → venv` |
| 2 | 1 | Multi-line paste split into multiple messages | `input()` reads one line at a time | Fixed in Phase 2 with `st.text_area()` |
| 3 | 1 | Conversation history lost after quit | Python list in RAM only | Expected — persistence added in Phase 4 |
| 4 | 2 | Follow-up answers were vague | System prompt had no follow-up instructions | Rewrote prompt with FOLLOW-UP QUESTIONS section |
| 5 | 3 | Bot responses showed italic gibberish and overflow | Markdown injected into raw HTML `<div>` | Replaced with `st.chat_message()` native component |
| 6 | 3 | Claude said it could not generate charts | Claude is a text model — it cannot render images | Charts built from pandas dataframe by app, Claude bypassed |
| 7 | 4 | 0% match rate on all 992 records | AI mapped `payment_id` (system ID) not `invoice_ref` (business ref) | Updated column mapping prompt to prefer business reference |
| 8 | 4 | 992 alert cards flooded the screen | Every mismatch rendered as individual card | Summary report: top 5 table + collapsed expanders |
| 9 | 4 | Conversations lost on browser close | `st.session_state` wiped on reload | `conversations` table in SQLite, saved after every message |
| 10 | 5 | Agent could run unsafe transformations | No execution boundary on AI-generated code | JSON spec pattern — Claude generates ops, app executes predefined functions only |

---

## 12. Key Design Decisions

**Pandas computes, Claude explains**  
From Phase 3 onward, pandas performs all mathematical comparisons. Claude receives pre-computed results and generates human-readable explanations. This is faster, cheaper on API tokens, and more accurate than asking Claude to compare text directly.

**No `exec()` for transformations**  
Claude generates a structured JSON spec, not Python code. The app executes only operations from a closed set of 12 predefined pandas functions. Safe and auditable.

**Preview before write**  
No transformation writes to S3 without a preview step. Users see before/after and can download locally without committing to cloud storage.

**Business ref over system ID for joins**  
The AI column mapper explicitly prefers business reference columns (e.g. `invoice_ref`) over internal system IDs (e.g. `payment_id`) as join keys — the fix for the critical 0% match rate bug in Phase 4.

**On-demand charts**  
Charts only render when explicitly requested via keywords (`pie`, `chart`, `visualize`). The dashboard stays clean by default. Claude is bypassed entirely for chart requests — no wasted tokens.

**Conversation persistence by default**  
Every message is saved to SQLite after each agent response. No manual save required. Any session is recoverable from the sidebar Load button.

---

## 13. How to Run

```bash
# Clone and set up
git clone https://github.com/Lasvitha05/finreconcile
cd finreconcile
python -m venv venv
source venv/bin/activate
pip install anthropic streamlit pandas plotly boto3 python-dotenv pyarrow

# Add your keys
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
echo "AWS_ACCESS_KEY_ID=AKIA..." >> .env
echo "AWS_SECRET_ACCESS_KEY=..." >> .env
echo "AWS_REGION=us-east-1" >> .env

# Run any phase
python phase1/app.py                  # terminal only
streamlit run phase2/app.py           # browser UI
streamlit run phase3/app.py           # CSV upload + dashboard
streamlit run phase4/app.py           # autonomous agent + S3
streamlit run phase5/app.py           # transform + write-back

# Generate S3 test data (Phase 4/5)
python generate_and_upload.py --bucket your-bucket --records 500 --months 3
```

---

## 14. Git Commit Convention

```bash
git commit -m "feat: add phase5 transformation and write-back"
git commit -m "fix: column mapping prefers business ref over system ID"
git commit -m "docs: update README with all 5 phases"
git commit -m "chore: add railway deployment config"
```

Format: `type: short description`  
Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

---

*Last updated: All 5 phases complete — March 2026*
