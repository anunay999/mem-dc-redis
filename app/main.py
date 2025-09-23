import argparse
from typing import Optional

from vector_store import ingest_memory, search_memories


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="mem-dc-redis CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest a memory")
    ingest_parser.add_argument("snippet", type=str, help="Memory snippet text")
    ingest_parser.add_argument(
        "--type",
        dest="memory_type",
        type=str,
        default="generic",
        help="Type of memory (e.g., semantic, episodic, etc.)",
    )
    ingest_parser.add_argument(
        "--model",
        dest="model_name",
        type=str,
        default="all-MiniLM-L6-v2",
        help="SentenceTransformers model to use for embeddings",
    )

    search_parser = subparsers.add_parser("search", help="Search memories with KNN")
    search_parser.add_argument("query", type=str, help="Search query text")
    search_parser.add_argument("--k", type=int, default=5, help="Top K results")
    search_parser.add_argument(
        "--type",
        dest="memory_type",
        type=str,
        default=None,
        help="Optional type filter (e.g., semantic, episodic)",
    )
    search_parser.add_argument(
        "--model",
        dest="model_name",
        type=str,
        default="all-MiniLM-L6-v2",
        help="SentenceTransformers model to use for query embeddings",
    )

    args = parser.parse_args(argv)

    if args.command == "ingest":
        key = ingest_memory(snippet=args.snippet, memory_type=args.memory_type, model_name=args.model_name)
        print(key)
        return 0
    if args.command == "search":
        results = search_memories(query=args.query, k=args.k, memory_type=args.memory_type, model_name=args.model_name)
        import json as _json
        print(_json.dumps(results, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
