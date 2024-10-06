# Install GAM as Python Library

Thanks to Jay Lee for showing me how to do this.

On Windows, you need to install Git to use the pip command.
* See: https://pythoninoffice.com/python-pip-install-from-github/

Scroll down to Install Git

You can install GAM as a Python library with pip.
```
pip install git+https://github.com/GAM-team/GAM.git#subdirectory=src
```

Or as a PEP 508 Requirement Specifier, e.g. in requirements.txt file:
```
advanced-gam-for-google-workspace @ git+https://github.com/GAM-team/GAM.git#subdirectory=src
```

Or a pyproject.toml file:
```
[project]
name = "your-project"
# ...
dependencies = [
    "advanced-gam-for-google-workspace @ git+https://github.com/GAM-team/GAM.git#subdirectory=src"
]
```

Target a specific revision or tag:
```
advanced-gam-for-google-workspace @ git+https://github.com/GAM-team/GAM.git@v6.76.01#subdirectory=src
```

## Using the library

```
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Sample Python script to call GAM"""

import multiprocessing
import platform

from gam import initializeLogging, CallGAMCommand

if __name__ == '__main__':
# One time initialization
  if platform.system() != 'Linux':
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn')
  initializeLogging()
#
  CallGAMCommand(['gam', 'version'])
  # Issue command, output goes to stdout/stderr
  rc = CallGAMCommand(['gam', 'info', 'domain'])
  # Issue command, redirect stdout/stderr
  rc = CallGAMCommand(['gam', 'redirect', 'stdout', 'domain.txt', 'redirect', 'stderr', 'stdout', 'info', 'domain'])
```
