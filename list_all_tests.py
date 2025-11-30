#!/usr/bin/env python3
"""
List all available tests in the project.

Useful for discovering what tests exist and their structure.

Usage:
    python list_all_tests.py              # List all tests
    python list_all_tests.py --detailed   # Show test details
    python list_all_tests.py --filter logging  # Filter by pattern
    python list_all_tests.py --count      # Just count tests
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def setup_environment() -> None:
    """Set up PYTHONPATH for the project."""
    project_root = Path(__file__).parent
    src_path = project_root / "src"

    if src_path.exists():
        pythonpath = str(src_path)
        if "PYTHONPATH" in os.environ:
            os.environ["PYTHONPATH"] = f"{pythonpath}:{os.environ['PYTHONPATH']}"
        else:
            os.environ["PYTHONPATH"] = pythonpath


def main() -> int:
    """List all tests in the project."""
    parser = argparse.ArgumentParser(
        description="List all tests in FactChecker project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed information for each test",
    )
    parser.add_argument(
        "--filter",
        help="Filter tests by pattern (e.g., 'logging', 'pipeline')",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        help="Show only test count",
    )
    parser.add_argument(
        "--markers",
        action="store_true",
        help="Show tests grouped by markers",
    )

    args = parser.parse_args()
    setup_environment()

    # Build command to collect tests
    cmd = ["python", "-m", "pytest", "--collect-only", "-q"]

    if args.detailed:
        cmd.remove("-q")
        cmd.append("-v")

    if args.filter:
        cmd.extend(["-k", args.filter])

    if args.count:
        cmd.append("--collect-only")

    # Add test paths
    cmd.extend(["tests/", "src/factchecker/tests/"])

    print(f"Collecting tests...")
    if args.filter:
        print(f"Filter: {args.filter}")
    print()

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)

        if args.count or args.filter:
            print("\n" + "=" * 60)
            if args.filter:
                print(f"Filtered tests listed above")
            else:
                print("Run with --detailed for full test information")

        return result.returncode
    except KeyboardInterrupt:
        print("\nCollection interrupted by user")
        return 130
    except Exception as e:
        print(f"Error collecting tests: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
