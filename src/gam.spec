# -*- mode: python ; coding: utf-8 -*-
from sys import platform
from PyInstaller.utils.hooks import copy_metadata


extra_files = []
extra_files += copy_metadata('google-api-python-client')
extra_files += [('cbcm-v1.1beta1.json', '.')]
extra_files += [('contactdelegation-v1.json', '.')]
extra_files += [('admin-directory_v1.1beta1.json', '.')]
extra_files += [('roots.pem', '.')]
hidden_imports = [
     'gam.auth.yubikey',
     ]
a = Analysis(
    ['gam/__main__.py'],
    pathex=[],
    binaries=[],
    datas=extra_files,
    hiddenimports=hidden_imports,
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
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='gam',
    debug=False,
    bootloader_ignore_signals=False,
    strip=strip,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=target_arch,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=strip,
    upx=False,
    upx_exclude=[],
    name='gam',
)

