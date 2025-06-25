# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a San Francisco-focused LED matrix display system that cycles through different data sources (sports scores, transit info, bike share availability) on an RGB LED matrix. The system is designed to run on a Raspberry Pi and uses a modular architecture where display modules are automatically cycled every 10 seconds.

## Setup

### Initial Configuration

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Copy configuration template:**
   ```bash
   cp config.example.json config.json
   ```

3. **Edit configuration with your personal settings:**
   ```bash
   # Edit config.json with your:
   # - Location coordinates (for weather)
   # - Transit addresses (for SFMTA bus info)
   # - Bike share stations (for Bay Wheels)
   # - Favorite sports teams (for ESPN)
   # - News sources and refresh rates
   ```

   The `config.json` file is ignored by git to protect your personal information.

## Commands

### Running the System

```bash
# Development (with emulator)
uv run python main.py --led-emulator

# Production (on Raspberry Pi with actual matrix)
uv run python main.py

# Install matrix library for Raspberry Pi
./install_matrix.sh
```

### Service Management (Production)

```bash
# Install as systemd service
sudo cp matrix.service /etc/systemd/system/
sudo systemctl enable matrix.service
sudo systemctl start matrix.service
```

## Architecture

### Committing

YOU MUST NOT mention claude in commit messages

### Core Pattern: Plugin-Based Display Controller

- **DisplayController** (`src/display/controller.py`): Central orchestrator that cycles through modules every 10 seconds
- **DisplayModule** (`src/display/base.py`): Abstract base class - all display modules must implement `update_data()` and `draw_frame()`
- **Data Sources** (`src/data_sources/`): Modular data fetchers (ESPN, Bay Wheels, SFMTA, etc.)

### Adding New Display Modules

1. Create new class inheriting from `DisplayModule` in `src/data_sources/`
2. Implement `update_data()` (fetch/process data) and `draw_frame()` (render to canvas)
3. Add to `main.py` modules list
4. Module will automatically be included in the 10-second rotation

### Data Flow

```
main.py → DisplayController → [ESPN, BayWheels, ...] → LED Matrix
                ↓
    10-second cycle: update_data() → draw_frame() → SwapOnVSync()
```

## Active Data Sources

### ESPN Sports (`src/data_sources/espn.py`)

- Shows NBA/NFL scores and schedules
- Downloads team logos as images
- API: `site.api.espn.com`

### Bay Wheels Bike Share (`src/data_sources/bay_wheels.py`)

- Tracks bike availability at specific SF stations
- GraphQL API with e-bike battery filtering
- Currently commented out in main.py

### SFMTA Transit (`src/data_sources/sfmta.py`)

- Bus arrival predictions using SFMTA + UMO Transit APIs
- Not yet integrated into main display

## Configuration

### Matrix Hardware Settings

- Default: 32x64 pixels, configurable via command line
- Font: `7x13.bdf` for text rendering
- Brightness and other parameters via `--led-*` flags

### Emulator Settings

- Configure via `emulator_config.json`
- Provides visual feedback during development
- Same interface as real hardware

## Key Files

- `main.py`: Entry point and module registration
- `samplebase.py`: Hardware abstraction layer
- `pyproject.toml`: Python dependencies and project configuration
