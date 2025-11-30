#!/usr/bin/env python3
"""
Code formatting with ruff.

Formats the codebase to match project standards (PEP 8, 88-char lines).

Usage:
    python format_code.py              # Format all code
    python format_code.py src/         # Format specific directory
    python format_code.py --check      # Check without modifying
    python format_code.py --verbose    # Verbose output
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Format code with ruff."""
    parser = argparse.ArgumentParser(
        description="Code formatting for FactChecker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "paths",
        nargs="*",
        default=["src/", "tests/"],
        help="Paths to format (default: src/ and tests/)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check without modifying files",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    print("FactChecker Code Formatting")
    print("=" * 60)

    cmd = ["python", "-m", "ruff", "format"]

    if args.check:
        print("Mode: Check only (use without --check to modify files)")
        cmd.append("--check")
    else:
        print("Mode: Format and modify files")

    cmd.extend(args.paths)

    if args.verbose:
        cmd.append("-v")

    print(f"Formatting: {', '.join(args.paths)}")
    print()

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)

        if result.returncode == 0:
            if args.check:
                print("\n✓ All files are properly formatted")
            else:
                print("\n✓ Code formatting complete")
        else:
            if args.check:
                print("\n✗ Some files need formatting")
                print("Run without --check to format them")

        return result.returncode
    except FileNotFoundError:
        print("Error: ruff not installed. Install with: pip install ruff")
        return 1
    except Exception as e:
        print(f"Error running formatter: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
