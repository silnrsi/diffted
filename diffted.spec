# -*- mode: python -*-

block_cipher = None

# options = [ ('v', None, 'OPTION') ]

a = Analysis(['scripts\\diffted'],
             pathex=['lib'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

bins = a.binaries
if sys.platform == 'win32':
    for d in ('vcruntime140', ):
        bins += [(d + '.dll', 'bins/' + d + '.dll', 'BINARY')]

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
#          options,
          bins,
          a.zipfiles,
          a.datas,
          [],
          name='diffted',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False )
