#!/usr/bin/env python3
"""Inject a version string into gam/__init__.py at build time."""
import re
import sys

if len(sys.argv) != 3:
    print(f'Usage: {sys.argv[0]} <file> <version>', file=sys.stderr)
    sys.exit(1)

target, version = sys.argv[1], sys.argv[2]
content = open(target, encoding='utf-8').read()
updated = re.sub(
    r"^__version__ = .*$",
    f"__version__ = '{version}'",
    content,
    count=1,
    flags=re.MULTILINE,
)
if updated == content:
    print(f'ERROR: no __version__ line found in {target}', file=sys.stderr)
    sys.exit(1)
open(target, 'w', encoding='utf-8').write(updated)
print(f'{target}: __version__ = \'{version}\'')
