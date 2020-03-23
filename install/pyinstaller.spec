# -*- mode: python -*-

import platform
p = platform.system()

version = "0.1.0"

a = Analysis(
    ['scripts/manualbox'],
    pathex=['.'],
    binaries=None,
    datas=[
        ("../manualbox/assets/mainicon.png", "manualbox")
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None)

pyz = PYZ(
    a.pure, a.zipped_data,
    cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='ManualBoxTool',
    debug=False,
    strip=False,
    upx=True,
    console=False)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='manualbox')

if p == 'Darwin':
    app = BUNDLE(
        coll,
        name='ManualBox.app',
        icon=None,
        bundle_identifier='in.kushaldas.manualbox',
        info_plist={
            'CFBundleShortVersionString': version,
            'NSHighResolutionCapable': 'True'
        }
    )