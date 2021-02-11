# -*- mode: python -*-

import sys

import importlib
from PyInstaller.utils.hooks import copy_metadata

sys.modules['FixTk'] = None

# dynamically determine where httplib2/cacerts.txt lives
proot = os.path.dirname(importlib.import_module('httplib2').__file__)
extra_files = [(os.path.join(proot, 'cacerts.txt'), 'httplib2')]

# dynamically determine where ykman/VERSION lives
yroot = os.path.dirname(importlib.import_module('ykman').__file__)
extra_files += [(os.path.join(yroot, 'VERSION'), 'ykman')]

extra_files += copy_metadata('google-api-python-client')
extra_files += [('cbcm-v1.1beta1.json', '.')]
extra_files += [('contactdelegation-v1.json', '.')]

a = Analysis(['gam/__main__.py'],
             hiddenimports=[],
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
          console=True )
