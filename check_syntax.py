#!/usr/bin/env python3
"""
Check Python syntax for all project files.

Validates that all Python files have correct syntax without running them.

Usage:
    python check_syntax.py              # Check all Python files
    python check_syntax.py --fix        # Attempt to report detailed issues
    python check_syntax.py src/         # Check specific directory
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path


def check_syntax(file_path: Path) -> tuple[bool, str | None]:
    """
    Check if a Python file has valid syntax.

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"{e.filename}:{e.lineno}:{e.offset} - {e.msg}"
    except Exception as e:
        return False, f"{e.__class__.__name__}: {e}"


def main() -> int:
    """Check syntax for all Python files in the project."""
    parser = argparse.ArgumentParser(
        description="Check Python syntax for FactChecker project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "paths",
        nargs="*",
        default=["src/", "tests/"],
        help="Paths to check (default: src/ and tests/)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Show detailed error information",
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent
    python_files = []

    # Collect all Python files
    for path_str in args.paths:
        path = project_root / path_str
        if path.is_file() and path.suffix == ".py":
            python_files.append(path)
        elif path.is_dir():
            python_files.extend(path.glob("**/*.py"))

    if not python_files:
        print("No Python files found to check")
        return 1

    print(f"Checking syntax for {len(python_files)} Python files...\n")

    errors = []
    for file_path in sorted(python_files):
        rel_path = file_path.relative_to(project_root)
        is_valid, error = check_syntax(file_path)

        if is_valid:
            print(f"✓ {rel_path}")
        else:
            print(f"✗ {rel_path}")
            if args.fix:
                print(f"  Error: {error}")
            errors.append((rel_path, error))

    print()
    print("=" * 60)

    if errors:
        print(f"FAILED: {len(errors)} file(s) with syntax errors\n")
        if args.fix:
            print("Detailed errors:")
            for file_path, error in errors:
                print(f"  {file_path}")
                print(f"    {error}")
        return 1
    else:
        print(f"SUCCESS: All {len(python_files)} files have valid syntax")
        return 0


if __name__ == "__main__":
    sys.exit(main())
