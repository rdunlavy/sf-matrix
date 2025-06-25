#!/bin/bash
# Run with sudo for proper hardware access
# Detect uv path before switching to sudo
UV_PATH=$(which uv)
if [ -z "$UV_PATH" ]; then
    echo "Error: uv not found in PATH"
    exit 1
fi

echo "Using uv at: $UV_PATH"
sudo "$UV_PATH" run python main.py --led-rows 32 --led-cols 64 --led-gpio-mapping adafruit-hat --led-slowdown-gpio 3