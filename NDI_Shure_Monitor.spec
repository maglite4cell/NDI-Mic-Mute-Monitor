# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

# Collect NDI library dynamically
import site
import glob

ndi_binaries = []
site_packages = site.getsitepackages()

# Try to find the NDIlib shared library in site-packages
for sp in site_packages:
    # Windows: .pyd or .dll, MacOS: .so or .dylib, Linux: .so
    files = glob.glob(os.path.join(sp, 'NDIlib*')) + glob.glob(os.path.join(sp, 'ndi_python*'))
    for f in files:
        if os.path.isfile(f) and f.endswith(('.so', '.dylib', '.pyd', '.dll')):
            ndi_binaries.append((f, 'NDIlib'))

# Collect global libndi if exists (Mostly for macOS / Linux)
if sys.platform == 'darwin':
    ndi_dylib = '/usr/local/lib/libndi.dylib'
    if os.path.exists(ndi_dylib):
        ndi_binaries.append((ndi_dylib, 'NDIlib'))
elif sys.platform == 'win32':
    # Windows usually expects Processing.NDI.Lib.x64.dll in the path or bundled
    pass

# Collect numpy dynamic libraries
numpy_libs = collect_dynamic_libs('numpy')
ndi_binaries.extend(numpy_libs)

# Collect pygame data
pygame_datas = collect_data_files('pygame')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=ndi_binaries,
    datas=pygame_datas,
    hiddenimports=[
        'pygame',
        'numpy',
        'numpy._core',
        'numpy._core._multiarray_umath',
        'numpy.core._multiarray_umath',
        'NDIlib',
        'fastapi',
        'uvicorn',
        'pydantic',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['hook-NDIlib.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NDI Shure Monitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NDI Shure Monitor',
)

app = BUNDLE(
    coll,
    name='NDI Shure Monitor.app',
    icon=None,
    bundle_identifier='com.shure.ndimonitor',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'LSBackgroundOnly': 'False',
    },
)
