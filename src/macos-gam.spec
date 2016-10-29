# -*- mode: python -*-
a = Analysis(['gam.py'],
             hiddenimports=[],
             hookspath=None,
             excludes=['_tkinter'],
             runtime_hooks=None)
for d in a.datas:
    if 'pyconfig' in d[0]:
        a.datas.remove(d)
        break
a.datas += [('httplib2/cacerts.txt', 'httplib2/cacerts.txt', 'DATA')]
a.datas += [('cloudprint-v2.json', 'cloudprint-v2.json', 'DATA')]
a.datas += [('email-settings-v2.json', 'email-settings-v2.json', 'DATA')]
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
