# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['src\\launch.py'],
             binaries=[],
             datas=[('src/backup_util/icon.ico', '.'),('src/backup_util/ttktheme_custom/', 'backup_util/ttktheme_custom'),('src/backup_util/images/', 'backup_util/images')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Backup Util',
          debug=True,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True , icon='src\\backup_util\\icon.ico')
