# -*- mode: python -*-

import sys

sys.modules['FixTk'] = None

a = Analysis(['gam.py'],
             hiddenimports=[],
             hookspath=None,
             excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter'],
             runtime_hooks=None)
for d in a.datas:
    if 'pyconfig' in d[0]:
        a.datas.remove(d)
        break
a.datas += [('cloudprint-v2.json', 'cloudprint-v2.json', 'DATA')]
a.datas += [('admin-directory_v2.json', 'admin-directory_v2.json', 'DATA')]

# dynamically determine where httplib2/cacerts.txt lives
import importlib
proot = os.path.dirname(importlib.import_module('httplib2').__file__)
a.datas += [('httplib2/cacerts.txt', os.path.join(proot, 'cacerts.txt'), 'DATA')]

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
