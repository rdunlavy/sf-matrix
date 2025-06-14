"""
Dynamic matrix module imports
Handles importing the correct RGB matrix library based on runtime mode
"""

import sys
import os

def is_emulator_mode():
    """Detect if emulator mode is requested from command line"""
    return '--led-emulator' in sys.argv

# Auto-detect mode and import the correct modules
if is_emulator_mode():
    try:
        from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions, graphics
        print("Matrix modules: Using emulator mode")
    except ImportError as e:
        print(f"ERROR: RGBMatrixEmulator not found: {e}")
        sys.exit(1)
else:
    try:
        # First try system-installed rgbmatrix
        from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
        print("Matrix modules: Using real hardware mode (system)")
    except ImportError:
        try:
            # Try local build in submodules
            matrix_path = os.path.join(os.path.dirname(__file__), '../../submodules/matrix/bindings/python')
            if matrix_path not in sys.path:
                sys.path.insert(0, matrix_path)
            from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
            print("Matrix modules: Using real hardware mode (local build)")
        except ImportError as e:
            print(f"ERROR: rgbmatrix module not found: {e}")
            
            # Check if matrix source exists but isn't built
            matrix_source_path = os.path.join(os.path.dirname(__file__), '../../submodules/matrix/bindings/python/rgbmatrix')
            if os.path.exists(matrix_source_path) and os.path.exists(os.path.join(matrix_source_path, 'core.pyx')):
                print("Matrix source found but not built. Run: ./install_matrix.sh")
            else:
                print("Matrix source not found. Run: ./install_matrix.sh")
            
            print("Install the matrix library or use --led-emulator")
            # Fall back to emulator if real hardware not available
            try:
                from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions, graphics
                print("Matrix modules: Falling back to emulator mode")
            except ImportError:
                print("ERROR: Neither rgbmatrix nor RGBMatrixEmulator could be imported")
                sys.exit(1)