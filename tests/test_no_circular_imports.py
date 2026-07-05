"""Detect circular imports between util/ modules.

Uses AST-based static analysis to build a directed import graph of all
modules under src/gam/util/, then runs DFS-based cycle detection.
Run this as a CI gate to prevent future circular dependencies.

Usage:
    python tests/test_no_circular_imports.py
    # or via pytest:
    pytest tests/test_no_circular_imports.py -v
"""

import ast
import os
import sys
import unittest
from collections import defaultdict
from pathlib import Path

# Resolve project root
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SRC_DIR = PROJECT_ROOT / 'src' / 'gam'
UTIL_DIR = SRC_DIR / 'util'


def _module_name_from_path(filepath: Path) -> str:
    """Convert a filesystem path to a dotted module name relative to src/gam/."""
    rel = filepath.relative_to(SRC_DIR)
    parts = list(rel.parts)
    if parts[-1] == '__init__.py':
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].removesuffix('.py')
    return '.'.join(parts)


def _collect_util_modules() -> dict[str, Path]:
    """Return a mapping of dotted module names → file paths for all util/ .py files."""
    modules = {}
    for py_file in UTIL_DIR.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        mod_name = _module_name_from_path(py_file)
        modules[mod_name] = py_file
    return modules


def _normalize_import(raw_module: str) -> str | None:
    """Normalize an import string to a dotted name relative to src/gam/.

    Handles both 'util.foo' and 'gam.util.foo' styles.
    Returns None if the import is not a util/ module.
    """
    if raw_module.startswith('gam.util.'):
        return raw_module.removeprefix('gam.')
    if raw_module.startswith('util.'):
        return raw_module
    return None


def _extract_imports(filepath: Path) -> set[str]:
    """Parse a Python file and return the set of util.* modules it imports from."""
    source = filepath.read_text(encoding='utf-8')
    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        return set()

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            normalized = _normalize_import(node.module)
            if normalized:
                imports.add(normalized)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                normalized = _normalize_import(alias.name)
                if normalized:
                    imports.add(normalized)
    return imports


def build_import_graph() -> dict[str, set[str]]:
    """Build a directed graph: module → set of util modules it imports."""
    modules = _collect_util_modules()
    graph = defaultdict(set)

    for mod_name, filepath in modules.items():
        raw_imports = _extract_imports(filepath)
        for imp in raw_imports:
            # Only track edges to modules that actually exist in our util/ tree.
            # An import like 'util.foo' might resolve to 'util.foo' (module)
            # or 'util.foo.__init__', so check both.
            if imp in modules or imp + '.__init__' in modules:
                target = imp if imp in modules else imp + '.__init__'
                if target != mod_name:  # skip self-imports
                    graph[mod_name].add(target)

    return dict(graph)


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Find all simple cycles in the directed graph using DFS.

    Returns a list of cycles, where each cycle is a list of module names
    forming a loop (e.g., ['util.a', 'util.b', 'util.a']).
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = defaultdict(int)
    cycles = []
    path = []

    def dfs(node):
        color[node] = GRAY
        path.append(node)
        for neighbor in graph.get(node, []):
            if color[neighbor] == GRAY:
                # Found a cycle — extract it
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)
            elif color[neighbor] == WHITE:
                dfs(neighbor)
        path.pop()
        color[node] = BLACK

    all_nodes = set(graph.keys())
    for edges in graph.values():
        all_nodes.update(edges)

    for node in sorted(all_nodes):
        if color[node] == WHITE:
            dfs(node)

    return cycles


class TestNoCircularImports(unittest.TestCase):
    """Ensure no circular imports exist between util/ modules."""

    def test_no_cycles_in_util(self):
        graph = build_import_graph()
        cycles = find_cycles(graph)

        if cycles:
            msg_lines = ['Circular imports detected between util/ modules:\n']
            for cycle in cycles:
                msg_lines.append('  → '.join(cycle))
            self.fail('\n'.join(msg_lines))


if __name__ == '__main__':
    # When run directly, print a human-readable report
    print(f'Scanning {UTIL_DIR} for circular imports...\n')
    graph = build_import_graph()

    print(f'Found {len(graph)} modules with util/ dependencies:\n')
    for mod, deps in sorted(graph.items()):
        print(f'  {mod}')
        for dep in sorted(deps):
            print(f'    → {dep}')

    cycles = find_cycles(graph)
    if cycles:
        print(f'\n❌ {len(cycles)} circular import(s) found:\n')
        for cycle in cycles:
            print('  ' + ' → '.join(cycle))
        sys.exit(1)
    else:
        print('\n✅ No circular imports detected.')
        sys.exit(0)
