# Lab 3 — Maintainable Python Service
## Part E: Before and After Maintainability Worksheet

**Student**: Vo Nguyen Hoang Bach  
**Course**: CSC10014 · Practical Track 2026 · Week 3  
**Project**: Smart Virtual Assistant (`assistant_core`)

---

### 1. Comparison Table

| Metric / Question | Monolith (`assistant_monolith.py`) | Refactored (`assistant_core`) | Analysis & Impact |
| :--- | :--- | :--- | :--- |
| **Places to change the credit rate** | 1 constant in code (`RATE = 450000` in script) | 1 variable in `.env` (`CREDIT_RATE_VND=450000`) | Adheres to Twelve-Factor App (Factor III - Config). Changing tuition rates no longer requires code modification, testing re-runs, or code redeployment. |
| **Tests run offline and deterministically?** | **No** (Uses `random.random()` in `llm()`, causing 5% flakiness; simulated remote LLM call) | **Yes** (100% deterministic pure functions in `tools.py` and `StubLLMResponder` / `TemplateResponder` running offline) | Eliminates flaky test suites in CI/CD pipelines. Tests execute in < 0.05s with reproducible assertions without needing internet or paid API quotas. |
| **Missing `handbook.json`** | Prints warning and continues silently (`except:` in `load()`) | Raises `DataError` at startup (`DataError: handbook file not found`) | Fail-fast principle: Corrupted or missing critical knowledge sources abort startup immediately with informative exceptions rather than failing mysteriously at runtime during user requests. |
| **Secret printed or logged?** | **Yes** (`API_KEY` printed directly in debug log within `llm()`) | **No** (`llm_api_key` has `Field(repr=False)` in Pydantic Settings, excluded from JSON logs, `.env` gitignored) | Eliminates severe security vulnerabilities (CWE-532: Information Exposure Through Log Files). Prevents leaking keys to git or centralized logging systems. |
| **Module-level globals** | **9 globals** (3 mutable: `history`, `offices`, `handbook`; 6 constants) | **0 module globals** | Eliminates hidden coupling, state pollution across tests, and thread-safety bugs. State is encapsulated cleanly via classes and injected using Dependency Injection (DI). |
| **Bare `except:`** | **3 bare excepts** (in `load()`, `main()`) | **0 bare excepts** (caught specific exceptions or converted to domain exceptions) | Conforms to PEP 8 and Ruff rule `BLE001`. Prevents masking critical system events like `KeyboardInterrupt` (`Ctrl+C`), memory errors, or typos (`NameError`). |
| **Longest function (lines)** | **~65 lines** (`handle()` performs routing, parsing, calculation, search, LLM calls) | **~15 lines** (`AssistantService.handle()`) | Follows Single Responsibility Principle (SRP). Functions are short, highly focused, readable, and have low cyclomatic complexity. |
| **Swap the LLM without touching the service?** | **No** (Directly coupled to simulated `llm()` function inside monolith) | **Yes** (Decoupled behind the `Responder` Protocol adapter pattern) | In Week 4, production LLMs (e.g., OpenAI, Claude, Ollama) can be plugged in by creating a new `Responder` implementation without changing a single line of `AssistantService`. |

---

### 2. Check Yourself Reflection

#### Q1: What got more complex?
- **File Structure & Packaging**: The codebase evolved from a single 163-line standalone script (`assistant_monolith.py`) into a structured Python package (`assistant_core`) organized with `pyproject.toml`, `requirements.txt`, 10 distinct modules, typed test suites, and documentation.
- **Architectural Abstractions**:
  - **Pydantic Schemas (`models.py`, `config.py`)**: Data validation and type enforcement at application boundaries instead of loose strings and dicts.
  - **Protocol / Adapter Pattern (`responder.py`)**: Using Python's `typing.Protocol` for structural typing and runtime dependency inversion.
  - **Explicit Domain Exception Hierarchy (`errors.py`)**: Distinguishing configuration, data loading, user request, and provider errors.
  - **Separation of I/O Streams (`logging_setup.py`, `__main__.py`)**: Emitting machine-readable structured JSON telemetry to `stderr` while keeping clean human answers on `stdout`.

#### Q2: When is that trade-off worth it?
This trade-off is essential and well worth the initial overhead in the following scenarios:
1. **Team Collaboration**: Multiple engineers can independently develop, review, and maintain separate modules (e.g. Member 1 on `service.py`, Member 2 on `config.py`/logging, Member 3 on `knowledge.py`/`responder.py`, Member 4 on `tools.py`/tests) without git merge conflicts.
2. **Automated CI/CD & Test Automation**: With pure deterministic tools and injectable responder stubs, CI pipelines can run unit tests offline rapidly and reliably on every pull request.
3. **Evolutionary Architecture**: As the virtual assistant scales to include FastAPI HTTP endpoints (Lab 4) or web interfaces (Lab 7), the core business engine (`AssistantService.handle`) remains completely unchanged and reusable across all delivery channels.
4. **Production Readiness & Security**: Zero secrets leakage, clean error boundaries, and structured JSON logs are non-negotiable requirements for auditing, monitoring, and compliance in real-world systems.

---

### 3. Verification & Quality Gates Summary

- **Unit Tests**: All 26 tests pass in 0.03s (`pytest -q`).
- **Code Formatting & Linting**: Completely clean on `ruff check .`, `ruff format .`, and `ruff check --select BLE .` (0 errors, 0 warnings).
- **Interface Contract**: Tested fallback path with `StubLLMResponder(fail=True)` verifies `degraded=True` and citation propagation without unhandled exceptions.
