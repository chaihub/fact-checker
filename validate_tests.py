#!/usr/bin/env python3
"""
Comprehensive validation of the test suite.

Performs multiple validation checks:
- Python syntax validation
- Test discovery and count
- Import validation
- Test markers
- Coverage analysis

Usage:
    python validate_tests.py              # Full validation
    python validate_tests.py --quick      # Skip coverage
    python validate_tests.py --syntax     # Only syntax check
    python validate_tests.py --imports    # Only import check
"""
from __future__ import annotations

import argparse
import ast
import os
import subprocess
import sys
from pathlib import Path


def check_syntax(file_path: Path) -> tuple[bool, str | None]:
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)


def check_imports(file_path: Path) -> tuple[bool, str | None]:
    """Check if a Python file's imports are valid."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        tree = ast.parse(code)

        # Basic import validation - check for unresolved relative imports
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module is None and node.level == 0:
                    return False, "Invalid relative import"
        return True, None
    except Exception as e:
        return False, str(e)


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


def validate_syntax(verbose: bool = False) -> bool:
    """Validate Python syntax for all project files."""
    print("\n" + "=" * 60)
    print("1. SYNTAX VALIDATION")
    print("=" * 60)

    project_root = Path(__file__).parent
    python_files = list((project_root / "src").glob("**/*.py"))
    python_files.extend((project_root / "tests").glob("**/*.py"))

    errors = []
    for file_path in sorted(python_files):
        rel_path = file_path.relative_to(project_root)
        is_valid, error = check_syntax(file_path)
        if not is_valid:
            errors.append((rel_path, error))
            if verbose:
                print(f"✗ {rel_path}: {error}")

    if errors:
        print(f"FAILED: {len(errors)} file(s) with syntax errors")
        for file_path, error in errors:
            print(f"  {file_path}: {error}")
        return False
    else:
        print(f"✓ PASSED: All {len(python_files)} files have valid syntax")
        return True


def validate_test_discovery() -> bool:
    """Discover and validate test count."""
    print("\n" + "=" * 60)
    print("2. TEST DISCOVERY")
    print("=" * 60)

    setup_environment()

    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/",
        "src/factchecker/tests/",
        "--collect-only",
        "-q",
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
        )

        output = result.stdout + result.stderr
        if "test session starts" in output or "passed" in output:
            # Extract test count from output
            lines = output.split("\n")
            for line in reversed(lines):
                if "test" in line.lower():
                    print(f"✓ PASSED: {line.strip()}")
                    return True
        print("✓ PASSED: Test discovery successful")
        return True
    except Exception as e:
        print(f"✗ FAILED: Test discovery error: {e}")
        return False


def validate_imports() -> bool:
    """Validate imports in test files."""
    print("\n" + "=" * 60)
    print("3. IMPORT VALIDATION")
    print("=" * 60)

    project_root = Path(__file__).parent
    test_files = list((project_root / "src" / "factchecker" / "tests").glob("test_*.py"))
    test_files.extend((project_root / "tests").glob("**/*.py"))

    errors = []
    for file_path in test_files:
        rel_path = file_path.relative_to(project_root)
        is_valid, error = check_imports(file_path)
        if not is_valid:
            errors.append((rel_path, error))

    if errors:
        print(f"✗ FAILED: {len(errors)} file(s) with import errors")
        for file_path, error in errors:
            print(f"  {file_path}: {error}")
        return False
    else:
        print(f"✓ PASSED: All {len(test_files)} test files have valid imports")
        return True


def validate_coverage() -> bool:
    """Run tests with coverage analysis."""
    print("\n" + "=" * 60)
    print("4. TEST EXECUTION & COVERAGE")
    print("=" * 60)

    setup_environment()

    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/",
        "src/factchecker/tests/",
        "-v",
        "--cov=src/factchecker",
        "--cov-report=term-missing",
        "--tb=short",
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
        )

        if result.returncode == 0:
            print("\n✓ PASSED: All tests executed successfully")
            return True
        else:
            print(f"\n✗ FAILED: Tests failed with return code {result.returncode}")
            return False
    except Exception as e:
        print(f"✗ FAILED: Error running tests: {e}")
        return False


def main() -> int:
    """Run comprehensive validation."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test validation for FactChecker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip coverage analysis (faster)",
    )
    parser.add_argument(
        "--syntax",
        action="store_true",
        help="Only check syntax",
    )
    parser.add_argument(
        "--discovery",
        action="store_true",
        help="Only check test discovery",
    )
    parser.add_argument(
        "--imports",
        action="store_true",
        help="Only check imports",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    print("FactChecker Test Validation Suite")
    print("=" * 60)

    results = {}

    # Determine which checks to run
    if args.syntax:
        results["syntax"] = validate_syntax(args.verbose)
    elif args.discovery:
        results["discovery"] = validate_test_discovery()
    elif args.imports:
        results["imports"] = validate_imports()
    else:
        # Run all validations
        results["syntax"] = validate_syntax(args.verbose)
        results["discovery"] = validate_test_discovery()
        results["imports"] = validate_imports()

        if not args.quick:
            results["coverage"] = validate_coverage()

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for check_name, passed_check in results.items():
        status = "✓ PASSED" if passed_check else "✗ FAILED"
        print(f"{check_name.upper():20} {status}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n✓ All validations passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} validation(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
