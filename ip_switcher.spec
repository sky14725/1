# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['ip_switcher.py'],
    pathex=[],
    binaries=[],
    datas=[('I:\\\\Users\\\\86157\\\\Desktop\\\\新建文件夹\\\\proxies.txt', '.'), ('I:\\\\Users\\\\86157\\\\Desktop\\\\新建文件夹\\\\background.jpg', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ip_switcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
