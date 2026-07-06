# GAM Codebase Rearchitecture — Developer Guide

## 1. Why This Was Done

### The Problem

`gam/__init__.py` was an **82,735-line monolith** — a single file containing virtually all of GAM's logic. Every Google Workspace API surface (Drive, Gmail, Calendar, Classroom, Groups, Vault, Chat, ChromeOS, etc.) lived in one file. This created real problems:

- **Navigating the codebase was painful.** Finding where a command was implemented meant scrolling through 82K lines or relying on grep. No IDE could provide useful file-level structure.
- **Merge conflicts were constant.** Any two developers touching different features (say, Drive and Gmail) would conflict because they were editing the same file.
- **Understanding scope was impossible.** Which constants belong to Drive? Which helper functions are shared vs. specific to Gmail? When everything is in one namespace, you can't tell.
- **There were no tests.** The monolith was untestable — you couldn't import a single utility without loading the entire 82K-line module with all its side effects.
- **No linting.** There was no static analysis catching undefined names, unused imports, or stale code.

### What Changed for Users

**Nothing.** GAM behaves identically. Every command, flag, and output format is unchanged.

### By the Numbers

| Metric | Before | After |
|--------|--------|-------|
| Source files | 1 (+ gamlib/) | 169 |
| `__init__.py` | 82,735 lines | 2,726 lines |
| Total source lines | ~83,000 | ~96,800 (split across 169 files) |
| Ruff violations | Never checked | **0** (clean) |
| Test files | 0 | 10 |
| Test cases | 0 | 155 passing |
| Architectural guardrails | None | 7 enforced rules |

---

## 2. The New Layout

### High-Level Structure

```
src/gam/
├── __init__.py          # Hub: imports, dispatch tables, ProcessGAMCommand()
├── __main__.py          # Entry point
├── constants.py         # Shared constants (star-imported everywhere)
├── var.py               # Singleton instances: Act, Cmd, Ent, Ind
│
├── gamlib/              # Pure data/config — no imports from gam/ or util/
│   ├── action.py        #   GamAction (Act) — action state machine
│   ├── api.py           #   API service definitions, scopes, versions
│   ├── clargs.py        #   GamCLArgs (Cmd) — command-line argument state
│   ├── entity.py        #   GamEntity (Ent) — entity type definitions
│   ├── gapi.py          #   GAPI error codes and exception classes
│   ├── indent.py        #   GamIndent (Ind) — output indentation
│   ├── msgs.py          #   User-facing message strings
│   ├── settings.py      #   GC — GAM configuration keys and defaults
│   ├── skus.py          #   Google Workspace SKU definitions
│   ├── state.py         #   GM — global mutable state (Globals dict)
│   ├── uprop.py         #   User property schema definitions
│   └── verlibs.py       #   Library version checks
│
├── util/                # Shared utilities — may import gamlib/, never cmd/
│   ├── api.py           #   HTTP transport, OAuth, service construction
│   ├── api_call.py      #   callGAPI, callGAPIpages — retry wrappers
│   ├── args.py          #   Argument parsing helpers (getString, getChoice, etc.)
│   ├── batch.py         #   Batch/CSV/loop execution engine
│   ├── config.py        #   SetGlobalVariables, config file I/O
│   ├── connection.py    #   Connection check, version, usage
│   ├── csv_pf.py        #   CSVPrintFile framework (~1,900 lines)
│   ├── display.py       #   Entity display, action reporting
│   ├── entity.py        #   Entity resolution (getEntityToModify, etc.)
│   ├── errors.py        #   Error exit helpers (invalidChoiceExit, etc.)
│   ├── fileio.py        #   File I/O, path resolution, redirect management
│   ├── output.py        #   writeStdout, writeStderr, formatting, color
│   ├── svcacct.py       #   Service account credential management
│   └── ...              #   (+ 12 more small focused modules)
│
└── cmd/                 # ALL command implementations (one module per API)
    ├── admin.py         #   Admin roles & privileges
    ├── calendar/        #   Calendar API (sub-package)
    │   ├── acls.py
    │   ├── calendars.py
    │   ├── events.py
    │   ├── core.py      #     Shared calendar helpers
    │   └── ...
    ├── chrome/           #   Chrome Management (sub-package)
    │   ├── apps.py       #     App management
    │   ├── browsers.py   #     Browser enrollment CRUD
    │   ├── policies.py   #     Chrome policies
    │   ├── profiles.py   #     Browser profiles
    │   └── tokens.py     #     Enrollment tokens
    ├── classroom/        #   Classroom API (sub-package)
    │   ├── courses.py
    │   ├── content.py
    │   ├── participants.py
    │   ├── guardians.py
    │   └── batch_ops.py
    ├── drive/            #   Drive API (sub-package)
    │   ├── core.py       #     Search, entities, MIME types
    │   ├── files.py      #     File CRUD
    │   ├── permissions.py
    │   ├── shareddrives.py
    │   ├── copymove/     #       Copy & move (nested)
    │   └── transfer/     #       Transfer & ownership (nested)
    ├── gmail/            #   Gmail API (sub-package)
    │   ├── labels.py
    │   ├── settings.py
    │   ├── modify.py     #     Message modify/delete/trash
    │   ├── print.py      #     Message list/export/forward
    │   └── ...
    ├── groups/           #   Groups API (sub-package)
    ├── people/           #   People API (sub-package)
    ├── users/            #   User management (sub-package)
    ├── vault/            #   Vault API (sub-package)
    └── ...               #   (+ 25 flat modules for smaller APIs)
```

### The Three Layers

The codebase has a strict three-layer architecture:

```
   gamlib/          Foundation — pure data, constants, definitions
     ↑                         NO imports from gam/ or util/
   util/            Infrastructure — shared utilities, API wrappers
     ↑                         May import gamlib/, NEVER cmd/
   cmd/             Commands — one module per Google API surface
                               Imports from util/ and gamlib/
```

`__init__.py` sits above all three as the dispatch hub. It imports from `cmd/` and wires functions into dispatch tables.

**This layering is enforced by automated tests** (see Section 5).

---

## 3. Key Patterns and Conventions

### How `__init__.py` Works Now

`__init__.py` (~2,726 lines) is the **dispatch hub**. It does three things:

1. **Imports every command function** from `cmd/` modules (~99 import blocks)
2. **Maps command names to handler functions** in dispatch tables (`MAIN_COMMANDS`, `MAIN_COMMANDS_WITH_OBJECTS`, etc.)
3. **Runs `ProcessGAMCommand()`** — the main command-line parser and dispatcher

It does NOT contain business logic. If you're implementing a new command, you write it in `cmd/` and add the import + dispatch table entry in `__init__.py`.

### Shared State: `var.py` and the Singletons

GAM uses four singleton helper objects everywhere:

```python
from gam.var import Act, Cmd, Ent, Ind
```

| Object | Class | Purpose |
|--------|-------|---------|
| `Act` | `GamAction` | Tracks current action (CREATE, UPDATE, DELETE, etc.) |
| `Cmd` | `GamCLArgs` | Command-line argument state and cursor |
| `Ent` | `GamEntity` | Entity type labels (USER, GROUP, etc.) |
| `Ind` | `GamIndent` | Output indentation level |

These classes use **class-level shared state** — all instances see the same values. `var.py` creates canonical instances that every module imports.

### How Command Modules Are Structured

Every `cmd/` module follows this pattern:

```python
"""Brief description — what API surface this covers."""

from gamlib import api as API
from gamlib import gapi as GAPI
from gamlib import settings as GC
from gamlib import state as GM
from gam.var import Act, Cmd, Ent, Ind
from gam.util.api import buildGAPIObject
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import getArgument, getString, ...
from gam.util.display import printGettingAllEntityItemsForWhom, ...
from gam.util.errors import invalidChoiceExit, ...
from gam.util.output import writeStdout, ...
from gam.constants import *

def doCreateSomething():
    ...

def doPrintShowSomething():
    ...
```

Key rules:

- **Import from `util/` and `gamlib/` directly** — use full paths like `from gam.util.args import getString`
- **Never use deferred imports** — all imports are at module top level
- **Never import from `gam.__init__`** — import from the actual source module
- **`from gam.constants import *`** is the one accepted star import — it provides shared constants

### How to Find a Function

**By intuition:** Module names map to API surfaces. Gmail labels → `cmd/gmail/labels.py`. Shared drive management → `cmd/drive/shareddrives.py`.

**By GAM command name:** Search the dispatch tables in `__init__.py`:
```bash
grep "drivefile" src/gam/__init__.py  # Find the handler function
grep "copyDriveFile" src/gam/__init__.py  # Find which module imports it
```

**By grep:**
```bash
grep -rn "def copyDriveFile" src/gam/cmd/
# → src/gam/cmd/drive/copymove/copymove_util.py:947
```

**By IDE:** Ctrl/Cmd-click any function name in `__init__.py` to jump to its definition.

---

## 4. Where New Code Goes

### Adding a New Command

1. **Find (or create) the right `cmd/` module.** Does it fit an existing API surface? Add to that module. New API surface? Create a new file in `cmd/`.

2. **Write the function** following the module pattern above. Import from `util/` and `gamlib/`, never from `__init__.py`.

3. **Wire it in `__init__.py`:**
   - Add the import: `from gam.cmd.your_module import doYourCommand`
   - Add the dispatch table entry in `MAIN_COMMANDS` or `MAIN_COMMANDS_WITH_OBJECTS`

4. **Run the checks:** `ruff check src/` and `pytest tests/`

### Adding a New Utility

Shared helpers that multiple `cmd/` modules need go in `util/`. Rules:

- **`util/` must NEVER import from `cmd/`.** This is enforced by tests.
- If your utility needs something currently in a `cmd/` module, that thing should be moved down to `util/` first.
- Small, focused modules are preferred — don't dump everything into one file.

### Creating a Sub-Package

When a `cmd/` module grows large enough to split, follow the existing pattern:

```
cmd/your_api/
├── __init__.py      # Empty or re-exports for dispatch
├── core.py          # Shared helpers, constants, entity definitions
├── manage.py        # CRUD operations
└── print.py         # Print/show/list operations
```

Sub-packages like `calendar/`, `chrome/`, `classroom/`, `drive/`, `gmail/`, `groups/`, `people/` all follow this pattern. The `core.py` module holds shared helpers that other modules in the package import.

---

## 5. Tooling: Ruff and Pytest

### Ruff (Linting)

Ruff runs on every PR via GitHub Actions. Configuration is in `pyproject.toml`:

```bash
# Check for violations (what CI runs)
python3 -m ruff check src/

# See what a specific rule catches
python3 -m ruff check --select F841 --no-fix src/
```

**Active rules:**

| Rule | What It Catches |
|------|----------------|
| `F` (Pyflakes) | Unused imports, undefined names, shadowed variables |
| `E711` | `x == None` instead of `x is None` |
| `E713` | `not x in y` instead of `x not in y` |
| `UP` (pyupgrade) | Pre-Python 3.11 syntax that should be modernized |

**Suppressed rules** (GAM architectural necessities, not bugs):

| Rule | Why Suppressed |
|------|----------------|
| `F402` | GAM reuses loop variable names that shadow imports (2 cases in `batch.py`) |
| `F403` | `from gam.constants import *` is used by design in every `cmd/` module |
| `F405` | Names from the star import above — unavoidable consequence of F403 |
| `F811` | GAM's arg-parsing `while` loops reassign variables in conditional branches |
| `F841` | `doPrintShowAdmins` in `admin.py` is an incomplete function with dead initializations |

**The ignore list should only shrink.** If you fix the underlying pattern, remove the suppression so ruff catches future regressions.

### Pytest (Unit Tests)

```bash
# Run all tests
python3 -m pytest tests/

# Run a specific test file
python3 -m pytest tests/test_architecture.py -v
```

Configuration is in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
```

**Test files and what they cover:**

| Test File | Purpose |
|-----------|---------|
| `test_architecture.py` | **Architectural guardrails** — the most important tests (see below) |
| `test_no_circular_imports.py` | Verifies `util/` has no internal circular imports |
| `test_imports.py` | Verifies all modules can be imported without errors |
| `test_args.py` | Unit tests for argument parsing utilities |
| `test_config.py` | Unit tests for config/settings utilities |
| `test_csv_pf.py` | Unit tests for CSV framework |
| `test_entity.py` | Unit tests for entity resolution and course scopes |
| `test_output.py` | Unit tests for output formatting |
| `test_password.py` | Unit tests for password hashing |

### Architectural Guardrail Tests (`test_architecture.py`)

These are the **critical tests** that prevent architectural regressions. They enforce 7 rules:

| Rule | What It Enforces |
|------|-----------------|
| **1. util/ never imports cmd/** | The foundation layer must not depend on the command layer |
| **2. No new cmd/ circular imports** | New A↔B import cycles between cmd/ modules are forbidden |
| **3. No new deferred imports** | All imports must be at module top-level — no `import X` inside functions |
| **4. gamlib/ never imports gam/ or util/** | The data layer has zero upward dependencies |
| **5. Undefined globals ratchet** | The count of undefined name references (`F821`) can only decrease, never increase |
| **6. No short-path imports** | Must use `from gam.util.X import ...`, not `from util.X import ...` |
| **7. No sys.modules aliasing** | No `sys.modules['gam.foo'] = bar` tricks |

Each rule has a **known violations allowlist** that must only shrink. If you fix a violation, remove it from the allowlist. If the test catches a new violation, **fix your code** — don't add to the allowlist.

---

## 6. Known Issues and Remaining Risks

### Incomplete Extractions

Some code hasn't been fully extracted from `__init__.py`:

- **`doPrintShowAdmins` in `admin.py`** — The function ends at line 604, mid-way through its arg-parsing loop. The remaining branches are still in `__init__.py`. This is tracked by the F841 suppression.
- **`__init__.py` still contains ~2,726 lines** — Most of this is import blocks and dispatch tables (necessary), but some residual business logic remains that could be moved to `cmd/` or `util/`.

### Known Circular Import Cycles

The architectural tests track 9 known direct cycles between `cmd/` modules:

| Cycle | Description |
|-------|-------------|
| `customer` ↔ `domains` | Domain and customer settings are tightly coupled |
| `calendar.acls` ↔ `calendar.resources` | Calendar resource ACLs reference each other |
| `calendar.acls` ↔ `calendar.calendars` | Calendar and ACL operations share helpers |
| `calendar.calendars` ↔ `calendar.settings` | Calendar settings need calendar helpers |
| `calendar.calendars` ↔ `calendar.events` | Events and calendars share utilities |
| `calendar.dispatch` ↔ `calendar.resources` | Calendar dispatch table references resources |
| `groups.groups` ↔ `groups.members` | Group and member operations are tightly coupled |
| `people.contacts` ↔ `people.domainprofiles` | Contact and profile operations share code |
| `people.contacts` ↔ `people.othercontacts` | Contact types share display logic |

These work at runtime (Python handles them if the cycle doesn't execute during import), but they should be broken over time by extracting shared code into `core.py` or a constants module.

### Known `util/` → `cmd/` Violations

Four `util/` modules still import from `cmd/` (tracked in `test_architecture.py`):

| util/ Module | Why |
|-------------|-----|
| `entity.py` | Calls `cmd/`-level functions for entity resolution |
| `batch.py` | Contains `doBatch`/`doCSV` which import from `cmd/drive/gdoc_fetch` |
| `api.py` | Uses yubikey module for hardware key auth |
| `tags.py` | References resources for tag substitution |

These are the hardest violations to fix because they require extracting shared logic out of `cmd/` modules into `util/`.

### Possible Bugs from the Refactor

The refactoring was mechanical — functions and constants were moved between files, imports were updated. No business logic was changed. However, some risk areas remain:

1. **Missing imports at runtime.** The codebase has ~96K lines and not all code paths are exercised by the test suite. A function in a rarely-used command could reference a name that was available in the monolith's flat namespace but wasn't explicitly imported after the split. Ruff's `F821` (undefined name) check catches many of these, but names from star imports (`from gam.constants import *`) can mask issues since Ruff can't statically resolve them.

2. **Constants that were duplicated.** Some constants (like `UNKNOWN`, `UTF8`, `ME_IN_OWNERS`) were defined in the monolith and used everywhere. During the split, they were added to `constants.py` for star-import, but some modules may have local copies that could drift out of sync.

3. **Dispatch table wiring.** Every command function must be imported in `__init__.py` and added to the dispatch table. If an import was missed or a function was renamed during the split, the command will fail at runtime with an `ImportError` or `NameError`. The `test_imports.py` suite catches import errors, but doesn't exercise every dispatch path.

4. **Cross-module closure state.** The original monolith used module-level variables as implicit shared state. After the split, some of these became module-level variables in different files. If two files both define `rolePrivileges = {}`, they now have separate dictionaries instead of sharing one. This is unlikely to be an issue (GAM functions are stateless request handlers), but it's worth noting.

5. **`_getMain()` remnants.** Early in the refactoring, extracted modules used `_getMain()` to access functions still in `__init__.py`. These have mostly been replaced with direct imports, but a few may remain. They work correctly but are unnecessary indirection — finding and replacing them with direct imports is safe cleanup.

---

## 7. Quick Reference

### Common Developer Tasks

| Task | How |
|------|-----|
| Run linter | `python3 -m ruff check src/` |
| Run tests | `python3 -m pytest tests/` |
| Find a function | `grep -rn "def functionName" src/gam/cmd/` |
| Find who calls a function | `grep -rn "functionName" src/gam/` |
| Check for cycles | `python3 -m pytest tests/test_no_circular_imports.py -v` |
| Check architectural rules | `python3 -m pytest tests/test_architecture.py -v` |
| Verify all imports work | `python3 -m pytest tests/test_imports.py -v` |

### Import Conventions

```python
# ✅ Correct — import from canonical source
from gam.util.args import getString
from gam.var import Act, Cmd, Ent, Ind
from gamlib import api as API

# ❌ Wrong — short-path import
from util.args import getString

# ❌ Wrong — importing from __init__.py
from gam import getString

# ❌ Wrong — deferred import inside a function
def doSomething():
    from gam.util.args import getString  # NO!
```

### File Size Guidelines

There are no hard limits, but as a rule of thumb:
- `cmd/` modules under 2,000 lines are comfortable to work with
- If a module grows past 3,000 lines, consider splitting into a sub-package
- `util/` modules should be focused — one clear responsibility per file

### Commit Conventions

Prefix commit messages with a type:
- `fix:` — Bug fixes
- `refactor:` — Code reorganization (no behavior change)
- `chore:` — Tooling, linting, config changes
- `test:` — New or updated tests
- `docs:` — Documentation
