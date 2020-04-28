#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provides backwards compatibility for calling gam as a single .py file"""

import sys

from gam.__main__ import main

# Run from command line
if __name__ == '__main__':
    main(sys.argv)
