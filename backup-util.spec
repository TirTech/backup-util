# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['backup_util\\backup_util.py'],
             pathex=['D:\\Projects\\backup-util'],
             binaries=[],
             datas=[('backup_util/icon.ico', 'icon.ico')],
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
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False , icon='backup_util\\icon.ico')
