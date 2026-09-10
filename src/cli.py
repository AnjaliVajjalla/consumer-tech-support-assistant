"""
Interactive command-line entry point for the Consumer Technology
Support Assistant. Ask any question, get a grounded, cited answer.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from generate import answer, langfuse  # noqa: E402


def main() -> None:
    print("Consumer Technology Support Assistant (Sony WH-1000XM5 / AirPods Pro 2)")
    print("Type a question, or 'quit' to exit.\n")

    while True:
        question = input("> ").strip()
        if not question:
            continue
        if question.lower() in {"quit", "exit"}:
            break

        result = answer(question)
        print(f"\n{result['answer']}\n")
        print("Sources:")
        for s in result["sources"]:
            print(f"  [{s['n']}] {s['product']} - {s['title']}")
            print(f"      {s['url']}")
        trace = result["trace"]
        print(f"Tokens used: {result['usage']['input_tokens']} in / {result['usage']['output_tokens']} out")
        print(
            f"Latency: retrieve {trace['retrieve_ms']}ms, "
            f"rerank {trace['rerank_ms']}ms, generate {trace['generate_ms']}ms"
        )
        langfuse.flush()
        print()


if __name__ == "__main__":
    main()
