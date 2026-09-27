#!/usr/bin/env python3
"""Create or upgrade the local SQLite schema (idempotent)."""

from ott_brain.database import ensure_database


def main() -> None:
    path = ensure_database()
    print(f"Database ready at {path}")


if __name__ == "__main__":
    main()
