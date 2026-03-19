# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is GAM

GAM (Google Workspace Admin Manager) is a command-line tool for Google Workspace administrators to manage domain and user settings via Google APIs. It is published as `gam7` on PyPI and distributed as pre-compiled binaries for Windows, macOS, and Linux.

## Development Setup

```bash
# Install in editable mode (with optional YubiKey support)
pip install -e .[yubikey]

# Run GAM directly
python -m gam <command>
```

## Build Commands

GAM uses `hatchling` as its build backend:

```bash
# Build wheel and sdist
python -m build

# Build compiled binary (PyInstaller)
python -m PyInstaller --clean --noconfirm --distpath="./dist/gam" gam.spec

# Build one-directory layout instead of single file
PYINSTALLER_BUILD_ONEDIR=yes python -m PyInstaller --clean --noconfirm --distpath="./dist/gam" gam.spec
```

## Testing

There is no traditional unit test suite. Testing is done exclusively via live integration tests against real Google Workspace APIs in the CI/CD pipeline (`build.yml`). There is no `pytest` or `unittest` framework to run locally.

## Code Architecture

### Entry Point

`src/gam/__main__.py` → calls `gam.initializeLogging()` then `gam.ProcessGAMCommand(sys.argv)`.

### Core Structure

```
src/gam/
├── __init__.py        # ~82,000-line monolithic file containing virtually all application logic
├── __main__.py        # CLI entry point
├── gamlib/            # Supporting library modules
│   ├── glapi.py       # Google API client wrapper, request handling, retry/error logic
│   ├── glcfg.py       # Configuration file management (credentials, gam.cfg)
│   ├── glclargs.py    # Command-line argument parsing
│   ├── glentity.py    # Entity management (users, groups, OUs, etc.)
│   ├── glgapi.py      # Google API wrappers and service builders
│   ├── glaction.py    # Action processing constants
│   ├── glmsgs.py      # All message/string constants
│   ├── glskus.py      # License SKU data
│   ├── gluprop.py     # User property definitions
│   ├── glglobals.py   # Global state (GC.Values, GM.Globals)
│   ├── glverlibs.py   # Version and library info
│   └── yubikey.py     # Optional YubiKey MFA support
├── atom/              # ATOM protocol support (legacy Google APIs)
├── gdata/             # Google Data client libraries (legacy)
└── cacerts.pem        # Bundled Mozilla CA certificates
```

### Architectural Patterns

- **Monolithic core**: Nearly all command parsing, API calls, and output formatting lives in `src/gam/__init__.py`. When looking for any feature, start there.
- **Global state**: `GC.Values` (config values) and `GM.Globals` (runtime state) defined in `gamlib/glglobals.py` are used throughout.
- **CSV output**: `CSVPrintFile` class handles all tabular output with consistent field ordering.
- **API client pattern**: Services are built via `glgapi.py` and called through `glapi.py` which handles pagination, retries, and error normalization.
- **Multiprocessing**: Bulk operations use Python's `multiprocessing` module; `freeze_support()` is called for PyInstaller compatibility.

### Key Configuration Files

- `pyproject.toml` — package metadata, dependencies, entry points
- `gam.spec` — PyInstaller build specification
- `gam.iss` / `gam.wxs` — Windows installer (Inno Setup / WiX)

## CI/CD

Three main workflows in `.github/workflows/`:
- **`build.yml`** — Builds native binaries for 12 platform/arch combinations (Ubuntu/macOS/Windows × Intel/ARM), code-signs them, then runs live Google Workspace API integration tests across Python 3.10–3.15
- **`pypi.yml`** — Publishes to PyPI on `v*.*.*` tags
- **`codeql-analysis.yml`** — Weekly CodeQL security scanning

Binary releases use custom-compiled Python and OpenSSL (cached in GCS) rather than system Python, to control security and compatibility.
