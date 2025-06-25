# SF Matrix Display

A San Francisco-focused LED matrix display system that cycles through live data sources including sports scores, transit information, bike share availability, weather, and news headlines.

## Features

- **Sports Scores** - Live NBA/NFL games with team logos and scores
- **Transit Info** - Real-time SFMTA bus arrival predictions
- **Bike Share** - Bay Wheels station availability 
- **Weather** - Current conditions with temperature
- **News Headlines** - Scrolling RSS feeds
- **Auto-Cycling** - Intelligent display timing based on content

## Prerequisites

This project uses [uv](https://github.com/astral-sh/uv) for fast Python dependency management. Install it first:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

## Quick Start

### Development (Any Computer)
```bash
git clone https://github.com/yourusername/sf-matrix.git
cd sf-matrix
uv sync
cp config.example.json config.json
# Edit config.json with your settings
uv run python main.py --led-emulator
```

### Raspberry Pi Setup

**1. Install OS and Dependencies**
```bash
# Install Raspberry Pi OS Lite, then:
sudo apt update && sudo apt install python3-pip git python3-dev cython3 -y
curl -LsSf https://astral.sh/uv/install.sh | sh
sudo raspi-config  # Enable SPI under Interface Options
```

**2. Install Project**
```bash
git clone https://github.com/yourusername/sf-matrix.git
cd sf-matrix
uv sync
./install_matrix.sh
cp config.example.json config.json
# Edit config.json with your settings
```

**3. Test Display**
```bash
uv run python main.py  # Test the display works
```

**4. Auto-Start on Boot**
```bash
# Install as system service
sudo cp matrix.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable matrix.service
sudo systemctl start matrix.service

# Check status
sudo systemctl status matrix.service
```

The display will now automatically start when the Raspberry Pi boots up. To disable auto-start: `sudo systemctl disable matrix.service`

## Hardware Requirements

- Raspberry Pi 3B+ or 4B
- 64x32 RGB LED matrix panel (HUB75 interface)
- 5V 4A+ power supply
- GPIO ribbon cable or HAT adapter
- MicroSD card (16GB+)

## Configuration

Edit `config.json` to customize your display:

```json
{
  "location": {
    "timezone": "America/Los_Angeles",
    "weather_latitude": 37.7749,
    "weather_longitude": -122.4194
  },
  "sports": {
    "favorite_teams": {
      "NBA": ["Warriors"],
      "NFL": ["49ers"] 
    }
  },
  "transit": {
    "target_addresses": [
      "Union Square, San Francisco, CA"
    ]
  }
}
```

## Usage

```bash
# Development mode (with emulator)
uv run python main.py --led-emulator

# Production mode (Raspberry Pi)
uv run python main.py

# Options
uv run python main.py --led-brightness=75 --led-cols=64 --led-rows=32
```

## Adding New Data Sources

1. Create a new module in `src/data_sources/`:
```python
from src.display import DisplayModule

class MyModule(DisplayModule):
    def update_data(self):
        # Fetch your data
        pass
    
    def draw_frame(self):
        # Draw to self.canvas
        pass
```

2. Register in `main.py`:
```python
controller.add_module(MyModule())
```

## Troubleshooting

**Matrix not lighting up**: Check wiring, power supply (5V 4A+), and SPI enabled

**Permission errors**: Run with `sudo uv run python main.py`

**API errors**: Check internet connection and `tail -f matrix_display.log`

**Service issues**: 
```bash
sudo systemctl status matrix.service
sudo journalctl -u matrix.service -f
```

## API Data Sources

- **ESPN API** - Sports scores and schedules
- **Open-Meteo** - Weather data (no API key required)
- **SFMTA API** - San Francisco transit predictions
- **Bay Wheels API** - Bike share station data
- **RSS Feeds** - News headlines