# AGENTS.md

## Build/Test/Lint Commands

### Standard Commands (use in terminal/CI)
- **Setup venv**: `python -m venv venv && source venv/bin/activate` (Windows: `venv\Scripts\activate`)
- **Install dependencies**: `pip install -r requirements.txt`
- **Run tests**: `pytest tests/ -v`
- **Run single test**: `pytest tests/test_file.py::test_function -v`
- **Lint code**: `ruff check . && mypy --strict .`
- **Format code**: `ruff format .`

### Python Wrapper Scripts (for Amp on WSL or when bash unavailable)

Use these scripts as bash command replacements. All support `-h` for detailed help.

#### Master Script
- **`python dev.py test`** - Run all tests
- **`python dev.py test --logging`** - Run logging tests only
- **`python dev.py lint`** - Run linting (ruff + mypy)
- **`python dev.py format`** - Format code
- **`python dev.py validate`** - Full validation suite
- **`python dev.py list-tests`** - List all tests
- **`python dev.py check-syntax`** - Check Python syntax
- **`python dev.py help [command]`** - Get command help

#### Individual Scripts
- **`python test_runner.py`** - Flexible pytest runner
  - `python test_runner.py -v --cov` - Verbose with coverage
  - `python test_runner.py -k test_setup_logging` - Run specific test
  - `python test_runner.py src/factchecker/tests/test_logging_config.py -v`

- **`python run_logging_tests.py`** - Run logging configuration tests
  - `python run_logging_tests.py -v` - Verbose output
  - `python run_logging_tests.py --cov` - With coverage report
  - `python run_logging_tests.py -k request_id` - Filter by keyword

- **`python list_all_tests.py`** - Discover and list tests
  - `python list_all_tests.py --detailed` - Full test info
  - `python list_all_tests.py --filter logging` - Filter by pattern

- **`python check_syntax.py`** - Validate Python syntax
  - `python check_syntax.py --fix` - Show detailed errors
  - `python check_syntax.py src/` - Check specific directory

- **`python validate_tests.py`** - Comprehensive validation
  - `python validate_tests.py --quick` - Skip coverage
  - `python validate_tests.py --syntax` - Syntax check only

- **`python lint_check.py`** - Code quality checks
  - `python lint_check.py --ruff` - Ruff linting only
  - `python lint_check.py --mypy` - Type checking only
  - `python lint_check.py --fix` - Attempt to fix issues

- **`python format_code.py`** - Format code
  - `python format_code.py --check` - Check without modifying
  - `python format_code.py src/` - Format specific directory

## Architecture & Structure

**Tech Stack**: Python (FastAPI for REST API), SQLite (local DB), WhatsApp/Twilio integration

**Key Components**:
- **API Layer**: FastAPI endpoints (authentication, rate limiting, message routing)
- **Fact-Checking Engine**: NLP-based claim extraction (spaCy/NLTK), verification against local DB and external sources (BeautifulSoup, APIs)
- **Data Layer**: SQLite for cached user requests and fact-check results; external APIs (Snopes, FactCheck.org, Twitter)
- **Frontend**: WhatsApp bot integration
- **Deployment**: Docker containerization, AWS Lambda for serverless

## Code Style & Conventions

**Style Guide**: PEP 8, enforced by Ruff

**Formatting**: 
- Line length: 88 characters (Black standard)
- 4-space indentation
- Use `from __future__ import annotations` for forward references

**Type Hints**: Required; use strict mypy type checking

**Imports**: Group as (1) stdlib, (2) third-party, (3) local; alphabetically within groups

**Error Handling**: Use specific exception types, include context; prefer try-except for external API calls

**Naming**: 
- Functions/variables: `snake_case`
- Classes/exceptions: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

**Async**: Use `asyncio` for external API calls; async-first in FastAPI routes
