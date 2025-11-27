# AGENTS.md

## Build/Test/Lint Commands

- **Install dependencies**: `pip install -r requirements.txt`
- **Run tests**: `pytest tests/ -v`
- **Run single test**: `pytest tests/test_file.py::test_function -v`
- **Lint code**: `ruff check . && mypy --strict .`
- **Format code**: `ruff format .`

## Architecture & Structure

**Tech Stack**: Python (FastAPI for REST API), SQLite (local DB), WhatsApp/Twilio integration

**Key Components**:
- **API Layer**: FastAPI endpoints (authentication, rate limiting, message routing)
- **Fact-Checking Engine**: NLP-based claim extraction (spaCy/NLTK), verification against local DB and external sources (BeautifulSoup, APIs)
- **Data Layer**: SQLite for cached facts, user history; external APIs (Snopes, FactCheck.org, Twitter)
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
