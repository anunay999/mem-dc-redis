import argparse
import logging
from typing import Optional

from vector_store import create_memory, search_memories


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)-5s %(message)s",
    )
    logger = logging.getLogger(__name__)
    parser = argparse.ArgumentParser(description="mem-dc-redis CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("create", help="Create a memory")
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

    if args.command == "create":
        logger.info(
            "CLI create: snippet_len=%s type=%s user_id_set=%s",
            len(args.snippet),
            args.memory_type,
            bool(args.user_id),
        )
        key = create_memory(snippet=args.snippet, memory_type=args.memory_type)
        print(key)
        return 0
    if args.command == "search":
        logger.info("CLI search: query_len=%s k=%s type=%s", len(args.query), args.k, args.memory_type or "<any>")
        results = search_memories(query=args.query, k=args.k, memory_type=args.memory_type)
        import json as _json
        print(_json.dumps(results, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
