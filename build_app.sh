#!/bin/bash

# Build script for NDI Shure Monitor macOS Application

echo "Building NDI Shure Monitor..."

# Ensure PyInstaller is installed
if ! venv/bin/pip show pyinstaller > /dev/null 2>&1; then
    echo "Installing PyInstaller..."
    venv/bin/pip install pyinstaller
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Build the application
echo "Running PyInstaller..."
venv/bin/pyinstaller NDI_Shure_Monitor.spec

# Check if build was successful
if [ -d "dist/NDI Shure Monitor.app" ]; then
    echo ""
    echo "✓ Build successful!"
    echo "Application created at: dist/NDI Shure Monitor.app"
    echo ""
    echo "You can now:"
    echo "  1. Run it directly: open 'dist/NDI Shure Monitor.app'"
    echo "  2. Move it to /Applications"
    echo ""
    echo "Note: The config.json file will be created in the app's directory on first run."
else
    echo ""
    echo "✗ Build failed. Check the output above for errors."
    exit 1
fi
