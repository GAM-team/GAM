# -*- mode: python ; coding: utf-8 -*-
from os import getenv
from re import search
from sys import platform

from PyInstaller.utils.hooks import (collect_all,
                                    copy_metadata)

from gam.var import GAM_VER_LIBS

datas = []
for pkg in GAM_VER_LIBS:
    datas += copy_metadata(pkg, recursive=True)
datas += [('cbcm-v1.1beta1.json', '.')]
datas += [('contactdelegation-v1.json', '.')]
datas += [('admin-directory_v1.1beta1.json', '.')]
datas += [('roots.pem', '.')]
hiddenimports = [
     'gam.auth.yubikey',
     ]
tmp_ret = collect_all('cryptography')
datas += tmp_ret[0]
binaries += [tmp_ret[1]]
hiddenimports += tmp_ret[2]

a = Analysis(
    ['gam/__main__.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
for d in a.datas:
    if 'pyconfig' in d[0]:
        a.datas.remove(d)
        break
pyz = PYZ(a.pure,
          a.zipped_data,
          cipher=None)
# requires Python 3.10+ but no one should be compiling
# GAM with older versions anyway
match platform:
    case "darwin":
        target_arch = "universal2"
        strip = True
    case "win32":
        target_arch = None
        strip = False
    case _:
        target_arch = None
        strip = True
name = 'gam'
debug = False
bootloader_ignore_signals = False
upx = False
console = True
disable_windowed_traceback = False
argv_emulation = False
codesign_identity = None
entitlements_file = None
if getenv('PYINSTALLER_BUILD_ONEFILE') == 'yes':
    # Build one file
    exe = EXE(
              pyz,
              a.scripts,
              a.binaries,
              a.zipfiles,
              a.datas,
              [],
              name=name,
              debug=debug,
              bootloader_ignore_signals=bootloader_ignore_signals,
              strip=strip,
              upx=upx,
              console=console,
              disable_windowed_traceback=disable_windowed_traceback,
              argv_emulation=argv_emulation,
              target_arch=target_arch,
              codesign_identity=codesign_identity,
              entitlements_file=entitlements_file,
              )
else:
    # Build one folder
    exe = EXE(
              pyz,
              a.scripts,
              [],
              exclude_binaries=True,
              name=name,
              debug=debug,
              bootloader_ignore_signals=bootloader_ignore_signals,
              strip=strip,
              upx=upx,
              console=console,
              disable_windowed_traceback=disable_windowed_traceback,
              argv_emulation=argv_emulation,
              target_arch=target_arch,
              codesign_identity=codesign_identity,
              entitlements_file=entitlements_file,
              )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=strip,
        upx=upx,
        upx_exclude=[],
        name=name,
        )

