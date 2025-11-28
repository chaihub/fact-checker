# Phase 0.3 Analysis: CI/CD & Testing Infrastructure

**Analysis Date**: November 28, 2025  
**Status**: NOT IMPLEMENTED - Analysis Only  
**Scope**: Tasks 0.3.1, 0.3.2, 0.3.3

---

## Task 0.3.1: Create GitHub Actions Workflow for Tests

### Overview
Automated testing on every push and pull request to ensure code quality gates are met.

### What This Needs

#### Files to Create
1. `.github/workflows/tests.yml` (main test workflow)
2. `.github/workflows/lint.yml` (separate linting workflow - optional but recommended)
3. `.github/workflows/publish.yml` (optional - for releases)

#### Required Configuration
- **Trigger Events**:
  - `push` to main/develop branches
  - `pull_request` to main/develop branches
  - `schedule` (optional - nightly builds)

- **Job Matrix**:
  - Python versions: 3.10, 3.11, 3.12
  - OS: ubuntu-latest (minimum), macos-latest, windows-latest (optional)
  
- **Steps**:
  1. Checkout code
  2. Setup Python (using `actions/setup-python`)
  3. Cache pip dependencies (using `actions/cache`)
  4. Install dependencies (`pip install -r requirements-dev.txt`)
  5. Run linting:
     - `ruff check .`
     - `mypy --strict src/`
  6. Run tests:
     - `pytest src/factchecker tests/ -v --cov=src/factchecker --cov-report=xml`
  7. Upload coverage reports (if 0.3.2 completed)

#### Dependencies & Prerequisites
- ✅ All code must be committed to git repository
- ✅ Repository must be on GitHub
- ✅ `requirements.txt` and `requirements-dev.txt` finalized (DONE)
- ✅ `pytest.ini` configured (DONE)
- ✅ `pyproject.toml` configured (DONE)
- ⏳ Tests must actually run (Phase 1-7 work in progress)

#### Tools/Services Needed
- GitHub (free - included with repo)
- No external services required for basic workflow

#### Estimated Complexity
- **Effort**: 2-4 hours
- **Difficulty**: Medium
- **Dependencies**: Requires working tests

#### Key Considerations
- Test execution time: Should complete in < 5 minutes ideally
- Matrix builds can be expensive (runs tests on each Python version)
- Caching will significantly speed up dependency installation
- Workflow may fail until actual test implementations are complete
- Need to decide: fail workflow if coverage < 85% threshold?

---

## Task 0.3.2: Setup Code Coverage Reporting

### Overview
Track test coverage metrics and optionally enforce minimum coverage thresholds.

### What This Needs

#### Integration Options (Choose One or More)

**Option A: Codecov Integration** (Most Popular)
- Files needed: `.github/workflows/coverage.yml` or add to tests.yml
- Configuration:
  - Register project on codecov.io (free for public repos)
  - Install codecov action: `codecov/codecov-action@v3`
  - Generate XML coverage report from pytest: `--cov-report=xml`
  - Upload to codecov.io for badges and PR comments
  
**Option B: Coveralls Integration**
- Similar to Codecov but different service
- Files needed: `.github/workflows/coveralls.yml`
- Configuration:
  - Register on coveralls.io
  - Use `coveralls-ruby` action or `python-coveralls` tool
  
**Option C: Local HTML Reports Only**
- No external service, just generate reports locally
- Already configured in `pytest.ini` and `pyproject.toml`
- Use GitHub Pages to host reports (optional)

#### Required Configuration in Code
- ✅ `pytest.ini` has coverage config (DONE)
- ✅ `pyproject.toml` has coverage config (DONE)
- `coverage` package in requirements-dev.txt (DONE)

#### Files to Create/Modify
1. `.github/workflows/coverage.yml` (if separate from tests.yml)
2. `.codecov.yml` (optional - codecov configuration)
3. `README.md` badge section (to display coverage badge)
4. `.github/workflows/tests.yml` (add coverage upload step)

#### Dependencies & Prerequisites
- ✅ Tests must exist and be running
- ✅ Pytest coverage plugin installed (included in requirements-dev.txt)
- ⏳ GitHub Actions workflow must be set up (0.3.1)
- External service account (Codecov/Coveralls) if not going local-only

#### Tools/Services Needed
- pytest-cov plugin (✅ in requirements-dev.txt)
- Codecov account (free for public repos)
- OR Coveralls account (free for public repos)
- OR just local HTML reports (no external service)

#### Estimated Complexity
- **Effort**: 1-3 hours
- **Difficulty**: Easy to Medium
- **Dependencies**: Requires working tests and 0.3.1 completion

#### Key Considerations
- Which service? Codecov is most popular, best integration
- Should enforce minimum coverage (85%) on PRs?
- Coverage reports need to be generated as XML from pytest
- Branch coverage vs line coverage - which to track?
- Coverage badges on README for visibility
- Historical tracking of coverage over time

---

## Task 0.3.3: Setup Pre-commit Hooks for Linting

### Overview
Run linting/formatting checks before each commit, preventing bad code from entering repository.

### What This Needs

#### Files to Create
1. `.pre-commit-config.yaml` (main configuration file)

#### Required Configuration
- **Hook Definitions**:
  - ruff check (linting)
  - ruff format (code formatting)
  - mypy (type checking)
  - black (code formatting - optional, conflicts with ruff)
  - trailing-whitespace
  - end-of-file-fixer
  - check-yaml
  - check-json
  - check-toml

- **Repository Configuration**:
  - Language: python
  - Additional dependencies: mypy, types-*
  - Exclude patterns (tests, venv, etc.)
  - Entry points for each tool

#### Installation/Setup Instructions
Users will need to:
1. Install pre-commit framework: `pip install pre-commit`
2. Install hooks: `pre-commit install`
3. First run may take time to install all hooks
4. Optional: `pre-commit run --all-files` to check existing code

#### Dependencies & Prerequisites
- ✅ ruff installed (in requirements-dev.txt)
- ✅ mypy installed (in requirements-dev.txt)
- ⏳ pre-commit framework (NOT in requirements-dev.txt - would need to add)
- Users must run `pre-commit install` after cloning

#### Tools/Services Needed
- pre-commit framework (pip installable)
- ruff (✅ already included)
- mypy (✅ already included)
- Additional type stubs if needed

#### Estimated Complexity
- **Effort**: 1-2 hours
- **Difficulty**: Easy
- **Dependencies**: None really, independent of tests

#### Key Considerations
- Will slow down `git commit` on first run
- Can be bypassed with `git commit --no-verify` (discouraged)
- Should be optional for CI (use workflow instead)
- Consideration: fail on warnings or only errors?
- Type checking can be slow - might want to exclude or run separately
- Update documentation/contribution guide to mention hooks
- Consider skip patterns for large refactors

---

## Task Dependency Analysis

```
0.3.1 (GitHub Actions)
  ├─ depends on: Git repo, tests exist
  ├─ enables: 0.3.2 (upload coverage)
  └─ enables: 0.3.3 (can run in CI instead of locally)

0.3.2 (Coverage Reporting)
  ├─ depends on: 0.3.1 (optional, can be local-only)
  ├─ depends on: Tests exist
  └─ independent of: 0.3.3

0.3.3 (Pre-commit Hooks)
  ├─ depends on: Nothing really
  ├─ independent of: 0.3.1 and 0.3.2
  └─ optional: Some teams require, some don't
```

**Recommended Order**:
1. **0.3.3** first (simplest, no dependencies, helps local dev)
2. **0.3.1** second (needed for CI automation)
3. **0.3.2** last (builds on 0.3.1, optional)

---

## Required Changes to Existing Files

### requirements-dev.txt
**Needs Addition**:
```
pre-commit>=3.5.0
```

### README.md (if exists, else create)
**Needs Addition**:
```markdown
## Development Setup

### Pre-commit Hooks
Install pre-commit hooks to automatically lint before commit:
```bash
pip install pre-commit
pre-commit install
```
```

### Contributing Guide
**May Need Creation**:
- Document commit hook setup
- Document workflow (fork → branch → PR)
- Coverage expectations

---

## File Inventory for Phase 0.3

| File | Purpose | Effort | Status |
|------|---------|--------|--------|
| `.github/workflows/tests.yml` | Test automation | 2-4h | TODO |
| `.github/workflows/lint.yml` | Separate lint job | 1-2h | Optional |
| `.codecov.yml` | Codecov config | 1h | Optional |
| `.pre-commit-config.yaml` | Pre-commit hooks | 1-2h | TODO |
| `CONTRIBUTING.md` | Dev guide | 1-2h | Optional |
| `requirements-dev.txt` | Add pre-commit | <15min | TODO |

---

## Blockers & Constraints

### Current Blockers
1. **Tests don't exist yet** - Phase 0.3 can define workflows, but they won't run successfully until Phase 1-7 complete
2. **No external service accounts** - Need to create Codecov/Coveralls accounts (or decide to skip)
3. **Private vs Public repo** - Affects which services are free

### Technical Constraints
- GitHub Actions: Free for public repos, limited for private (2000 min/month)
- Codecov: Free for public repos, paid for private
- Test execution time: Must keep under reasonable limits
- Python versions: Currently targeting 3.10+

### Timing Constraints
- These tasks are low priority (Phase 0.3)
- Better to implement after core functionality is working
- Can be skipped for MVP if needed

---

## Effort Summary

| Task | Effort | Difficulty | Blockers | Priority |
|------|--------|------------|----------|----------|
| 0.3.1 | 2-4h | Medium | Tests needed | MEDIUM |
| 0.3.2 | 1-3h | Easy | Tests needed, Codecov acct | MEDIUM |
| 0.3.3 | 1-2h | Easy | None | LOW-MEDIUM |
| **Total** | **5-9h** | **Easy-Medium** | **Tests** | **MEDIUM** |

---

## Recommendations

### For MVP (Minimum Viable Product)
✅ **Do implement 0.3.3** (pre-commit hooks) - helps local development immediately  
⏳ **Skip 0.3.1 and 0.3.2** initially - can add after core functionality works

### For Production Ready
✅ **Implement all three** in order: 0.3.3 → 0.3.1 → 0.3.2

### If Resource Constrained
**Priority Order**: 0.3.3 → 0.3.1 → 0.3.2  
**Time Budget**: 5-9 hours total

### Best Practices to Follow
- Start with 0.3.3 (no dependencies, helps dev flow)
- Keep GitHub Actions lean and fast
- Use caching aggressively
- Codecov over Coveralls (more popular, better integrations)
- Make coverage threshold enforceable on PRs
- Document pre-commit setup in README

---

## Next Steps (When Ready to Implement)

1. **Before implementing 0.3.1**:
   - Verify GitHub repo is accessible
   - Test that `pytest` runs locally successfully
   - Ensure all dependencies resolve correctly

2. **Before implementing 0.3.2**:
   - Create Codecov account (or choose alternative)
   - Get repository token if needed
   - Decide on coverage threshold enforcement

3. **Before implementing 0.3.3**:
   - Add `pre-commit` to requirements-dev.txt
   - Verify ruff and mypy are compatible
   - Test locally before committing `.pre-commit-config.yaml`

---

**Status**: Analysis Complete - Ready for Implementation When Needed
