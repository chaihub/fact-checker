# Python Wrapper Scripts - Complete Guide

## 🎯 What Are These Scripts?

Python wrapper scripts that replace bash commands for testing, linting, and validation in the FactChecker project. They work everywhere: locally, in CI/CD, and in Amp on WSL.

**Problem**: Amp in Windows WSL can't run bash (`spawn /bin/sh ENOENT` error)  
**Solution**: Pure Python scripts that do the same thing

## 🚀 Quick Start (30 seconds)

```bash
# Run tests
python test_runner.py -v --cov

# Check code quality
python lint_check.py

# Format code
python format_code.py

# Full validation
python validate_tests.py
```

That's it! No setup required. PYTHONPATH is set automatically.

## 📚 Documentation

Start with one of these based on your needs:

| Document | Purpose | Best For |
|----------|---------|----------|
| **QUICK_REFERENCE.md** | Command cheat sheet | Quick lookup of common commands |
| **PYTHON_WRAPPERS.md** | Complete user guide | Learning all features and options |
| **PYTHON_WRAPPERS_SUMMARY.md** | Implementation details | Understanding how it works |
| **PYTHON_WRAPPERS_IMPLEMENTATION_REPORT.md** | Technical report | Project overview and statistics |
| **This file** | Navigation guide | Finding what you need |

## 🎬 Common Tasks

### Run Logging Tests
```bash
python run_logging_tests.py -v
python run_logging_tests.py --cov
python run_logging_tests.py -k request_id
```

### Check Code Quality
```bash
python lint_check.py              # Ruff + Mypy
python lint_check.py --ruff       # Just ruff
python lint_check.py --mypy       # Just mypy
python lint_check.py --fix        # Fix issues
```

### Format Code
```bash
python format_code.py             # Format in-place
python format_code.py --check     # Check only
python format_code.py src/        # Specific directory
```

### Validate Everything
```bash
python validate_tests.py          # All checks
python validate_tests.py --quick  # Skip coverage
```

### Test Filtering
```bash
python test_runner.py -k test_setup_logging   # By name
python test_runner.py -m asyncio               # By marker
python test_runner.py --lf                     # Last failed
python test_runner.py -x                       # Exit on first failure
```

## 🛠️ Using the Master Script

Unified interface for everything:

```bash
python dev.py test              # Run tests
python dev.py test --logging    # Logging tests
python dev.py lint              # Lint code
python dev.py format            # Format code
python dev.py validate          # Validate
python dev.py list-tests        # List tests
python dev.py check-syntax      # Check syntax
python dev.py help              # Show help
python dev.py help test         # Help for command
```

## 📋 All Scripts

| Script | Purpose |
|--------|---------|
| `dev.py` | Master script - unified interface |
| `test_runner.py` | Run tests with filtering, coverage, etc. |
| `run_logging_tests.py` | Run logging configuration tests |
| `list_all_tests.py` | Discover and list all tests |
| `check_syntax.py` | Validate Python syntax |
| `validate_tests.py` | Comprehensive validation suite |
| `lint_check.py` | Ruff linting + Mypy type checking |
| `format_code.py` | Format code with ruff |

## 🔧 Script Details

### test_runner.py
**Flexible test runner with coverage and filtering**

```bash
python test_runner.py                    # Run all
python test_runner.py -v --cov          # Verbose with coverage
python test_runner.py -k test_name      # Filter by name
python test_runner.py -m asyncio        # Run by marker
python test_runner.py --lf              # Last failed
python test_runner.py -x                # Exit on first failure
python test_runner.py -s                # Don't capture output
```

**Common options**: `-v`, `--cov`, `-k`, `-m`, `-x`, `-s`, `--lf`, `--ff`

---

### run_logging_tests.py
**Focused runner for logging tests**

```bash
python run_logging_tests.py              # Run all logging tests
python run_logging_tests.py -v           # Verbose (default)
python run_logging_tests.py --cov        # With coverage
python run_logging_tests.py -k request_id  # Filter
```

---

### lint_check.py
**Code quality: ruff linting + mypy type checking**

```bash
python lint_check.py                # Both ruff and mypy
python lint_check.py --ruff         # Ruff only
python lint_check.py --mypy         # Mypy only
python lint_check.py --fix          # Fix ruff issues
python lint_check.py -v             # Verbose
```

---

### format_code.py
**Format code to project standards**

```bash
python format_code.py               # Format in-place
python format_code.py --check       # Check only
python format_code.py src/          # Specific directory
python format_code.py -v            # Verbose
```

---

### validate_tests.py
**Comprehensive 4-point validation**

Checks:
1. Python syntax for all files
2. Test discovery
3. Import validation
4. Test execution + coverage

```bash
python validate_tests.py            # All checks
python validate_tests.py --quick    # Skip coverage
python validate_tests.py --syntax   # Syntax only
python validate_tests.py -v         # Verbose
```

---

### check_syntax.py
**Quick syntax validation**

```bash
python check_syntax.py              # Check all
python check_syntax.py --fix        # Show detailed errors
python check_syntax.py src/         # Check directory
```

---

### list_all_tests.py
**Discover and list tests**

```bash
python list_all_tests.py                # List all
python list_all_tests.py --detailed     # Full info
python list_all_tests.py --filter logging  # Filter
```

---

## 🌳 Getting Help

Every script supports `-h`:

```bash
python dev.py help              # Master script help
python test_runner.py -h        # Test runner help
python lint_check.py -h         # Lint help
# ... and so on
```

## 📖 Documentation References

### For Quick Lookup
**→ QUICK_REFERENCE.md**
- One-line command descriptions
- Common workflows
- Cheat sheet style

### For Comprehensive Learning
**→ PYTHON_WRAPPERS.md**
- Complete usage guide
- All options documented
- Real-world examples
- Integration scenarios
- Troubleshooting section

### For Technical Details
**→ PYTHON_WRAPPERS_SUMMARY.md**
- Implementation overview
- What was built
- Why each script exists
- Next steps

### For Project Stats
**→ PYTHON_WRAPPERS_IMPLEMENTATION_REPORT.md**
- Detailed statistics
- Success criteria
- Verification results

## 🔄 Integration

### Local Development
```bash
# Activate venv (optional - scripts work without it)
source venv/bin/activate

# Run any script
python test_runner.py -v --cov
python lint_check.py
python format_code.py
```

### CI/CD Pipelines
```yaml
# GitHub Actions, GitLab CI, etc.
- run: python test_runner.py -v --cov
- run: python lint_check.py
- run: python format_code.py --check
```

### Amp on WSL
Since bash doesn't work in Amp on WSL, reference these scripts in documentation and use them outside Amp (terminal, CI/CD).

## ⚙️ How It Works

1. **Environment Setup**: Scripts automatically set `PYTHONPATH=/path/to/src`
2. **No Dependencies**: Only uses Python stdlib + installed packages
3. **Cross-Platform**: Works on Windows, Linux, macOS
4. **Error Handling**: Proper exit codes, clear error messages
5. **Help System**: Built-in `-h` on all scripts

## ✅ Features

- ✅ **No setup required** - Auto-configures environment
- ✅ **Works anywhere** - Local, CI/CD, Amp docs
- ✅ **Full coverage** - All testing/linting/formatting needs
- ✅ **Well documented** - Multiple guides with examples
- ✅ **Production quality** - Type hints, error handling, docstrings
- ✅ **User-friendly** - Consistent CLI, rich help system
- ✅ **Chainable** - Can combine multiple scripts

## 🎓 Learning Path

1. **First time**: Read QUICK_REFERENCE.md
2. **Common tasks**: Use the examples above
3. **Advanced usage**: Read PYTHON_WRAPPERS.md
4. **Understanding design**: Read PYTHON_WRAPPERS_SUMMARY.md
5. **Getting help**: Use `-h` flag or `python dev.py help [cmd]`

## 📊 Script Comparison

| Task | Bash | Python Script |
|------|------|---------------|
| Run tests | `pytest tests/ -v` | `python test_runner.py -v` |
| With coverage | `pytest --cov` | `python test_runner.py --cov` |
| Lint code | `ruff check . && mypy .` | `python lint_check.py` |
| Format code | `ruff format .` | `python format_code.py` |
| Full validation | Multiple commands | `python validate_tests.py` |

**Python scripts are simpler to use and work everywhere bash doesn't.**

## 🚦 Common Workflows

### Before Committing Code
```bash
python check_syntax.py && \
python lint_check.py && \
python format_code.py --check && \
python test_runner.py -v
```

### Quick Sanity Check
```bash
python validate_tests.py --quick
```

### Full CI/CD Pipeline
```bash
python test_runner.py -v --cov
python lint_check.py
python format_code.py --check
```

### Development Loop
```bash
# Make changes
code src/factchecker/example.py

# Test
python run_logging_tests.py -k test_

# Format
python format_code.py

# Check
python lint_check.py
```

## 📞 Getting Help

1. **Quick answer**: Run `python script.py -h`
2. **Common commands**: See QUICK_REFERENCE.md
3. **Detailed guide**: Read PYTHON_WRAPPERS.md
4. **Implementation details**: Check PYTHON_WRAPPERS_SUMMARY.md
5. **Master script**: Use `python dev.py help [cmd]`

## 🎯 Next Steps

1. **Try it**: `python test_runner.py -v`
2. **Explore**: `python dev.py help`
3. **Integrate**: Use in your workflow
4. **Share**: Let team know about alternatives to bash

## 📝 Files Created

```
dev.py                                    # Master script
test_runner.py                            # Test runner
run_logging_tests.py                      # Logging tests
list_all_tests.py                         # Test discovery
check_syntax.py                           # Syntax check
validate_tests.py                         # Full validation
lint_check.py                             # Linting
format_code.py                            # Formatting

PYTHON_WRAPPERS.md                        # Complete guide
PYTHON_WRAPPERS_SUMMARY.md                # Summary
PYTHON_WRAPPERS_IMPLEMENTATION_REPORT.md  # Technical report
QUICK_REFERENCE.md                        # Quick lookup
README_WRAPPERS.md                        # This file

AGENTS.md                                 # Updated with new section
```

---

**Status**: ✅ Complete and production-ready  
**Created**: November 30, 2025  
**Type**: Solution 3 - Python Wrapper Scripts  
**Purpose**: Bash-free alternative for Amp on Windows WSL
