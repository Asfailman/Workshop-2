"""
Module 1 - Entry Point
======================
Interactive CLI for testing the NLP conversational guidance assistant.

Usage:
    python main.py

Type a message and press Enter to receive a structured JSON response.
Type 'quit' or 'exit' to stop.
"""

import json
import sys

from nlp_module import NLPModule

SEP  = "-" * 52
SEP2 = "=" * 52


def print_result(result: dict):
    """Pretty-print the NLP result, separating user-facing and internal fields."""
    core = {
        "intent":      result.get("intent"),
        "entities":    result.get("entities"),
        "reply":       result.get("reply"),
        "destination": result.get("destination"),
    }

    print("\n" + SEP)
    print("  OUTPUT")
    print(SEP)
    print(json.dumps(core, indent=2, ensure_ascii=False))

    if "_context" in result:
        print("\n  CONTEXT STATE")
        print(SEP)
        print(json.dumps(result["_context"], indent=2, ensure_ascii=False))

    if "_handoff" in result:
        print("\n  HANDOFF PAYLOAD")
        print(SEP)
        print(json.dumps(result["_handoff"], indent=2, ensure_ascii=False))

    if "_error" in result:
        print(f"\n  [!] ERROR: {result['_error']}")

    print(SEP + "\n")


import time

def main():
    print(SEP2)
    print("  Module 1 - Conversational AI Guidance Assistant")
    print("  Powered by Ollama (llama3.2:3b)")
    print(SEP2)
    print("  Type a message to begin. Type 'exit' to quit.")
    print(SEP2 + "\n")

    try:
        nlp = NLPModule()
    except ValueError as e:
        print(f"\n[ERROR] Initialization failed: {e}\n")
        return

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nSession ended.")
            break

        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit"}:
            print("\nGoodbye! Have a great day.")
            break

        print("  Processing...", end="\r", flush=True)
        t0 = time.time()
        result = nlp.process(user_input)
        elapsed = round(time.time() - t0, 2)
        print(f"  [Response generated in {elapsed}s]       ")
        print_result(result)


if __name__ == "__main__":
    main()
