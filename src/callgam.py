#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Sample Python script to call GAM"""

import multiprocessing
import platform
import sys

if __name__ == '__main__':
# One time initialization
  if platform.system() != 'Linux':
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)
  try:
    from gam import CallGAMCommand
    from gam.util.batch import initializeLogging
    initializeLogging()
#
    CallGAMCommand(['gam', 'version'])
    # Issue command, output goes to stdout/stderr
    rc = CallGAMCommand(['gam', 'info', 'domain'])
    # Issue command, redirect stdout/stderr
    rc = CallGAMCommand(['gam', 'redirect', 'stdout', 'domain.txt', 'redirect', 'stderr', 'stdout', 'info', 'domain'])
  except KeyboardInterrupt:
    sys.exit(8)
