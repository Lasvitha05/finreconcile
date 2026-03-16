# FinReconcile — Project Documentation

> **AI-Powered Financial Reconciliation Assistant**  
> Built with Python + Anthropic Claude API  
> Author: Lasvitha | Started: March 2026

---

## Table of Contents

1. [Project Vision](#1-project-vision)
2. [Why This Exists](#2-why-this-exists)
3. [Project Roadmap](#3-project-roadmap)
4. [Tech Stack](#4-tech-stack)
5. [Project Structure](#5-project-structure)
6. [Phase 1 — Setup & Installation](#6-phase-1--setup--installation)
7. [Phase 1 — Code Walkthrough](#7-phase-1--code-walkthrough)
8. [Phase 1 — Execution Flow](#8-phase-1--execution-flow)
9. [Phase 1 — Sample Run](#9-phase-1--sample-run)
10. [Bugs & Fixes Log](#10-bugs--fixes-log)
11. [Q&A Log](#11-qa-log)
12. [How to Run](#12-how-to-run)

---

## 1. Project Vision

FinReconcile is an AI-powered financial reconciliation assistant that helps finance teams at small and mid-size companies automatically detect, explain, and prioritize mismatches between two financial data sources — for example, Stripe vs QuickBooks, or a bank statement vs an internal ledger.

**The problem it solves:**  
Finance teams spend 3–5 days every month manually reconciling data across multiple systems in Excel. Numbers never match, the process is error-prone, and no one enjoys it. FinReconcile replaces that manual process with a conversational AI that finds discrepancies instantly, ranks them by dollar impact, and explains what to investigate.

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
Phase 3  ✅  CSV upload — auto-detect mismatches before sending to Claude
Phase 4  ✅  Agent mode — connect to live databases and AWS data sources
```

Each phase is a standalone working product. No phase breaks the one before it.

---

## 4. Tech Stack

| Tool | Purpose | Version |
|---|---|---|
| Python | Core language | 3.11 |
| anthropic | Official Claude API SDK | 0.84.0 |
| python-dotenv | Load API key from .env file | 0.21.0 |
| streamlit | UI framework (Phase 2+) | latest |
| pandas | CSV handling (Phase 3+) | latest |
| Git + GitHub | Version control + portfolio | — |

---

## 5. Project Structure

```
finreconcile/
│
├── .env                  ← API key (never commit this to Git)
├── .gitignore            ← excludes .env and venv from Git
├── requirements.txt      ← all installed libraries
├── README.md             ← this file
│
├── phase1/
│   └── app.py            ← terminal chatbot, core API logic
│
├── phase2/
│   └── app.py            ← Streamlit UI + conversation memory (coming)
│
├── phase3/
│   └── app.py            ← CSV upload + auto mismatch detection (coming)
│
└── phase4/
    └── app.py            ← full agent with live data sources (coming)
```

---

## 6. Phase 1 — Setup & Installation

### Prerequisites
- Python 3.10 or higher
- A terminal (Mac Terminal, VS Code Terminal, or any CLI)
- An Anthropic API key from console.anthropic.com

### Step-by-step Installation

```bash
# 1. Create project folder
mkdir finreconcile
cd finreconcile

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate          # Mac/Linux
# venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install anthropic python-dotenv streamlit pandas

# 4. Save dependencies to requirements.txt
pip freeze > requirements.txt

# 5. Create folder structure
mkdir phase1 phase2 phase3 phase4

# 6. Add your API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# 7. Initialize Git
git init
echo "venv/" > .gitignore
echo ".env" >> .gitignore
git add .
git commit -m "project scaffold — phase 1"
```

> ⚠️ **Critical:** Never commit your `.env` file. Your API key is a secret. The `.gitignore` file above protects you from accidentally pushing it to GitHub.

---

## 7. Phase 1 — Code Walkthrough

**File:** `phase1/app.py`

### Block 1 — Imports

```python
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anthropic import Anthropic
from dotenv import load_dotenv
```

- `sys.path.append` tells Python to look one folder up for files — needed because app.py lives inside the `phase1/` subfolder
- `Anthropic` is the official SDK that connects to Claude's API
- `load_dotenv` reads your `.env` file and loads your API key silently into the environment

---

### Block 2 — Client and Memory Setup

```python
load_dotenv()
client = Anthropic()
conversation_history = []
```

- `load_dotenv()` picks up the API key from `.env` — without this, authentication fails
- `client = Anthropic()` opens the connection to Claude — like dialing a phone line
- `conversation_history = []` is the chatbot's memory. Every message sent and received is stored here as a list of dictionaries

---

### Block 3 — System Prompt

```python
SYSTEM_PROMPT = """
You are a financial reconciliation assistant...
"""
```

This is the most important part of the entire project. It is the job description handed to Claude before every conversation. It defines:

- What role Claude plays (financial reconciliation analyst)
- What to do with the data (find mismatches, rank by impact, explain causes)
- What format to respond in (structured tables and numbered lists)
- What rules it must never break (never invent numbers, always ask if unclear)

This single prompt is the core product logic. It gets refined more than any other part of the codebase.

---

### Block 4 — The `chat()` Function (The Engine)

```python
def chat(user_message):
    conversation_history.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=conversation_history
    )

    reply = response.content[0].text

    conversation_history.append({"role": "assistant", "content": reply})

    return reply
```

What happens on every single call:

1. The user message is appended to `conversation_history` with `role: user`
2. The **entire conversation history** is sent to Claude along with the system prompt
3. Claude reads everything and generates a response
4. `response.content[0].text` extracts the actual text from the response object
5. Claude's reply is appended to `conversation_history` with `role: assistant`
6. The reply is returned to the main loop for printing

> **Key insight:** Claude has no memory by default. Every API call is stateless. The `conversation_history` list is manually passed on every call to simulate memory. This is how every chatbot works under the hood.

---

### Block 5 — The `main()` Loop

```python
def main():
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "quit":   # exits the program
        if user_input.lower() == "reset":  # clears conversation memory
        response = chat(user_input)
        print(f"FinReconcile: {response}")
```

A continuous loop that:
- Takes user input from the terminal
- Passes it to `chat()`
- Prints the response
- Repeats until the user types `quit`

The `reset` command clears `conversation_history` — useful when starting a new reconciliation without old context interfering.

---

## 8. Phase 1 — Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        PHASE 1 FLOW                             │
└─────────────────────────────────────────────────────────────────┘

  User types message in terminal
           │
           ▼
  message appended to conversation_history
  as {"role": "user", "content": "..."}
           │
           ▼
  client.messages.create() called with:
  ┌──────────────────────────────────┐
  │  model: claude-sonnet-4-6        │
  │  system: SYSTEM_PROMPT           │
  │  messages: conversation_history  │  ← full history every time
  └──────────────────────────────────┘
           │
           ▼
  Claude API processes and returns response object
           │
           ▼
  response.content[0].text extracted
           │
           ▼
  reply appended to conversation_history
  as {"role": "assistant", "content": "..."}
           │
           ▼
  reply printed to terminal
           │
           ▼
  loop repeats ──────────────────────────────────┐
                                                  │
  user types "reset" → history cleared           │
  user types "quit"  → program exits             │
                                                  │
  ◄─────────────────────────────────────────────┘

  Memory lifetime:
  ┌─────────────────────────────────────────────┐
  │  Program starts  → history = []             │
  │  Chatting        → history grows in RAM     │
  │  quit / crash    → history lost forever     │
  │  reset           → history manually cleared │
  └─────────────────────────────────────────────┘
  Note: Persistence (saving to disk/DB) added in Phase 3+
```

---

## 9. Phase 1 — Sample Run

**Input given:**
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
```

**Output summary:**

| Invoice | Stripe | QuickBooks | Status |
|---|---|---|---|
| INV-001 | $12,500 | $12,500 | ✅ Match |
| INV-002 | $8,200 | $7,900 | ❌ $300 mismatch + 1 day date diff |
| INV-003 | $3,400 | $3,400 | ✅ Match |
| INV-004 | $6,100 | — | ❌ Missing in QuickBooks |
| INV-005 | — | $2,200 | ❌ Missing in Stripe |

**Net difference detected:** $4,100  
**Ranked by impact:** INV-004 ($6,100) → INV-005 ($2,200) → INV-002 ($300)

---

## 10. Bugs & Fixes Log

| # | Issue | Root Cause | Fix |
|---|---|---|---|
| 1 | `ModuleNotFoundError: No module named 'anthropic'` when running in VS Code | VS Code was using system Python (`/usr/bin/python3`) instead of the venv | `Cmd+Shift+P` → Python: Select Interpreter → select the venv path |
| 2 | Multi-line pasted input split into multiple separate messages | Python's `input()` reads one line at a time. Each Enter key sent a new message | Known limitation — fixed in Phase 2 with Streamlit's multi-line text box |
| 3 | Conversation history lost after quitting | `conversation_history` is a Python list in RAM only — no persistence | Expected Phase 1 behavior — persistence added in Phase 3 |

---

## 11. Q&A Log

**Q: Why use the Anthropic API directly instead of Claude Code CLI?**  
A: Claude Code CLI is a coding assistant tool that requires a Pro/Max subscription ($20–100/month). The Anthropic API is pay-per-use (~$5 gets you through all of Phase 1 and 2). More importantly, calling the API directly means you understand exactly what is happening under the hood — you build the product, you own the logic. Claude Code abstracts that away. Use the API to learn; use Claude Code later to accelerate.

**Q: Why does VS Code show library errors even after pip install?**  
A: VS Code has its own Python interpreter setting that defaults to system Python. When you pip install inside a virtual environment, those packages only exist in that venv. You need to explicitly point VS Code to your venv interpreter via `Cmd+Shift+P → Python: Select Interpreter`.

**Q: Why did pasting multi-line data break the conversation into multiple messages?**  
A: Python's built-in `input()` reads one line at a time and sends immediately on each Enter key press. The full multi-line paste got split into individual messages. This is resolved in Phase 2 by using Streamlit's `st.text_area()` which accepts multi-line input and only submits on button click.

**Q: Is conversation_history stored permanently?**  
A: No. It is a Python list that lives in RAM only for the duration of the program run. When the user types `quit` or the program crashes, the list is gone. This is intentional for Phase 1 simplicity. In Phase 3 we will add persistence to a local file or database, which is actually a key product differentiator for finance teams who need audit logs.

---

## 12. How to Run

```bash
# Navigate to your project
cd finreconcile

# Activate virtual environment
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# Run Phase 1
cd phase1
python app.py

# Commands inside the app
# Type your financial data and press Enter to send
# Type 'reset' to clear conversation history
# Type 'quit' to exit
```

---

## Git Commit Convention (Use This Going Forward)

```bash
git add .
git commit -m "phase1: working terminal chatbot with reconciliation prompt"
git commit -m "phase2: add streamlit UI and multiline input"
git commit -m "fix: VS Code interpreter issue documented"
git commit -m "docs: update README with phase 1 QA log"
```

Format: `type(scope): short description`  
Types: `feat`, `fix`, `docs`, `refactor`, `test`

---

*Last updated: Phase 1 complete — March 2026*
