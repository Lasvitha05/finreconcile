# Phase 2 — Streamlit UI

> Terminal chatbot upgraded to a browser-based interface with sidebar data
> input, styled chat window, and follow-up conversation support.  
> Run locally at http://localhost:8501

---

## What Changed From Phase 1

| Problem in Phase 1 | Fix in Phase 2 |
|---|---|
| Multi-line paste split into multiple messages | `st.text_area()` — paste full dataset, submit once |
| Terminal only — nothing to show anyone | Full browser UI at localhost:8501 |
| No visual separation between data input and chat | Sidebar for data entry, main panel for conversation |
| Follow-up questions required re-pasting data | Chat bar unlocks after first analysis, memory persists |

**Core AI logic is identical to Phase 1.** Phase 2 only changes the interface,
not the brain. This is intentional — never change two things at once.

---

## How to Run

```bash
# From the finreconcile root with venv active
source venv/bin/activate

# Run Phase 2
cd phase2
streamlit run app.py
```

Opens automatically at **http://localhost:8501**

---

## UI Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  SIDEBAR                    │  MAIN PANEL                       │
│                             │                                   │
│  📋 Source A                │  FinReconcile                     │
│  Label: [Stripe        ]    │  ─────────────────────────────    │
│  ┌─────────────────────┐    │                                   │
│  │ INV-001  $12,500... │    │  YOU                              │
│  │ INV-002  $8,200...  │    │  ┌─────────────────────────────┐ │
│  └─────────────────────┘    │  │ Stripe records: INV-001...  │ │
│                             │  └─────────────────────────────┘ │
│  📋 Source B                │                                   │
│  Label: [QuickBooks    ]    │  FINRECONCILE                     │
│  ┌─────────────────────┐    │  ┌─────────────────────────────┐ │
│  │ INV-001  $12,500... │    │  │ Found 3 mismatches...       │ │
│  │ INV-002  $7,900...  │    │  │ | INV | Stripe | QB | ...   │ │
│  └─────────────────────┘    │  └─────────────────────────────┘ │
│                             │                                   │
│  ✓ Both datasets ready      │                                   │
│                             ├───────────────────────────────────│
│  [🔍 Analyze Mismatches]    │  Ask a follow-up question...  [→] │
│  [↺ Reset Session     ]     │                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features

**Sidebar**
- Two labeled text areas — Source A and Source B
- Editable labels (e.g. "Stripe", "Bank Statement", "QuickBooks", "Ledger")
- Status badge — orange warning until both datasets filled, green when ready
- Analyze button — disabled until both datasets are pasted
- Reset button — clears full session state and reloads the page

**Main Panel**
- Dark themed chat UI with styled message bubbles
- User messages — right-aligned, dark blue background
- Bot messages — left-aligned, teal left border for visual distinction
- Welcome state shown when no messages exist yet
- Chat input bar — disabled until first analysis runs, then unlocks for follow-ups

**Session Memory**
- Full conversation history persisted in `st.session_state`
- Follow-up questions reference previously submitted data automatically
- Memory cleared only when Reset is clicked or the browser tab is closed

---

## How to Use

**Step 1 — Paste your data**
Enter a label for each source, paste datasets into Source A and Source B.
Badge turns green when both are filled.

**Step 2 — Analyze**
Click **Analyze Mismatches**. Results appear as a comparison table with
ranked mismatches and explanations.

**Step 3 — Ask follow-ups**
Use the chat bar at the bottom. Claude remembers full context — no
re-pasting required. Example follow-ups:
- *"Which mismatch should I fix first?"*
- *"What's the most likely reason for the INV-002 discrepancy?"*
- *"Summarize this for my CFO in 3 bullet points"*

**Step 4 — Reset**
Click **Reset Session** to clear everything and start a new reconciliation.

---

## Test Inputs

### Source A — Stripe
```
INV-001  $12,500  Acme Corp      Jan 5
INV-002  $8,200   Beta LLC       Jan 8
INV-003  $3,400   Gamma Inc      Jan 12
INV-004  $6,100   Delta Co       Jan 15
```

### Source B — QuickBooks
```
INV-001  $12,500  Acme Corp      Jan 5
INV-002  $7,900   Beta LLC       Jan 9
INV-003  $3,400   Gamma Inc      Jan 12
INV-005  $2,200   Epsilon Ltd    Jan 18
```

---

## Expected Output

### After clicking Analyze Mismatches

**Comparison table:**

| Invoice | Stripe | QuickBooks | Stripe Date | QB Date | Status |
|---|---|---|---|---|---|
| INV-001 | $12,500 | $12,500 | Jan 5 | Jan 5 | ✅ Match |
| INV-002 | $8,200 | $7,900 | Jan 8 | Jan 9 | ❌ Amount + Date mismatch |
| INV-003 | $3,400 | $3,400 | Jan 12 | Jan 12 | ✅ Match |
| INV-004 | $6,100 | — | Jan 15 | — | ❌ Missing in QuickBooks |
| INV-005 | — | $2,200 | — | Jan 18 | ❌ Missing in Stripe |

**Net difference: $4,100**  
**Mismatches ranked:** INV-004 ($6,100) → INV-005 ($2,200) → INV-002 ($300)

### After follow-up: *"Which should I fix first?"*

Claude references INV-004 by name, explains the $6,100 is the largest
unaccounted amount and a revenue recognition risk — exists in Stripe
(customer likely paid) but has no QuickBooks entry.

### After clicking Reset

Chat clears, welcome state reappears, chat bar returns to disabled state.

---

## System Prompt (v2 — Upgraded From Phase 1)

Phase 2 introduced a significantly improved system prompt after observing
that follow-up answers in Phase 1 were too generic.

```python
SYSTEM_PROMPT = """
You are FinReconcile, a senior financial reconciliation analyst with 15 years
of experience at Big 4 accounting firms.

FIRST ANALYSIS — when given two datasets:
1. Produce a full comparison table with every record side by side
2. Rank every mismatch by dollar impact — largest first
3. For each mismatch write: what the discrepancy is, the most likely cause
   (timing difference, manual entry error, payment method mismatch, system
   sync failure, partial payment, duplicate entry), and the exact action
   the finance team should take
4. End with a summary: total records, matched count, mismatch count,
   net dollar difference

FOLLOW-UP QUESTIONS — when the user asks for clarification:
- Always reference the specific invoice numbers and amounts from the data
- Give concrete, actionable answers — not generic explanations
- If asked to explain better or go deeper, pick the single most important
  mismatch and walk through the full investigation steps a real accountant
  would take
- Never ask the user to re-paste data already in the conversation

TONE: Direct, precise, professional. Talking to a CFO or Controller
who has no time for vague answers.
"""
```

> **Key lesson:** The system prompt is the product. A weak prompt produces
> weak output regardless of UI quality. Iterate on this more than anything
> else in the codebase.

---

## Bugs & Fixes Log

| # | Issue | Root Cause | Fix |
|---|---|---|---|
| 1 | Follow-up answers were vague | System prompt lacked follow-up instructions | Rewrote prompt with dedicated FOLLOW-UP QUESTIONS section |
| 2 | Analyze button active with empty inputs | No input validation | Added `disabled=not (source_a_data.strip() and source_b_data.strip())` |
| 3 | Chat bar accessible before first analysis | No gate on input | `data_submitted` flag disables chat until first analysis runs |

---

## Known Limitations (Phase 2)

| Limitation | Fixed In |
|---|---|
| User must manually copy-paste data — still manual work | Phase 3 — CSV upload |
| No programmatic detection — fully LLM dependent | Phase 3 — pandas pre-processing layer |
| Conversation history lost on browser close | Phase 3 — local persistence |
| No export of reconciliation report | Phase 3+ |
| Local only — no shareable link | Phase 4+ |

---

## Screenshots

See the `images/` folder for sample output.

| File | Description |
|---|---|
| `01_welcome_state.png` | App on first load |
| `02_data_pasted.png` | Both datasets filled, badge green |
| `03_analysis_output.png` | Full mismatch report in chat |
| `04_followup_response.png` | Follow-up answered with full context |

---

*Phase 2 complete — March 2026*  
*Next: Phase 3 — CSV upload + programmatic mismatch detection*
