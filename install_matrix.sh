#!/bin/bash

# Taken directly from MLB scoreboard project
# https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard/blob/master/install.sh
echo "Running rgbmatrix installation..."
sudo apt-get install -y make
mkdir submodules
cd submodules || exit
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git matrix
cd matrix || exit
git pull
make build-python PYTHON="$PYTHON"
sudo make install-python PYTHON="$PYTHON"
cd ../.. || exit

echo "RGBMatrix installation complete"
