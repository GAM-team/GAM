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

    def test_cmd_package_globals(self):
        """Every function in split cmd/ packages should resolve all global names.

        After splitting monolithic cmd/ files into packages, submodules may
        reference names that were in scope in the original file but weren't
        explicitly imported into the new submodule. These show up as NameError
        at runtime when the specific code path is hit.

        This test catches such issues statically by inspecting each function's
        bytecode for LOAD_GLOBAL instructions and verifying the referenced
        names exist in the module's global namespace (or are builtins).
        """
        import dis
        import types
        import builtins

        CMD_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'gam', 'cmd')
        CMD_DIR = os.path.normpath(CMD_DIR)

        # Packages that were split from monolithic files
        SPLIT_PACKAGES = ['calendar', 'cros', 'gmail', 'groups', 'people']

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

        errors = []
        for pkg_name in SPLIT_PACKAGES:
            pkg_dir = os.path.join(CMD_DIR, pkg_name)
            if not os.path.isdir(pkg_dir):
                continue

            for fname in sorted(os.listdir(pkg_dir)):
                if not fname.endswith('.py') or fname == '__init__.py':
                    continue

                mod_name = f'gam.cmd.{pkg_name}.{fname[:-3]}'
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
            f"Found {len(errors)} undefined global reference(s) in split "
            f"cmd/ packages (likely missing imports):\n" +
            "\n".join(errors)
        )

