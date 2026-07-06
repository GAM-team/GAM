#!/usr/bin/env python3
"""Provides backwards compatibility for calling gam as a single .py file"""

import multiprocessing
import platform
import sys

# Run from command line
if __name__ == '__main__':
  if platform.system() != 'Linux':
    multiprocessing.freeze_support()
  # Python 3.14.4 and PyInstaller 6.19.0 don't play nice with Linux forkserver
  # use spawn everywhere for now.
  multiprocessing.set_start_method('spawn', force=True)
  try:
    from gam.__main__ import main
    main()
  except KeyboardInterrupt:
    sys.exit(8)
