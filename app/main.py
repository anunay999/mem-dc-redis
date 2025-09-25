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
    ingest_parser.add_argument("text", type=str, help="Memory text")
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
    ingest_parser.add_argument(
        "--memory-id",
        dest="memory_id",
        type=str,
        default=None,
        help="Optional memory ID for upsert functionality",
    )
    ingest_parser.add_argument(
        "--status",
        dest="status",
        type=str,
        default="active",
        help="Memory status (e.g., active, archived, deleted)",
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
        "--status",
        dest="status",
        type=str,
        default=None,
        help="Optional status filter (e.g., active, archived, deleted)",
    )

    args = parser.parse_args(argv)

    if args.command == "create":
        logger.info(
            "CLI create: text_len=%s type=%s user_id_set=%s memory_id=%s status=%s",
            len(args.text),
            args.memory_type,
            bool(args.user_id),
            args.memory_id or "auto-generated",
            args.status,
        )
        key = create_memory(text=args.text, memory_type=args.memory_type, memory_id=args.memory_id)
        print(key)
        return 0
    if args.command == "search":
        logger.info("CLI search: query_len=%s k=%s type=%s status=%s", len(args.query), args.k, args.memory_type or "<any>", args.status or "<any>")
        results = search_memories(query=args.query, k=args.k, memory_type=args.memory_type, status=args.status)
        # Convert SearchResponseItem objects to dictionaries for JSON serialization
        results_dict = [item.model_dump() for item in results]
        import json as _json
        print(_json.dumps(results_dict, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
