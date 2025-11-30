#!/usr/bin/env python3
"""
Master development script for FactChecker.

Unified interface for all common development tasks.

Usage:
    python dev.py test                         # Run all tests
    python dev.py test --logging               # Run logging tests only
    python dev.py lint                         # Run linting checks
    python dev.py format                       # Format code
    python dev.py validate                     # Full validation
    python dev.py list-tests                   # List all tests
    python dev.py check-syntax                 # Check syntax only
    
    python dev.py help [command]               # Get help for command

Examples:
    python dev.py test -v --cov               # Verbose tests with coverage
    python dev.py test -k test_setup_logging  # Run specific test
    python dev.py lint --ruff                 # Ruff only
    python dev.py format --check              # Check formatting
    python dev.py validate --quick            # Skip coverage
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import NoReturn


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


def run_script(script_name: str, args: list[str]) -> int:
    """Run a wrapper script with arguments."""
    setup_environment()
    script_path = Path(__file__).parent / f"{script_name}.py"

    if not script_path.exists():
        print(f"Error: Script {script_name}.py not found", file=sys.stderr)
        return 1

    cmd = ["python", str(script_path)] + args

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        return 130
    except Exception as e:
        print(f"Error running command: {e}", file=sys.stderr)
        return 1


def print_help() -> NoReturn:
    """Print help message and exit."""
    print(__doc__)
    sys.exit(0)


def print_command_help(command: str) -> NoReturn:
    """Print help for a specific command."""
    helps = {
        "test": "Run pytest tests\n  python test_runner.py -h",
        "test-logging": "Run logging configuration tests\n  python run_logging_tests.py -h",
        "lint": "Run ruff and mypy checks\n  python lint_check.py -h",
        "format": "Format code with ruff\n  python format_code.py -h",
        "validate": "Comprehensive validation\n  python validate_tests.py -h",
        "list-tests": "List all available tests\n  python list_all_tests.py -h",
        "check-syntax": "Check Python syntax\n  python check_syntax.py -h",
    }

    if command in helps:
        print(f"Help for: {command}\n")
        print(helps[command])
    else:
        print(f"Unknown command: {command}")
        print(f"\nAvailable commands: {', '.join(helps.keys())}")

    sys.exit(0)


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print_help()

    command = sys.argv[1]
    args = sys.argv[2:]

    # Map commands to scripts
    command_map = {
        "test": "test_runner",
        "test-logging": "run_logging_tests",
        "lint": "lint_check",
        "format": "format_code",
        "validate": "validate_tests",
        "list-tests": "list_all_tests",
        "check-syntax": "check_syntax",
    }

    if command == "help":
        if args:
            print_command_help(args[0])
        else:
            print_help()

    if command in command_map:
        return run_script(command_map[command], args)

    # Check for common typos
    if command in ["--help", "-h", "h"]:
        print_help()

    print(f"Unknown command: {command}")
    print(f"Use 'python dev.py help' for available commands")
    return 1


if __name__ == "__main__":
    sys.exit(main())
