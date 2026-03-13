# Phase 1 — Terminal Chatbot

> Core chatbot with Claude API, conversation memory, and financial reconciliation system prompt.  
> Input: raw text pasted into terminal | Output: structured mismatch report

---

## How to Run

```bash
# Make sure you're in the finreconcile root with venv active
source venv/bin/activate

# Run the app
cd phase1
python app.py
```

---

## What It Does

- Accepts two financial datasets as plain text input
- Identifies every mismatch between the two datasets
- Ranks discrepancies by dollar impact (largest first)
- Explains the likely cause of each mismatch in plain English
- Suggests what the finance team should investigate next
- Maintains conversation memory across the session

---

## Commands

| Command | Action |
|---|---|
| Paste your data + Enter | Send message to Claude |
| `reset` | Clear conversation history and start fresh |
| `quit` | Exit the program |

---

## Test Input

Copy and paste the following into the terminal when prompted with `You:` to test the bot end to end.

**Test Case 1 — Basic Mismatch Detection**
```
Stripe records:
INV-001  $12,500  Acme Corp      Jan 5
INV-002  $8,200   Beta LLC       Jan 8
INV-003  $3,400   Gamma Inc      Jan 12
INV-004  $6,100   Delta Co       Jan 15

QuickBooks records:
INV-001  $12,500  Acme Corp      Jan 5
INV-002  $7,900   Beta LLC       Jan 9
INV-003  $3,400   Gamma Inc      Jan 12
INV-005  $2,200   Epsilon Ltd    Jan 18

Find all mismatches and tell me what to investigate.
```

**Test Case 2 — Follow-up Question (tests conversation memory)**
```
Which of these mismatches should the finance team fix first and why?
```

**Test Case 3 — Reset and fresh reconciliation**
```
reset
```
Then paste a new dataset to confirm memory is cleared.

---

## Expected Output

### For Test Case 1

The bot should produce a full comparison table followed by ranked mismatches:

```
## Full Dataset Comparison

| Invoice | Stripe Amount | QB Amount | Stripe Date | QB Date | Status         |
|---------|--------------|-----------|-------------|---------|----------------|
| INV-001 | $12,500      | $12,500   | Jan 5       | Jan 5   | ✅ Match        |
| INV-002 | $8,200       | $7,900    | Jan 8       | Jan 9   | ❌ Mismatch     |
| INV-003 | $3,400       | $3,400    | Jan 12      | Jan 12  | ✅ Match        |
| INV-004 | $6,100       | —         | Jan 15      | —       | ❌ Missing in QB |
| INV-005 | —            | $2,200    | —           | Jan 18  | ❌ Missing in Stripe |

Stripe Total: $30,200 | QuickBooks Total: $26,100 | Net Difference: $4,100
```

**Mismatches ranked by dollar impact:**

| Rank | Invoice | Impact | Issue |
|---|---|---|---|
| 1 | INV-004 | $6,100 | Present in Stripe, missing in QuickBooks |
| 2 | INV-005 | $2,200 | Present in QuickBooks, missing in Stripe |
| 3 | INV-002 | $300 | Amount mismatch + 1 day date discrepancy |

**Explanations the bot should provide:**
- INV-004 → Payment collected in Stripe but never recorded in QuickBooks. Likely a sync failure or manual entry omission.
- INV-005 → Recorded in QuickBooks but not in Stripe. Likely paid via wire/check outside of Stripe.
- INV-002 → $300 gap on Beta LLC. Possible partial payment or manual typo in QuickBooks. Date difference suggests it was entered the following day.

---

### For Test Case 2

The bot should remember the previous reconciliation context (no need to re-paste data) and respond with a prioritized recommendation such as:

```
Fix INV-004 first — $6,100 is the largest unaccounted amount and it exists 
in Stripe (meaning the customer may have already paid) but has no record in 
QuickBooks. This is a revenue recognition risk. Confirm with the bank and 
create the entry manually if payment is confirmed.
```

---

### For Test Case 3 (reset)

The bot should print:
```
Conversation reset.
```

And then have zero memory of the previous session. If you ask "what were the invoices we just discussed?" it should say it has no prior context.

---

## Known Limitations (Phase 1)

| Limitation | Status | Fixed In |
|---|---|---|
| Multi-line paste splits into multiple messages | Terminal `input()` reads line by line | Phase 2 — Streamlit UI |
| No file upload — data must be pasted as text | No file handler yet | Phase 3 — CSV upload |
| Conversation history lost on quit | In-memory only, no persistence | Phase 3 — local DB |
| No visual UI | Terminal only | Phase 2 — Streamlit |

---

## Screenshots

See the `images/` folder for sample output.

| File | Description |
|---|---|
| `01_first_api_response.png` | First successful API response |
| `02_reconciliation_output.png` | Full mismatch detection output |

---

*Phase 1 complete — March 2026*
'EOF'
