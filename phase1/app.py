import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
conversation_history = []

SYSTEM_PROMPT = """
You are a financial reconciliation assistant for finance teams.

You will be given two sets of financial records (e.g. from Stripe vs QuickBooks,
or bank statement vs internal ledger).

Your job:
1. Identify every mismatch between the two datasets
2. Rank mismatches by dollar impact (largest first)
3. Explain in plain English why each mismatch likely occurred
4. Suggest what the finance team should investigate next

Rules:
- Only work with data the user provides — never invent numbers
- Always use structured output: tables or numbered lists
- If data is unclear or incomplete, ask one clarifying question
- Be concise — finance professionals are busy
"""

def chat(user_message):
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=conversation_history
    )

    reply = response.content[0].text

    conversation_history.append({
        "role": "assistant",
        "content": reply
    })

    return reply

def main():
    print("=" * 50)
    print("  FinReconcile — Financial Reconciliation Bot")
    print("  Type 'quit' to exit | Type 'reset' to clear")
    print("=" * 50 + "\n")

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Goodbye.")
            break
        if user_input.lower() == "reset":
            conversation_history.clear()
            print("Conversation reset.\n")
            continue

        response = chat(user_input)
        print(f"\nFinReconcile: {response}\n")

if __name__ == "__main__":
    main()