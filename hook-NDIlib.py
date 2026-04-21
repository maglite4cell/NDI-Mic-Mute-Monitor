import os
import sys

# Runtime hook for NDI library path configuration
# This ensures the NDI library can find its dependencies when running as a bundled app

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running in a PyInstaller bundle
    bundle_dir = sys._MEIPASS
    
    # Add the NDIlib directory to the library search path
    ndi_lib_dir = os.path.join(bundle_dir, 'NDIlib')
    
    # Set environment variable for dynamic library loading
    if sys.platform == 'darwin':
        # macOS: Set DYLD_LIBRARY_PATH
        current_path = os.environ.get('DYLD_LIBRARY_PATH', '')
        if current_path:
            os.environ['DYLD_LIBRARY_PATH'] = f"{ndi_lib_dir}:{current_path}"
        else:
            os.environ['DYLD_LIBRARY_PATH'] = ndi_lib_dir
