#!/usr/bin/env python3
"""
Focused test runner for logging configuration tests.

Runs the comprehensive logging_config test suite with useful options.

Usage:
    python run_logging_tests.py              # Run all logging tests
    python run_logging_tests.py -v           # Verbose output
    python run_logging_tests.py --cov        # With coverage
    python run_logging_tests.py -k request_id  # Run specific test by keyword
    python run_logging_tests.py --lf         # Run last failed
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
    """Run logging configuration tests."""
    parser = argparse.ArgumentParser(
        description="Run logging configuration tests for FactChecker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Quiet output",
    )
    parser.add_argument(
        "--cov",
        action="store_true",
        help="Generate coverage report",
    )
    parser.add_argument(
        "-k",
        "--keyword",
        help="Run tests matching keyword (e.g., test_setup_logging, request_id)",
    )
    parser.add_argument(
        "-x",
        "--exit-first",
        action="store_true",
        help="Exit on first failure",
    )
    parser.add_argument(
        "-s",
        "--show-output",
        action="store_true",
        help="Show captured output",
    )
    parser.add_argument(
        "--lf",
        action="store_true",
        help="Run last failed tests",
    )

    args = parser.parse_args()
    setup_environment()

    test_file = "src/factchecker/tests/test_logging_config.py"

    # Build command
    cmd = ["python", "-m", "pytest", test_file]

    if args.verbose:
        cmd.append("-v")
    elif args.quiet:
        cmd.append("-q")
    else:
        cmd.append("-v")  # Default to verbose for this focused runner

    if args.cov:
        cmd.extend(["--cov=src/factchecker", "--cov-report=term-missing"])

    if args.keyword:
        cmd.extend(["-k", args.keyword])

    if args.exit_first:
        cmd.append("-x")

    if args.show_output:
        cmd.append("-s")

    if args.lf:
        cmd.append("--lf")

    cmd.extend(["--tb=short", "--strict-markers"])

    print(f"Running logging configuration tests...")
    print(f"Command: {' '.join(cmd)}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'not set')}")
    print()

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        return 130
    except Exception as e:
        print(f"Error running tests: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
