from __future__ import annotations

import argparse
import getpass
import logging
import os
import sys
from pathlib import Path

from .core import organize


def main() -> int:
    parser = argparse.ArgumentParser(description="Sort files by type and securely archive files untouched for a year.")
    parser.add_argument("--source", required=True, type=Path, help="Directory to scan")
    parser.add_argument("--target", required=True, type=Path, help="Base directory for sorted files and Deep_Archive.zip")
    parser.add_argument("--dry-run", action="store_true", help="List planned actions without changing files")
    parser.add_argument("--log", type=Path, help="Write the run log to this file (also prints to console)")
    parser.add_argument("--password", help="AES archive password (prefer FILE_ORGANIZER_PASSWORD environment variable)")
    args = parser.parse_args()

    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if args.log:
        args.log.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(args.log, encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=handlers)
    logger = logging.getLogger("file-organizer")
    password = args.password or os.environ.get("FILE_ORGANIZER_PASSWORD")
    if password is None and not args.dry_run and sys.stdin.isatty():
        password = getpass.getpass("Archive password (leave empty to skip old-file archiving): ") or None
    try:
        actions = organize(args.source, args.target, password, args.dry_run, logger)
        if not actions:
            logger.info("No files need organizing or archiving.")
        return 0
    except Exception as exc:
        logger.error("Run failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
