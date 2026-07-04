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
                ('import gam', 'import gdata', 'import google', 'import httplib2',
                 'import arrow', 'import distro', 'import termios')):
                stdlib_imports.append(stripped)

        # Currently 8: http.client, importlib, logging, os, platform, re, sys, types
        assert len(stdlib_imports) <= 10, (
            f"__init__.py has {len(stdlib_imports)} stdlib imports (max 10). "
            f"New stdlib imports should go in the module that uses them, "
            f"not __init__.py.\n" + "\n".join(stdlib_imports)
        )
