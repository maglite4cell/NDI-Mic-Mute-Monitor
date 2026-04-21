#!/bin/bash
set -e

# Ensure we are in the directory where this script lives (Project Root)
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

echo "========================================"
echo "   NDI Python Wrapper Installer Helper"
echo "========================================"
echo "📂 Working in: $PROJECT_ROOT"

# 1. Check for NDI SDK
NDI_SDK="/Library/NDI SDK for Apple"
if [ ! -d "$NDI_SDK" ]; then
    echo "❌ NDI SDK not found at: $NDI_SDK"
    echo "Please download and install 'NDI SDK for macOS' from: https://ndi.video/tools/ndi-sdk/"
    exit 1
else
    echo "✅ NDI SDK found!"
fi

# 2. Setup Environment
export NDI_SDK_DIR="$NDI_SDK"
export SDKROOT=$(xcrun --show-sdk-path)
export MACOSX_DEPLOYMENT_TARGET=10.15
export CFLAGS="-isysroot $SDKROOT"
export CXXFLAGS="-isysroot $SDKROOT"
export CMAKE_ARGS="-DCMAKE_OSX_SYSROOT=$SDKROOT"

echo "Using SDKROOT: $SDKROOT"

# 3. Clean Build
echo "🧹 Cleaning previous builds..."
rm -rf 3rdparty/ndi-python/build
rm -rf 3rdparty/ndi-python/dist
rm -rf 3rdparty/ndi-python/*.egg-info

# 4. Install
echo "🚀 Building and Installing..."
# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ venv directory not found in $PROJECT_ROOT"
    exit 1
fi

source venv/bin/activate
cd 3rdparty/ndi-python
pip install . --no-build-isolation

echo ""
echo "========================================"
echo "✅ Success! NDI Python installed."
echo "You can now run: venv/bin/python main.py"
echo "========================================"
