#!/bin/bash

# RGB Matrix installation script for Raspberry Pi
echo "Running rgbmatrix installation..."

# Detect Python executable - prefer current Python if in venv
if [ -z "$PYTHON" ]; then
    if [ -n "$VIRTUAL_ENV" ]; then
        # Use the Python from the virtual environment
        PYTHON="$(which python3)"
        echo "Detected virtual environment: $VIRTUAL_ENV"
    elif command -v python3 &> /dev/null; then
        PYTHON="python3"
    elif command -v python &> /dev/null; then
        PYTHON="python"
    else
        echo "ERROR: No Python executable found"
        exit 1
    fi
fi

echo "Using Python: $PYTHON"
echo "Python version: $($PYTHON --version)"
echo "Python path: $(which "$PYTHON")"

# Install system dependencies
sudo apt-get update
sudo apt-get install -y make build-essential python3-dev cython3

# Create submodules directory
mkdir -p submodules
cd submodules || exit

# Clone or update matrix library
if [ ! -d "matrix" ]; then
    git clone https://github.com/hzeller/rpi-rgb-led-matrix.git matrix
else
    echo "Matrix directory exists, updating..."
    cd matrix && git pull && cd ..
fi

cd matrix || exit

# Clean previous builds
make clean

# Build Python bindings
echo "Building Python bindings..."

if make build-python PYTHON="$PYTHON"; then
    echo "Build successful, installing..."
    
    if sudo make install-python PYTHON="$PYTHON"; then
        echo "✓ RGBMatrix installation completed successfully"
    else
        echo "✗ Installation failed"
        exit 1
    fi
else
    echo "✗ Build failed"
    exit 1
fi

cd ../.. || exit
