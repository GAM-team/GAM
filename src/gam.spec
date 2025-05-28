# -*- mode: python ; coding: utf-8 -*-
from os import getenv
import re
from sys import platform

from PyInstaller.utils.hooks import copy_metadata

from gam.gamlib.glverlibs import GAM_VER_LIBS


with open("gam/__init__.py") as f:
    version_file = f.read()
version = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M).group(1)
version_list = [int(i) for i in version.split('.')]
while len(version_list) < 4:
  version_list.append(0)
version_tuple = tuple(version_list)
version_str = str(version_tuple)
with open("version_info.txt.in") as f:
    version_info = f.read()
version_info = version_info.replace("{VERSION}", version).replace(
    "{VERSION_TUPLE}", version_str
)
with open("version_info.txt", "w") as f:
    f.write(version_info)
print(version_info)

datas = []
for pkg in GAM_VER_LIBS:
    datas += copy_metadata(pkg, recursive=True)
datas += [('gam/cbcm-v1.1beta1.json', '.')]
datas += [('gam/contactdelegation-v1.json', '.')]
datas += [('gam/datastudio-v1.json', '.')]
datas += [('gam/meet-v2beta.json', '.')]
datas += [('gam/serviceaccountlookup-v1.json', '.')]
datas += [('cacerts.pem', '.')]
hiddenimports = [
     'gam.gamlib.yubikey',
     ]

excludes = [
    'pkg_resources',
]

runtime_hooks = []
a = Analysis(
    ['gam/__main__.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
    )
#print(f"datas from analysis:\n{a.datas}")
for d in a.datas:
    if 'pyconfig' in d[0]:
        a.datas.remove(d)
        break
#print(f"datas after pyconfig cleanup:\n{a.datas}")
pyz = PYZ(a.pure,
          a.zipped_data,
          cipher=None)
# requires Python 3.10+ but no one should be compiling
# GAM with older versions anyway
target_arch = None
codesign_identity = None
entitlements_file = None
manifest = None
version = 'version_info.txt'
match platform:
    case "darwin":
        if getenv('arch') == 'universal2':
            target_arch = "universal2"

        codesign_identity = getenv('codesign_identity')
        if codesign_identity:
            entitlements_file = '../.github/actions/entitlements.plist'
        strip = True
    case "win32":
        target_arch = None
        strip = False
        manifest = 'gam.exe.manifest'
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
if getenv('PYINSTALLER_BUILD_ONEDIR') == 'yes':
    # Build one directory
    exe = EXE(
              pyz,
              a.scripts,
              [],
              exclude_binaries=True,
              name=name,
              debug=debug,
              bootloader_ignore_signals=bootloader_ignore_signals,
              strip=strip,
              manifest=manifest,
              upx=upx,
              console=console,
              # put most everyting under a lib/ subfolder
              contents_directory='lib',
              disable_windowed_traceback=disable_windowed_traceback,
              argv_emulation=argv_emulation,
              target_arch=target_arch,
              codesign_identity=codesign_identity,
              entitlements_file=entitlements_file,
              version=version,
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
else:
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
              manifest=manifest,
              strip=strip,
              upx=upx,
              console=console,
              disable_windowed_traceback=disable_windowed_traceback,
              argv_emulation=argv_emulation,
              target_arch=target_arch,
              codesign_identity=codesign_identity,
              entitlements_file=entitlements_file,
              version=version,
              )

