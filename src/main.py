import sys

from view_decisions_cli import main as view_decisions_main

"""
Sovereignty Control System
Initial entry point.

This file will evolve into the core orchestration layer.
"""


def main() -> None:
    # If a subcommand is provided, dispatch on it.
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "view-decisions":
            # Pass remaining arguments through to the view-decisions CLI
            # so flags like --limit still work.
            sys.argv = [sys.argv[0]] + sys.argv[2:]
            view_decisions_main()
            return

    # Default behavior (no or unknown command):
    print("== Sovereignty Control System CLI ==")
    print()
    print("Available commands:")
    print("  view-decisions   Show recent governance decisions from the audit log.")
    print()
    print("Usage:")
    print("  python src/main.py view-decisions [--limit N] [--audit-log PATH]")
    print()


if __name__ == "__main__":
    main()
