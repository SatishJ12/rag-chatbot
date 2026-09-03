"""Interactive CLI REPL for the NovaCell RAG chatbot. Type 'quit' to exit."""
from chain import answer_stream
from config import GROQ_API_KEY


def main():
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY is not set. Copy .env.example to .env and add your key.")
        return

    print("NovaCell Support Assistant (CLI) — type 'quit' to exit.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not question:
            continue
        if question.lower() == "quit":
            print("Goodbye.")
            break

        print("Bot: ", end="", flush=True)
        token_stream, sources = answer_stream(question)
        for token in token_stream:
            print(token, end="", flush=True)
        print()

        if sources:
            print("\nSources:")
            for s in sources:
                print(f"  - [{s['source']}] {s['id']}")
        print()


if __name__ == "__main__":
    main()
