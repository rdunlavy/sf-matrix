# SF Matrix Display

A San Francisco-focused LED matrix display system that cycles through live data sources including sports scores, transit information, bike share availability, weather, and news headlines. Designed for 64x32 RGB LED panels and Raspberry Pi.

## Features

- **🏀 Sports Scores** - Live NBA/NFL games with team logos, scores, and betting lines
- **🚌 Transit Info** - Real-time SFMTA bus arrival predictions
- **🚲 Bike Share** - Bay Wheels station availability 
- **🌤️ Weather** - Current conditions with temperature and precipitation
- **📰 News Headlines** - Scrolling RSS feeds from multiple sources
- **⚙️ Modular Design** - Easy to add new data sources
- **🔄 Auto-Cycling** - Intelligent display timing based on content
- **🎨 Visual Polish** - Team logos, weather icons, smooth scrolling

## Hardware Requirements

### For Raspberry Pi (Production)
- Raspberry Pi 3B+ or 4B recommended
- 64x32 RGB LED matrix panel (HUB75 interface)
- 5V power supply (4A+ recommended)
- GPIO ribbon cable or HAT adapter
- MicroSD card (16GB+)

### For Development
- Any computer with Python 3.8+
- Uses built-in RGB matrix emulator for testing

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/sf-matrix.git
cd sf-matrix
```

### 2. Set Up Python Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Settings
```bash
cp config.example.json config.json
# Edit config.json with your personal settings:
# - Location coordinates for weather
# - Transit addresses for bus info  
# - Bike share stations
# - Favorite sports teams
# - News sources
```

### 4. Install Matrix Library (Raspberry Pi Only)
```bash
chmod +x ./install_matrix.sh
./install_matrix.sh
```

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
    },
    "leagues": ["NBA", "NFL"]
  },
  "transit": {
    "target_addresses": [
      "1225 Bay St, San Francisco, CA",
      "Union Square, San Francisco, CA"
    ]
  }
  // ... more settings
}
```

### Key Configuration Options:
- **Sports Leagues**: Choose from NBA, NFL, WNBA, NHL, MLB
- **News Sources**: Add/remove RSS feeds
- **Refresh Rates**: How often to fetch new data
- **Display Timing**: How long each module shows

## Usage

### Development Mode (With Emulator)
```bash
python main.py --led-emulator
```
Opens a web browser showing the matrix display at http://localhost:8888

### Production Mode (Raspberry Pi)
```bash
python main.py
```

### Additional Options
```bash
# Specify matrix dimensions
python main.py --led-cols=64 --led-rows=32

# Set brightness (1-100)
python main.py --led-brightness=75

# Show help
python main.py --help
```

## Raspberry Pi Setup

### 1. Install Raspberry Pi OS
Use Raspberry Pi Imager to install Raspberry Pi OS Lite (64-bit recommended)

### 2. Enable SPI and Configure
```bash
sudo raspi-config
# Navigate to: Interface Options > SPI > Enable
```

### 3. Wire the Matrix
Connect your 64x32 LED panel to the Raspberry Pi GPIO pins. See [wiring guide](submodules/matrix/wiring.md) for details.

### 4. Install Dependencies
```bash
sudo apt update
sudo apt install python3-pip python3-venv git
```

### 5. Clone and Setup Project
```bash
git clone https://github.com/yourusername/sf-matrix.git
cd sf-matrix
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./install_matrix.sh
```

### 6. Configure and Test
```bash
cp config.example.json config.json
# Edit config.json with your settings
python main.py  # Test the display
```

### 7. Run as Service (Auto-start)
```bash
# Install systemd service
sudo cp matrix.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable matrix.service
sudo systemctl start matrix.service

# Check status
sudo systemctl status matrix.service
```

## Project Structure

```
sf-matrix/
├── src/
│   ├── data_sources/          # Display modules
│   │   ├── espn.py           # Sports scores
│   │   ├── news.py           # RSS news feeds  
│   │   ├── weather.py        # Weather data
│   │   ├── sfmta.py          # Transit info
│   │   └── bay_wheels.py     # Bike share
│   ├── display/              # Display system
│   │   ├── base.py           # Module interface
│   │   └── controller.py     # Main controller
│   └── utils/                # Utilities
│       ├── config.py         # Configuration loader
│       └── logger.py         # Logging system
├── config.example.json       # Configuration template
├── main.py                   # Entry point
├── requirements.txt          # Python dependencies
└── RGBMatrixEmulator/        # Development emulator
```

## Development

### Adding New Data Sources

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
    
    def get_display_duration(self):
        return 20  # seconds
```

2. Register in `main.py`:
```python
controller.add_module(MyModule())
```

### Testing
```bash
# Run with emulator for development
python main.py --led-emulator

# View logs
tail -f matrix_display.log
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Test with the emulator
4. Submit a pull request

## Troubleshooting

### Common Issues

**Emulator not opening**: Check if port 8888 is available
```bash
python main.py --led-emulator --led-emulator-port=8889
```

**API errors**: Check your internet connection and API rate limits

**Matrix not lighting up (Pi)**: 
- Verify wiring connections
- Check power supply (5V, 4A+)
- Ensure SPI is enabled

**Permission errors (Pi)**:
```bash
sudo python main.py
```

### Logs
All modules log activity to `matrix_display.log`:
```bash
tail -f matrix_display.log
```

## Hardware Recommendations

### LED Panels
- **Adafruit 64x32 RGB LED Matrix** - High quality, good documentation
- **Any HUB75 compatible panel** - Standard interface

### Power Supply
- **5V 4A minimum** for single 64x32 panel
- **5V 8A+** for multiple panels or high brightness

### Raspberry Pi Accessories
- **Quality MicroSD card** - SanDisk Ultra/Extreme recommended
- **Adequate cooling** - Heat sinks or fan for continuous operation
- **Reliable power supply** - Official Pi power supply recommended

## API Data Sources

- **ESPN API** - Sports scores and schedules
- **Open-Meteo** - Weather data (free, no API key required)
- **SFMTA API** - San Francisco transit predictions
- **Bay Wheels API** - Bike share station data
- **RSS Feeds** - News headlines from configurable sources

## License

This project is open source. See `docs/LICENSE` for details.

## Acknowledgments

- [rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix) - Excellent LED matrix library
- RGB Matrix Emulator for development testing
- San Francisco Open Data for transit APIs