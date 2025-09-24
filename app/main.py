import argparse
from typing import Optional

from vector_store import create_memory, search_memories


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
        "--user-id",
        dest="user_id",
        type=str,
        default=None,
        help="Optional userId to associate with this memory",
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

    args = parser.parse_args(argv)

    if args.command == "ingest":
        key = create_memory(snippet=args.snippet, memory_type=args.memory_type, user_id=args.user_id)
        print(key)
        return 0
    if args.command == "search":
        results = search_memories(query=args.query, k=args.k, memory_type=args.memory_type)
        import json as _json
        print(_json.dumps(results, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
