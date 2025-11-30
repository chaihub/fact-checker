#!/usr/bin/env python3
"""
Code quality checking with ruff and mypy.

Performs linting and type checking on the codebase.

Usage:
    python lint_check.py              # Run both ruff and mypy
    python lint_check.py --ruff       # Only ruff linting
    python lint_check.py --mypy       # Only mypy type checking
    python lint_check.py --fix        # Attempt to fix issues
    python lint_check.py --verbose    # Verbose output
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


def run_ruff(fix: bool = False, verbose: bool = False) -> int:
    """Run ruff linter."""
    print("\n" + "=" * 60)
    print("RUFF LINTING")
    print("=" * 60)

    cmd = ["python", "-m", "ruff", "check"]

    if fix:
        cmd.append("--fix")
        print("Mode: Fix issues")
    else:
        print("Mode: Check only (use --fix to attempt fixes)")

    cmd.extend(["src/", "tests/"])

    if verbose:
        cmd.append("-v")

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode
    except FileNotFoundError:
        print("Error: ruff not installed. Install with: pip install ruff")
        return 1
    except Exception as e:
        print(f"Error running ruff: {e}")
        return 1


def run_mypy(verbose: bool = False) -> int:
    """Run mypy type checker."""
    print("\n" + "=" * 60)
    print("MYPY TYPE CHECKING")
    print("=" * 60)

    setup_environment()

    cmd = ["python", "-m", "mypy", "--strict"]

    if verbose:
        cmd.append("-v")

    cmd.extend(["src/factchecker", "tests/"])

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode
    except FileNotFoundError:
        print("Error: mypy not installed. Install with: pip install mypy")
        return 1
    except Exception as e:
        print(f"Error running mypy: {e}")
        return 1


def main() -> int:
    """Run code quality checks."""
    parser = argparse.ArgumentParser(
        description="Code quality checking for FactChecker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--ruff",
        action="store_true",
        help="Run only ruff linting",
    )
    parser.add_argument(
        "--mypy",
        action="store_true",
        help="Run only mypy type checking",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix issues (ruff only)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    print("FactChecker Code Quality Checks")
    print("=" * 60)

    results = {}

    # Determine which checks to run
    if args.ruff:
        results["ruff"] = run_ruff(args.fix, args.verbose) == 0
    elif args.mypy:
        results["mypy"] = run_mypy(args.verbose) == 0
    else:
        # Run both
        results["ruff"] = run_ruff(args.fix, args.verbose) == 0
        results["mypy"] = run_mypy(args.verbose) == 0

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for check_name, passed_check in results.items():
        status = "✓ PASSED" if passed_check else "✗ FAILED"
        print(f"{check_name.upper():20} {status}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n✓ All checks passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} check(s) failed")
        if args.fix and "ruff" in results:
            print("Use --fix to attempt automatic fixes for ruff issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
