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

# ndi-python wheels bundle libndi.dylib INSIDE the NDIlib package subdirectory.
# We must look inside NDIlib/ rather than just at the top level of site-packages,
# because glob('NDIlib*') finds the directory, not the files within it.
for sp in site_packages:
    ndi_pkg_dir = os.path.join(sp, 'NDIlib')
    if os.path.isdir(ndi_pkg_dir):
        for ext in ('*.so', '*.dylib', '*.pyd', '*.dll'):
            for f in glob.glob(os.path.join(ndi_pkg_dir, ext)):
                if os.path.isfile(f):
                    ndi_binaries.append((f, 'NDIlib'))
    # Also check top-level site-packages for any direct NDIlib/ndi_python files
    for pattern in ('NDIlib*.so', 'NDIlib*.dylib', 'ndi_python*.so', 'ndi_python*.pyd'):
        for f in glob.glob(os.path.join(sp, pattern)):
            if os.path.isfile(f):
                ndi_binaries.append((f, 'NDIlib'))

# Fallback: system-level libndi installed by the NDI SDK (macOS/Linux)
if sys.platform == 'darwin':
    ndi_dylib = '/usr/local/lib/libndi.dylib'
    if os.path.exists(ndi_dylib):
        ndi_binaries.append((ndi_dylib, 'NDIlib'))
elif sys.platform == 'win32':
    for candidate in [
        r'C:\Program Files\NDI\NDI 6 Runtime\Processing.NDI.Lib.x64.dll',
        r'C:\Program Files\NDI\NDI 5 Runtime\Processing.NDI.Lib.x64.dll',
    ]:
        if os.path.exists(candidate):
            ndi_binaries.append((candidate, '.'))
            break

print(f"[spec] NDI binaries found: {ndi_binaries}")

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
        'numpy.core.multiarray',
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
    icon='icon.ico',
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
    icon='icon.icns',
    bundle_identifier='com.shure.ndimonitor',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'LSBackgroundOnly': 'False',
    },
)
