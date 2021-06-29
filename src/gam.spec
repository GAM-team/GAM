# -*- mode: python -*-

import sys

import importlib
from PyInstaller.utils.hooks import copy_metadata

import os
import importlib.util
var_file = os.path.join(os.getcwd(), 'gam/var.py')
spec = importlib.util.spec_from_file_location('gam.var', var_file)
gam_var = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gam_var)
# dynamically determine where httplib2/cacerts.txt lives
proot = os.path.dirname(importlib.import_module('httplib2').__file__)
extra_files = [(os.path.join(proot, 'cacerts.txt'), 'httplib2')]

extra_files += copy_metadata('google-api-python-client')
extra_files += [('cbcm-v1.1beta1.json', '.')]
extra_files += [('contactdelegation-v1.json', '.')]
extra_files += [('versionhistory-v1.json', '.')]

hidden_imports = [
     'gam.auth.yubikey',
     ]

a = Analysis(['gam/__main__.py'],
             hiddenimports=hidden_imports,
             hookspath=None,
             excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter'],
             datas=extra_files,
             runtime_hooks=None)

for d in a.datas:
    if 'pyconfig' in d[0]:
        a.datas.remove(d)
        break


pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='gam',
          debug=False,
          strip=None,
          upx=False,
          console=True,
          version=gam_var.GAM_VERSION)
