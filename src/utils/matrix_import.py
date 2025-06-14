"""
Dynamic matrix module imports
Handles importing the correct RGB matrix library based on runtime mode
"""

import sys

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
        from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
        print("Matrix modules: Using real hardware mode")
    except ImportError:
        print("ERROR: rgbmatrix module not found. Install the matrix library or use --led-emulator")
        print("Run: ./install_matrix.sh")
        # Fall back to emulator if real hardware not available
        try:
            from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions, graphics
            print("Matrix modules: Falling back to emulator mode")
        except ImportError:
            print("ERROR: Neither rgbmatrix nor RGBMatrixEmulator could be imported")
            sys.exit(1)