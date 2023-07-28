# -*- mode: python ; coding: utf-8 -*-
from os import getenv
from re import search
from sys import platform

from PyInstaller.utils.hooks import copy_metadata

from gam.gamlib.glverlibs import GAM_VER_LIBS

datas = []
for pkg in GAM_VER_LIBS:
    datas += copy_metadata(pkg, recursive=True)
datas += [('cbcm-v1.1beta1.json', '.')]
datas += [('contactdelegation-v1.json', '.')]
datas += [('admin-directory_v1.1beta1.json', '.')]
datas += [('cacerts.pem', '.')]
hiddenimports = [
     'gam.auth.yubikey',
     ]

a = Analysis(
    ['gam/__main__.py'],
    pathex=[],
    binaries=[],
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
        if getenv('arch') == 'universal2':
            target_arch = "universal2"
        else:
            target_arch = None
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
if not getenv('PYINSTALLER_BUILD_ONEDIR') == 'yes':
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

