# CARLA Foundations — LLM-Executable PRD

> Purpose: a **single Markdown spec** an LLM (e.g., GPT-Codex) can execute to **scaffold the repo** that Mubarak sets up so **Ebube can run Step 1 (Environment Bring-Up)** without blockers. Scope is foundations only (repo, tooling, docs, orchestration hooks, data contracts, CI), **no scenario logic**.

---

## 1) Project Name & Problem

**Project:** CARLA Environment Foundations for Step 1 Execution
**Problem it solves:** Provide a deterministic, one-command bring-up of CARLA with smoke and determinism checks, a minimal orchestration CLI, data/KPI schema contracts, and CI—so Ebube can immediately proceed with Step 1 scenario work.

---

## 2) Tech Stack, Dependencies, and APIs

**Languages/Frameworks**

* Python 3.10/3.11 (orchestration, validators, CLI)
* Flask (REST API wrapper to trigger runs, expose health/artefacts)
* React + Vite (minimal dashboard to view logs/summaries)
* PyTest + pydantic + jsonschema (tests & validation)
* GitHub Actions (CI)
* Makefile for DX
* Optional: Conda/mamba env; Docker (future)

**External Systems & APIs**

* **CARLA Simulator** (headless or GUI)
* **CARLA Python API** (`carla` module)
* Local filesystem for logs/artefacts (CSV/JSON/Parquet)
* (No cloud dependencies in Step 1)

**Python Dependencies (pin conservatively)**

* `carla` (version to match installed simulator)
* `pydantic>=2`
* `jsonschema`
* `numpy`, `pandas`, `pyarrow`
* `click` (CLI)
* `flask`
* `rich`, `typer` (optional DX)
* `pytest`, `pytest-cov`
* `mypy`, `ruff`, `black`, `isort`, `pre-commit`

**Node Dependencies**

* `react`, `react-dom`, `vite`
* `axios`
* `vitest`, `@testing-library/react`

---

## 3) Schemas (Contracts First)

> Contracts exist now; population of KPI values happens later with scenarios.

### 3.1 `meta.run.json` (JSON Schema)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "RunMeta",
  "type": "object",
  "required": ["scenario_id", "run_id", "seed", "carla_version", "map", "weather", "start_ts", "end_ts"],
  "properties": {
    "scenario_id": {"type": "string"},
    "run_id": {"type": "string"},
    "seed": {"type": "integer"},
    "carla_version": {"type": "string"},
    "map": {"type": "string"},
    "weather": {"type": "string"},
    "start_ts": {"type": "string", "format": "date-time"},
    "end_ts": {"type": "string", "format": "date-time"}
  }
}
```

### 3.2 `frames.parquet` (tabular schema; CSV allowed in smoke)

* Columns:
  `t` (float seconds), `ego_x`,`ego_y`,`ego_yaw` (floats), `vehicle_count` (int), `avg_speed` (float), `queue_len_est` (float), `light_states` (string JSON)

### 3.3 `kpi.json` (JSON Schema; placeholders allowed)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "KpiSummary",
  "type": "object",
  "properties": {
    "avg_travel_time": {"type": "number"},
    "throughput": {"type": "number"},
    "queue_length": {"type": "number"},
    "congestion_index": {"type": "number"}
  },
  "additionalProperties": true
}
```

---

## 4) In-Scope vs Out-of-Scope

**In Scope (foundations Mubarak provides)**

* Repo skeleton, Make targets, pre-commit hooks, CI
* Onboarding docs & troubleshooting
* Orchestration CLI (smoke/health/determinism only)
* Flask API to wrap orchestration for UI
* React dashboard to view run artefacts
* Determinism harness (fixed delta, seeds)
* Data & KPI schema contracts + validators
* Test stubs (pytest/Jest)

**Out of Scope (owned by Ebube / later steps)**

* Scenario authoring (routes, events, sensor graphs)
* KPI computations beyond placeholders
* Dataset generation runs and ML/RL training
* Any non-smoke CARLA logic

---

## 5) Requirements

### 5.1 Functional

* **F1 Bring-Up:** `make setup && make carla_up && make smoke` runs on a clean machine.
* **F2 Health:** `make health` prints server version, map, sync status.
* **F3 Determinism:** `make determinism_check` runs two seeded sessions and compares summary hashes (match expected).
* **F4 REST API:** `POST /api/run/smoke`, `GET /api/health`, `GET /api/runs/:id/summary`.
* **F5 UI:** Minimal React page shows last N runs and determinism result.
* **F6 Validation:** `pytest -k schema` validates example payloads against JSON Schemas.

### 5.2 Non-Functional

* **N1 Time-to-First-Bring-Up ≤ 30 min**
* **N2 Docs ≤ 2 pages for onboarding**
* **N3 CI green (lint/type/test)**
* **N4 Deterministic summaries on identical seeds**
* **N5 Portability: Linux primary; Windows notes included**

---

## 6) Architecture & Repo Layout (to generate)

```
carla-foundations/
  README.md
  Makefile
  pyproject.toml
  requirements.txt
  environment.yml
  .editorconfig
  .gitignore
  .pre-commit-config.yaml
  .github/workflows/ci.yml

  configs/
    app.yaml
    seeds.yaml
    schema_version.yaml

  schemas/
    run_meta.schema.json
    kpi.schema.json

  orchestration/
    __init__.py
    runner.py          # CLI (click/typer): smoke, health, determinism-check
    determinism.py
    logging_utils.py
    carla_client.py    # connection wrappers, sync mode setters

  data_pipeline/
    __init__.py
    writers.py         # CSV/Parquet writers
    validators.py      # pydantic/jsonschema validators

  api/                 # Flask REST
    __init__.py
    app.py             # endpoints: /api/health, /api/run/smoke, /api/runs/<id>/summary

  web/                 # React + Vite
    index.html
    src/
      main.jsx
      App.jsx
      api.js
      components/RunList.jsx
      components/RunDetail.jsx
    package.json
    vite.config.js

  scripts/
    carla_up.sh        # notes / wrapper to launch CARLA locally
    smoke_example.sh

  docs/
    GETTING_STARTED.md
    TROUBLESHOOTING.md
    CONTRIBUTING.md
    DETERMINISM.md

  tests/
    test_smoke.py
    test_determinism.py
    test_schema_validation.py
    api/
      test_api_smoke.py
  web/tests/
    App.test.jsx
```

---

## 7) CLI & REST Contracts

**CLI (click/typer)**

* `python -m orchestration.runner smoke --seed 42 --map Town03 --fps 20 --duration 5`
* `python -m orchestration.runner health`
* `python -m orchestration.runner determinism-check --seed 123 --map Town03 --fps 20 --ticks 50`

**Flask**

* `GET /api/health` → `{ carla_version, map, sync }`
* `POST /api/run/smoke` body `{ "seed": int, "map":"Town03","fps":20,"duration":5 }` → `{ "run_id": "uuid", "status":"started|ok|error" }`
* `GET /api/runs/:id/summary` → `{ "match": true, "meta": {...}, "kpi": {...} }` (for determinism, return both hash values)

---

## 8) Make Targets

```Makefile
setup:        ## install env, pre-commit, node deps
carla_up:     ## helper notes/wrapper to launch CARLA
smoke:        ## run smoke test via CLI
health:       ## print CARLA health
determinism_check: ## run twice and compare summaries
lint:         ## ruff + black --check + isort --check + mypy
test:         ## pytest -q
web:          ## cd web && npm run dev
build-web:    ## cd web && npm run build
```

---

## 9) CI (GitHub Actions)

* Triggers on PR + push:

  * Python: install, `ruff`, `black --check`, `isort --check`, `mypy`, `pytest`
  * Node: `npm ci`, `npm test` (vitest)
* Upload test artefacts: `artefacts/smoke/<run_id>/...`

---

## 10) Coding Standards (VERBATIM)

```
## Engineering Practices (VERBATIM)
## file_length_and_structure
Never allow a file to exceed 500 lines.
If a file approaches 400 lines, break it up immediately.
Treat 1000 lines as unacceptable, even temporarily.
Use folders and naming conventions to keep small files logically grouped.
### oop_first
Every functionality should be in a dedicated class, struct, or protocol, even if it's small.
Favor composition over inheritance, but always use object-oriented thinking.
Code must be built for reuse, not just to "make it work."
### single_responsibility_principle
Every file, class, and function should do one thing only.
If it has multiple responsibilities, split it immediately.
Each view, manager, or utility should be laser-focused on one concern.
### modular_design
Code should connect like Lego – interchangeable, testable, and isolated.
Ask: "Can I reuse this class in a different screen or project?" If not, refactor it.
Reduce tight coupling between components. Favor dependency injection or protocols.
### manager_and_coordinator_patterns
Use ViewModel, Manager, and Coordinator naming conventions for logic separation:
UI logic → ViewModel
Business logic → Manager
Navigation/state flow → Coordinator
Never mix views and business logic directly.
### function_and_class_size
Keep functions under 30-40 lines.
If a class is over 200 lines, assess splitting into smaller helper classes.
### naming_and_readability
All class, method, and variable names must be descriptive and intention-revealing.
Avoid vague names like data, info, helper, or temp.
### scalability_mindset
Always code as if someone else will scale this.
Include extension points (e.g., protocol conformance, dependency injection) from day one.
### avoid_god_classes
Never let one file or class hold everything (e.g., massive ViewController, ViewModel, or Service).
Split into UI, State, Handlers, Networking, etc.

## Output Requirements
- Generate multi-file scaffold implementing CLI, Flask API, and React UI.
- Include all necessary imports, requirements, and `README.md`.
- Flask and React must communicate solely through REST.
- Output code directly importable into VS Code.
- Include lightweight testing stubs for each layer (pytest / Jest).

## Prompting Style
- Use system + role + contextual prompting (per Prompt Engineering Whitepaper).
- Apply step-back reasoning for design ambiguity (e.g., HDBSCAN param choice).
- Maintain deterministic tone, temperature 0.2, for structured reproducibility.
- Output must follow clear modular hierarchy and include docstrings.
```

---

## 11) LLM Generation Tasks (do in order)

1. **Scaffold repo:** Create all files/dirs from **Section 6** with minimal, compilable contents.
2. **Python project config:**

   * `pyproject.toml` with `black`, `isort`, `ruff`, `mypy`, `pytest` settings.
   * `requirements.txt` with dependencies from **Section 2**.
3. **Pre-commit & CI:**

   * `.pre-commit-config.yaml` (black, isort, ruff, trailing-whitespace, end-of-file-fixer).
   * `.github/workflows/ci.yml` per **Section 9**.
4. **Orchestration code:**

   * `carla_client.py` (connect, enable sync, set fixed delta).
   * `runner.py` (commands: `smoke`, `health`, `determinism-check`).
   * `determinism.py` (write summaries, compare hashes).
   * `writers.py`, `validators.py` (implement schema writes & checks).
5. **Schemas & validators:**

   * Materialize JSON Schemas from **Section 3**; add `tests/test_schema_validation.py`.
6. **Flask API:**

   * `api/app.py` implementing endpoints from **Section 7**.
   * `tests/api/test_api_smoke.py`.
7. **React UI:**

   * Vite app; `RunList` & `RunDetail` call Flask REST; a simple table + detail view.
   * `web/tests/App.test.jsx`.
8. **Docs:**

   * `docs/GETTING_STARTED.md` (copy-paste commands), `TROUBLESHOOTING.md`, `DETERMINISM.md`, `CONTRIBUTING.md`.
9. **Makefile:**

   * Targets from **Section 8**; ensure `lint`, `test` aggregate Python & web tasks.
10. **Smoke artefacts:**

* Ensure `make smoke` produces `artefacts/<run_id>/meta.run.json`, `frames.csv`, `kpi.json`, `summary.hash`.

---

## 12) Assumptions & Risks

* **Assumptions:** CARLA installed externally; version documented; CPU-only path acceptable for smoke.
* **Risks:** Version drift (pin and verify), CUDA/driver issues (document tested combos), determinism variance (hash summaries, not raw frames).

---

## 13) Handover

Deliver a clean repo with CI green, working `make smoke`, determinism harness, REST API + UI stubs, and all docs. Scenario logic remains untouched for Ebube.

---

> **Instruction to LLM:** Generate the entire scaffold exactly as specified above. Use the **Coding Standards (Section 10)** across all files. Keep functions small, add docstrings, and ensure initial tests and linters pass.
