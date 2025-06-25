"""
Configuration loader for SF Matrix Display
Loads settings from config.json with fallback defaults
"""

import json
import os
from typing import Dict, Any, List

# Path to config file
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../../config.json")

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json with fallback defaults"""
    
    # Default configuration
    defaults = {
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
                "Market St & 4th St, San Francisco, CA",
                "Union Square, San Francisco, CA"
            ]
        },
        "bike_share": {
            "target_stations": [
                "Market St at 4th St",
                "Powell St BART Station (Market St at 4th St)"
            ]
        },
        "news": {
            "sources": {
                "NYT": {
                    "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
                    "favicon_url": "https://www.nytimes.com/favicon.ico",
                    "name": "NY Times"
                }
            }
        },
        "display": {
            "refresh_rates": {
                "espn": 30,
                "weather": 1800,
                "news": 300,
                "sfmta": 30,
                "bay_wheels": 30
            },
            "timing": {
                "display_time_per_module": 20,
                "game_display_duration": 3,
                "station_switch_interval": 5
            },
            "brightness": {
                "auto_brightness": True,
                "min_brightness": 20,
                "max_brightness": 100,
                "update_interval": 300
            }
        }
    }
    
    # Try to load from config.json
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Config file {CONFIG_FILE} not found, using defaults")
        return defaults
    except json.JSONDecodeError as e:
        print(f"Error parsing config file: {e}, using defaults")
        return defaults

# Load configuration once when module is imported
config = load_config()

# Legacy compatibility - expose individual settings for existing code
TIMEZONE = config["location"]["timezone"]
WEATHER_LATITUDE = config["location"]["weather_latitude"]
WEATHER_LONGITUDE = config["location"]["weather_longitude"]

FAVORITE_TEAMS = config["sports"]["favorite_teams"]
SPORTS_LEAGUES = config["sports"]["leagues"]

TARGET_TRANSIT_ADDRESSES = config["transit"]["target_addresses"]
TARGET_BIKE_STATIONS = config["bike_share"]["target_stations"]

NEWS_SOURCES = config["news"]["sources"]

REFRESH_RATES = config["display"]["refresh_rates"]
DISPLAY_TIME_PER_MODULE = config["display"]["timing"]["display_time_per_module"]
GAME_DISPLAY_DURATION = config["display"]["timing"]["game_display_duration"]
STATION_SWITCH_INTERVAL = config["display"]["timing"]["station_switch_interval"]

# Brightness settings
BRIGHTNESS_CONFIG = config["display"].get("brightness", {
    "auto_brightness": True,
    "min_brightness": 20,
    "max_brightness": 100,
    "update_interval": 300
})