# -*- mode: python -*-

import sys

import importlib
from PyInstaller.utils.hooks import copy_metadata

extra_files = []

extra_files += copy_metadata('google-api-python-client')
extra_files += [('cbcm-v1.1beta1.json', '.')]
extra_files += [('contactdelegation-v1.json', '.')]
extra_files += [('admin-directory_v1.1beta1.json', '.')]

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


if sys.platform == "darwin":
     target_arch="universal2"
else:
     target_arch=None

# use strip on all non-Windows platforms
strip = not sys.platform == 'win32'

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='gam',
          debug=False,
          strip=strip,
          upx=False,
          target_arch=target_arch,
          console=True)
