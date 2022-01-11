#!/usr/bin/env python3

from packaging import version
import sys

a = sys.argv[1]
b = sys.argv[2]
result = version.parse(a) >= version.parse(b)
if result:
    print(f'OK: {a} is equal or newer than {b}')
else:
    print(f'ERROR: {a} is older than {b}')
sys.exit(not result)
