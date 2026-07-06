"""Architectural guardrail tests for the GAM codebase.

These tests enforce the project's layering and import rules to prevent
circular dependencies and architectural regressions. They analyze the
source code statically — no modules are imported (except for Rule 5).

Rules enforced:
    1. util/ modules must NEVER import from cmd/ modules.
    2. cmd/ modules must not form NEW import cycles with each other.
    3. No NEW deferred (function-scope) imports.
    4. gamlib/ modules must NEVER import from gam/ or util/.
    5. Undefined global references must not increase (ratchet).
    6. No short-path ``from util.X`` imports — use ``from gam.util.X``.
    7. No ``sys.modules`` manipulation for module aliasing.
"""

import ast
import os
from collections import defaultdict
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / 'src'
GAM_DIR = SRC_DIR / 'gam'
UTIL_DIR = GAM_DIR / 'util'
CMD_DIR = GAM_DIR / 'cmd'
GAMLIB_DIR = GAM_DIR / 'gamlib'


def _iter_python_files(directory: Path):
    """Yield absolute Path for every .py file under directory."""
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for fname in sorted(files):
            if fname.endswith('.py'):
                yield Path(root) / fname


def _parse_imports(filepath: Path):
    """Parse a Python file and return all import AST nodes."""
    try:
        source = filepath.read_text(encoding='utf-8')
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        return []
    return [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]


def _get_import_module_names(node):
    """Extract dotted module name(s) from an import AST node."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.module:
        return [node.module]
    return []


def _imports_cmd(mod_name):
    """Return True if mod_name refers to a cmd module."""
    return (mod_name.startswith('gam.cmd.')
            or mod_name.startswith('cmd.')
            or mod_name == 'gam.cmd'
            or mod_name == 'cmd')


# ──────────────────────────────────────────────────────────────────────
# Rule 1: util/ must NEVER import from cmd/
# ──────────────────────────────────────────────────────────────────────

class TestUtilNeverImportsCmd:
    """util/ is the foundation layer — it must not depend on cmd/.

    KNOWN_VIOLATIONS lists existing violations being actively cleaned up.
    The allowlist must only SHRINK — any new violations fail the test.
    """

    # (filename, imported_module_prefix) — remove entries as they are fixed.
    KNOWN_VIOLATIONS = {
        # entity.py references cmd-level functions via __init__.py re-exports
        ('entity.py', 'gam.cmd'),
        # batch.py contains cmd-level handlers (doBatch, doCSV) that import
        # from cmd/drive/gdoc_fetch.  Should migrate to cmd/ eventually.
        ('batch.py', 'gam.cmd'),
        # api.py uses yubikey module for hardware key auth
        ('api.py', 'gam.cmd'),
        # tags.py references resources for tag substitution
        ('tags.py', 'gam.cmd'),
    }

    def test_util_does_not_import_cmd(self):
        """No util/ module should import from gam.cmd.* or cmd.*."""
        violations = []
        for filepath in _iter_python_files(UTIL_DIR):
            fname = filepath.name
            for node in _parse_imports(filepath):
                for mod_name in _get_import_module_names(node):
                    if not mod_name or not _imports_cmd(mod_name):
                        continue
                    # Check if this is a known violation
                    if any(fname == kf and mod_name.startswith(kp)
                           for kf, kp in self.KNOWN_VIOLATIONS):
                        continue
                    violations.append(
                        f'  {fname}:{node.lineno}: {mod_name}'
                    )

        assert not violations, (
            f'\n\nARCHITECTURE VIOLATION: {len(violations)} NEW util/ → cmd/ '
            f'import(s) detected.\n'
            f'util/ is the foundation layer and must NEVER depend on cmd/.\n'
            f'Move the needed function/constant DOWN into util/ or a shared '
            f'constants module.\n\n'
            + '\n'.join(violations)
        )


# ──────────────────────────────────────────────────────────────────────
# Rule 2: No NEW circular imports between cmd/ modules
# ──────────────────────────────────────────────────────────────────────

class TestNoCmdCircularImports:
    """cmd/ modules may import from each other, but must not form NEW cycles."""

    # Existing direct cycles being resolved. Remove entries as they are fixed.
    KNOWN_DIRECT_CYCLES = {
        frozenset({'gam.cmd.customer', 'gam.cmd.domains'}),
        frozenset({'gam.cmd.calendar.acls', 'gam.cmd.calendar.resources'}),
        frozenset({'gam.cmd.calendar.acls', 'gam.cmd.calendar.calendars'}),
        frozenset({'gam.cmd.calendar.calendars', 'gam.cmd.calendar.settings'}),
        frozenset({'gam.cmd.calendar.calendars', 'gam.cmd.calendar.events'}),
        frozenset({'gam.cmd.calendar.dispatch', 'gam.cmd.calendar.resources'}),
        frozenset({'gam.cmd.groups.groups', 'gam.cmd.groups.members'}),
        frozenset({'gam.cmd.people.contacts', 'gam.cmd.people.domainprofiles'}),
        frozenset({'gam.cmd.people.contacts', 'gam.cmd.people.othercontacts'}),
    }

    def _build_cmd_import_graph(self):
        """Build module-level dependency graph for cmd/ (non-__init__) modules."""
        graph = defaultdict(set)
        for filepath in _iter_python_files(CMD_DIR):
            rel = filepath.relative_to(SRC_DIR)
            parts = list(rel.parts)
            if parts[-1] == '__init__.py':
                continue  # skip aggregator modules
            mod_name = '.'.join(parts)[:-3]

            for node in _parse_imports(filepath):
                for imp_mod in _get_import_module_names(node):
                    if imp_mod and imp_mod.startswith('gam.cmd.'):
                        graph[mod_name].add(imp_mod)
        return graph

    def test_no_new_direct_circular_imports(self):
        """No NEW A↔B circular imports between cmd/ modules."""
        graph = self._build_cmd_import_graph()

        direct_cycles = set()
        for mod_a, deps in graph.items():
            for mod_b in deps:
                if mod_a in graph.get(mod_b, set()):
                    direct_cycles.add(frozenset({mod_a, mod_b}))

        new_cycles = direct_cycles - self.KNOWN_DIRECT_CYCLES
        assert not new_cycles, (
            f'\n\nARCHITECTURE VIOLATION: {len(new_cycles)} NEW direct '
            f'circular import(s) between cmd/ modules:\n\n'
            + '\n'.join(f'  {sorted(c)[0]} ↔ {sorted(c)[1]}' for c in new_cycles)
            + '\n\nBreak the cycle by moving shared constants/functions '
            'to a lower-level module (e.g. core.py, setup.py, or constants.py).'
        )

    def test_known_cycles_count_only_decreases(self):
        """If a known cycle is fixed, remind developer to remove it."""
        graph = self._build_cmd_import_graph()

        actual_cycles = set()
        for mod_a, deps in graph.items():
            for mod_b in deps:
                if mod_a in graph.get(mod_b, set()):
                    actual_cycles.add(frozenset({mod_a, mod_b}))

        resolved = self.KNOWN_DIRECT_CYCLES - actual_cycles
        if resolved:
            pytest.skip(
                f'Congrats! These cycles are resolved — remove from '
                f'KNOWN_DIRECT_CYCLES: {[sorted(c) for c in resolved]}'
            )


# ──────────────────────────────────────────────────────────────────────
# Rule 3: No NEW deferred (function-scope) imports
# ──────────────────────────────────────────────────────────────────────

class TestNoDeferredImports:
    """All imports must be at module top-level (Pythonic style).

    Existing deferred imports are tracked in an allowlist. The allowlist
    must only SHRINK — any new deferred imports fail the test immediately.
    """

    # (relative_path, line_number) of existing deferred imports.
    KNOWN_DEFERRED_UTIL = set()

    KNOWN_DEFERRED_CMD = {
        ('gam/cmd/calendar/resources.py', 13),  # cycle: resources <-> dispatch
        ('gam/cmd/people/contacts.py', 723),    # cycle: contacts <-> othercontacts
    }

    def test_no_new_deferred_imports_in_util(self):
        """No NEW function-scope imports in util/."""
        self._check_directory(UTIL_DIR, 'util', self.KNOWN_DEFERRED_UTIL)

    def test_no_new_deferred_imports_in_cmd(self):
        """No NEW function-scope imports in cmd/."""
        self._check_directory(CMD_DIR, 'cmd', self.KNOWN_DEFERRED_CMD)

    def _check_directory(self, directory: Path, label: str, known: set):
        violations = []
        for filepath in _iter_python_files(directory):
            try:
                source = filepath.read_text(encoding='utf-8')
                tree = ast.parse(source, filename=str(filepath))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for child in ast.walk(node):
                    if not isinstance(child, (ast.Import, ast.ImportFrom)):
                        continue
                    rel_path = str(filepath.relative_to(SRC_DIR))
                    key = (rel_path, child.lineno)
                    if key in known:
                        continue
                    mod_names = _get_import_module_names(child)
                    violations.append(
                        f'  {rel_path}:{child.lineno}: '
                        f'{"from " + mod_names[0] if mod_names else "import ..."}'
                    )

        assert not violations, (
            f'\n\nARCHITECTURE VIOLATION: {len(violations)} NEW deferred '
            f'import(s) found in {label}/.\n'
            f'All imports must be at module top-level — deferred/inline '
            f'imports are strictly prohibited.\n'
            f'If you need a name from another module, add a top-level import '
            f'or refactor to break the cycle.\n\n'
            + '\n'.join(violations)
        )


# ──────────────────────────────────────────────────────────────────────
# Rule 4: gamlib/ must NEVER import from gam/ or util/
# ──────────────────────────────────────────────────────────────────────

class TestGamlibIndependence:
    """gamlib/ is the lowest layer — it must not import from gam/ or util/."""

    def test_gamlib_does_not_import_gam_or_util(self):
        """gamlib/ modules should never import from gam.* or util.*."""

        violations = []
        for filepath in _iter_python_files(GAMLIB_DIR):
            for node in _parse_imports(filepath):
                for mod_name in _get_import_module_names(node):
                    if not mod_name:
                        continue
                    if (mod_name.startswith('gam.')
                            or mod_name.startswith('util.')
                            or mod_name == 'gam'
                            or mod_name == 'util'):
                        violations.append(
                            f'  {filepath.name}:{node.lineno}: {mod_name}'
                        )

        assert not violations, (
            '\n\nARCHITECTURE VIOLATION: gamlib/ imports from gam/ or util/.\n'
            'gamlib/ is the lowest layer and must be fully independent.\n\n'
            + '\n'.join(violations)
        )


# ──────────────────────────────────────────────────────────────────────
# Rule 5: Undefined global references ratchet (cannot increase)
# ──────────────────────────────────────────────────────────────────────

class TestUndefinedGlobalsRatchet:
    """Functions must not reference names that aren't defined or imported.

    This is a ratchet test: the count can only decrease. Update
    MAX_ALLOWED as you fix issues to lock in progress.
    """

    # Current count. ONLY decrease this number as issues are fixed.
    MAX_ALLOWED = 443

    def test_undefined_globals_do_not_increase(self):
        """The number of undefined global references must not grow."""
        import dis
        import types
        import builtins
        import importlib

        builtin_names = set(dir(builtins))

        def get_global_loads(code_obj):
            names = set()
            for instr in dis.get_instructions(code_obj):
                if instr.opname in ('LOAD_GLOBAL', 'LOAD_GLOBAL_AND_NULL',
                                    'LOAD_GLOBAL_MORPH'):
                    names.add(instr.argval)
            for const in code_obj.co_consts:
                if isinstance(const, types.CodeType):
                    names.update(get_global_loads(const))
            return names

        errors = []
        for filepath in _iter_python_files(GAM_DIR):
            if filepath.name == '__init__.py':
                continue
            rel = filepath.relative_to(SRC_DIR)
            mod_name = '.'.join(rel.parts)[:-3]
            try:
                mod = importlib.import_module(mod_name)
            except Exception:
                continue

            mod_globals = set(dir(mod))
            for attr_name in dir(mod):
                obj = getattr(mod, attr_name)
                if not isinstance(obj, types.FunctionType):
                    continue
                if obj.__module__ != mod.__name__:
                    continue
                referenced = get_global_loads(obj.__code__)
                for ref_name in sorted(referenced):
                    if ref_name in mod_globals or ref_name in builtin_names:
                        continue
                    errors.append(f'{mod_name}.{attr_name}(): {ref_name}')

        count = len(errors)
        assert count <= self.MAX_ALLOWED, (
            f'\n\nREGRESSION: Undefined globals increased from '
            f'{self.MAX_ALLOWED} to {count}.\n'
            f'Fix the new undefined references or check if a recent change '
            f'removed an import that was needed.\n\n'
            f'New issues (first 20):\n'
            + '\n'.join(f'  {e}' for e in errors[:20])
        )

        # Nudge developers to tighten the ratchet
        if count < self.MAX_ALLOWED - 5:
            print(
                f'\n  ✓ Undefined globals dropped to {count} '
                f'(cap is {self.MAX_ALLOWED}). '
                f'Update MAX_ALLOWED in test_architecture.py to {count} '
                f'to lock in progress.'
            )


# ──────────────────────────────────────────────────────────────────────
# Rule 6: No short-path "from util.X" imports
# ──────────────────────────────────────────────────────────────────────

class TestNoShortPathImports:
    """All internal imports must use fully-qualified paths.

    ``from util.args import ...`` is BANNED.  Use ``from gam.util.args import ...``.

    The short-path style only works because __init__.py adds src/gam/ to
    sys.path, which causes Python to register modules under *two* names
    (util.X and gam.util.X).  That dual registration was the root cause of
    the sys.modules aliasing hacks.  Zero tolerance — no allowlist.
    """

    def test_no_short_path_util_imports(self):
        """No file under gam/ may use 'from util.X import ...'."""
        violations = []
        for filepath in _iter_python_files(GAM_DIR):
            for node in _parse_imports(filepath):
                for mod_name in _get_import_module_names(node):
                    if not mod_name:
                        continue
                    if (mod_name.startswith('util.')
                            or mod_name == 'util'):
                        violations.append(
                            f'  {filepath.relative_to(SRC_DIR)}:{node.lineno}: '
                            f'{mod_name}  →  use gam.{mod_name}'
                        )

        assert not violations, (
            f'\n\nARCHITECTURE VIOLATION: {len(violations)} short-path '
            f'import(s) found.\n'
            f'Use "from gam.util.X import ..." not "from util.X import ...".\n'
            f'Short paths cause dual module registration in sys.modules.\n\n'
            + '\n'.join(violations)
        )


# ──────────────────────────────────────────────────────────────────────
# Rule 7: No sys.modules manipulation for module aliasing
# ──────────────────────────────────────────────────────────────────────

class TestNoSysModulesAliasing:
    """sys.modules must not be manipulated to paper over import path issues.

    The codebase previously used sys.modules aliasing to synchronize
    short-path (util.X) and fully-qualified (gam.util.X) module objects.
    That hack is now eliminated.  This test ensures it never returns.
    """

    # Patterns that are legitimate sys.modules usage (not aliasing)
    _LEGITIMATE_PATTERNS = {
        # yubikey.py looks up the gam module for the multiprocessing lock
        "sys.modules['gam']",
    }

    def test_no_sys_modules_aliasing(self):
        """No source file may manipulate sys.modules for aliasing."""
        import re
        violations = []
        for filepath in _iter_python_files(GAM_DIR):
            source = filepath.read_text(encoding='utf-8')
            for i, line in enumerate(source.splitlines(), 1):
                stripped = line.strip()
                if 'sys.modules' not in stripped:
                    continue
                # Skip comments
                if stripped.startswith('#'):
                    continue
                # Skip known legitimate uses
                if any(pat in stripped for pat in self._LEGITIMATE_PATTERNS):
                    continue
                violations.append(
                    f'  {filepath.relative_to(SRC_DIR)}:{i}: {stripped}'
                )

        assert not violations, (
            f'\n\nARCHITECTURE VIOLATION: {len(violations)} sys.modules '
            f'manipulation(s) found.\n'
            f'sys.modules aliasing was eliminated — do not reintroduce it.\n'
            f'Fix the root cause (use canonical import paths) instead.\n\n'
            + '\n'.join(violations)
        )
