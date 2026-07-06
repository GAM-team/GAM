"""Structural tests — verify all modules import without errors."""

import importlib
import os
import sys

import pytest


class TestAllModulesImport:
    """Every module in gam/ should import without errors."""

    def test_gam_package_imports(self):
        """The top-level gam package should import without circular import errors."""
        import gam
        assert hasattr(gam, 'ProcessGAMCommand')

    def test_util_modules_import(self):
        """All util/ modules should import individually without errors."""
        util_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'gam', 'util')
        util_dir = os.path.normpath(util_dir)

        failures = []
        for f in sorted(os.listdir(util_dir)):
            if not f.endswith('.py') or f == '__init__.py':
                continue
            mod_name = f'gam.util.{f[:-3]}'
            try:
                importlib.import_module(mod_name)
            except Exception as e:
                failures.append(f'{mod_name}: {e}')

        assert not failures, "Failed to import:\n" + "\n".join(failures)

    def test_no_local_imports_in_util(self):
        """util/ modules should not have function-scope imports from other util/ modules."""
        import re
        util_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'gam', 'util')
        util_dir = os.path.normpath(util_dir)

        KNOWN_EXCEPTIONS = set()

        violations = []
        for f in sorted(os.listdir(util_dir)):
            if not f.endswith('.py') or f == '__init__.py':
                continue
            with open(os.path.join(util_dir, f)) as fh:
                for i, line in enumerate(fh, 1):
                    if re.match(r'^\s+from (util|gam\.util)\.\w+ import', line):
                        text = line.strip().split('#')[0].strip()
                        if (f, text) not in KNOWN_EXCEPTIONS:
                            violations.append(f'{f}:{i}: {line.strip()}')

        assert not violations, (
            f"Found {len(violations)} unexpected local import(s) in util/:\n"
            + "\n".join(violations)
        )

    def test_init_stdlib_import_count(self):
        """Guard against stdlib import bloat creeping back into __init__.py.

        After the cleanup, __init__.py should only import the ~8 stdlib
        modules it actually uses. This test catches accidental additions.
        """
        init_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'gam', '__init__.py')
        with open(os.path.normpath(init_path)) as f:
            lines = f.readlines()

        stdlib_imports = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('import ') and not stripped.startswith(
                ('import gam', 'import google', 'import httplib2',
                 'import arrow', 'import distro', 'import termios')):
                stdlib_imports.append(stripped)

        # Currently 8: http.client, importlib, logging, os, platform, re, sys, types
        assert len(stdlib_imports) <= 10, (
            f"__init__.py has {len(stdlib_imports)} stdlib imports (max 10). "
            f"New stdlib imports should go in the module that uses them, "
            f"not __init__.py.\n" + "\n".join(stdlib_imports)
        )

    def test_all_module_globals(self):
        """Every function in cmd/, util/, and gamlib/ should resolve all global names.

        After extracting code from the monolithic __init__.py into sub-modules,
        functions may reference names that were in scope in the original file
        but weren't explicitly imported into the new module. These show up as
        NameError at runtime when the specific code path is hit.

        This test catches such issues statically by inspecting each function's
        bytecode for LOAD_GLOBAL instructions and verifying the referenced
        names exist in the module's global namespace (or are builtins).
        """
        import dis
        import types
        import builtins
        from pathlib import Path

        GAM_DIR = Path(__file__).resolve().parent.parent / 'src' / 'gam'
        builtin_names = set(dir(builtins))

        def get_global_loads(code_obj):
            """Extract names loaded via LOAD_GLOBAL from a code object, recursively."""
            names = set()
            for instr in dis.get_instructions(code_obj):
                if instr.opname in ('LOAD_GLOBAL', 'LOAD_GLOBAL_AND_NULL',
                                    'LOAD_GLOBAL_MORPH'):
                    names.add(instr.argval)
            # Check nested code objects (inner functions, comprehensions)
            for const in code_obj.co_consts:
                if isinstance(const, types.CodeType):
                    names.update(get_global_loads(const))
            return names

        def discover_modules(base_dir, package_prefix):
            """Discover all .py modules under a directory, returning dotted module names."""
            modules = []
            for py_file in sorted(base_dir.rglob('*.py')):
                if '__pycache__' in str(py_file) or py_file.name == '__init__.py':
                    continue
                rel = py_file.relative_to(base_dir)
                parts = list(rel.parts)
                parts[-1] = parts[-1].removesuffix('.py')
                mod_name = f'{package_prefix}.{".".join(parts)}'
                modules.append(mod_name)
            return modules

        # Discover all modules across cmd/, util/, and gamlib/
        all_modules = []
        for subdir, prefix in [('cmd', 'gam.cmd'), ('util', 'gam.util'), ('gamlib', 'gamlib')]:
            target = GAM_DIR / subdir if subdir != 'gamlib' else GAM_DIR.parent.parent / 'src' / subdir
            # gamlib lives alongside gam, not inside it
            if subdir == 'gamlib':
                target = GAM_DIR.parent / subdir
            if target.is_dir():
                all_modules.extend(discover_modules(target, prefix))

        errors = []
        for mod_name in all_modules:
            try:
                mod = importlib.import_module(mod_name)
            except Exception as e:
                errors.append(f'{mod_name}: import failed: {e}')
                continue

            mod_globals = set(dir(mod))

            for attr_name in dir(mod):
                obj = getattr(mod, attr_name)
                if not isinstance(obj, types.FunctionType):
                    continue
                if obj.__module__ != mod.__name__:
                    continue  # skip re-exported functions

                referenced = get_global_loads(obj.__code__)
                for ref_name in sorted(referenced):
                    if ref_name in mod_globals or ref_name in builtin_names:
                        continue
                    errors.append(
                        f'{mod_name}.{attr_name}() references '
                        f'undefined global: {ref_name}'
                    )

        assert not errors, (
            f"Found {len(errors)} undefined global reference(s) "
            f"(likely missing imports):\n" +
            "\n".join(errors)
        )


