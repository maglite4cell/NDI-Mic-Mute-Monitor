# Building NDI Shure Monitor as a macOS Application

## Overview
I've created the necessary files to package your application as a standalone macOS `.app` bundle using PyInstaller.

## Files Created
- `NDI_Shure_Monitor.spec` - PyInstaller specification file
- `build_app.sh` - Automated build script

## Build Instructions

### 1. Run the Build Script
```bash
./build_app.sh
```

This will:
- Install PyInstaller (if not already installed)
- Clean previous builds
- Package the application with all dependencies
- Create `dist/NDI Shure Monitor.app`

### 2. Run the Application
```bash
open "dist/NDI Shure Monitor.app"
```

Or drag it to your Applications folder and launch from there.

## What Gets Bundled
- All Python dependencies (FastAPI, Pygame, Numpy, etc.)
- NDI library (`NDIlib.cpython-313-darwin.so`)
- NDI SDK dynamic library (`libndi.dylib`)
- All necessary data files

## Configuration
- The `config.json` file will be created in the application's working directory on first run
- To reset configuration, delete the `config.json` file

## Notes
- The app bundle will be approximately 100-200MB due to all the bundled dependencies
- The application runs with a console window (for debugging). To hide it, change `console=True` to `console=False` in the spec file
- The web interface will still be accessible at `http://localhost:8001`

## Troubleshooting

### If NDI library is not found:
Edit `NDI_Shure_Monitor.spec` and update the path to `libndi.dylib` if it's in a different location:
```python
ndi_dylib = '/path/to/your/libndi.dylib'
```

### To rebuild after code changes:
Simply run `./build_app.sh` again - it will clean and rebuild everything.
