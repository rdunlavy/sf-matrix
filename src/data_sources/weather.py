import openmeteo_requests
import requests_cache
import time
import os
from retry_requests import retry
from typing import Optional, Dict, Any
from src.display import DisplayModule
from src.utils.logger import get_logger, log_network_error
from src.utils.matrix_import import graphics

from src.utils.config import WEATHER_LATITUDE, WEATHER_LONGITUDE, REFRESH_RATES


class WeatherModule(DisplayModule):
    def __init__(self):
        super().__init__()
        
        # Configuration from config.py
        self.REFRESH_RATE_SECONDS = REFRESH_RATES["weather"]
        self.SF_LATITUDE = WEATHER_LATITUDE
        self.SF_LONGITUDE = WEATHER_LONGITUDE
        
        # Setup the Open-Meteo API client with cache and retry on error
        cache_session = requests_cache.CachedSession(".weather_cache", expire_after=3600)
        retry_session = retry(cache_session, retries=3, backoff_factor=0.2)
        self.openmeteo = openmeteo_requests.Client(session=retry_session)
        
        # State management
        self.weather_data = None
        self.last_fetch_time = 0
        self.logger = get_logger('weather')
        
        # Load fonts
        self.font = graphics.Font()
        font_path = os.path.join(
            os.path.dirname(__file__), "../../submodules/matrix/fonts/4x6.bdf"
        )
        self.font.LoadFont(font_path)
        
        # Weather icons (8x8 bitmaps)
        self.weather_icons = {
            'sunny': [
                [0, 0, 0, 1, 1, 0, 0, 0],
                [0, 1, 0, 1, 1, 0, 1, 0],
                [0, 0, 1, 1, 1, 1, 0, 0],
                [1, 1, 1, 1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1, 1, 1, 1],
                [0, 0, 1, 1, 1, 1, 0, 0],
                [0, 1, 0, 1, 1, 0, 1, 0],
                [0, 0, 0, 1, 1, 0, 0, 0]
            ],
            'cloudy': [
                [0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, 1, 1, 0, 0, 0],
                [0, 1, 1, 1, 1, 1, 0, 0],
                [1, 1, 1, 1, 1, 1, 1, 0],
                [1, 1, 1, 1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1, 1, 1, 1],
                [0, 1, 1, 1, 1, 1, 1, 0],
                [0, 0, 0, 0, 0, 0, 0, 0]
            ],
            'rainy': [
                [0, 0, 1, 1, 1, 0, 0, 0],
                [0, 1, 1, 1, 1, 1, 0, 0],
                [1, 1, 1, 1, 1, 1, 1, 0],
                [1, 1, 1, 1, 1, 1, 1, 1],
                [0, 1, 0, 1, 0, 1, 0, 1],
                [1, 0, 1, 0, 1, 0, 1, 0],
                [0, 1, 0, 1, 0, 1, 0, 1],
                [1, 0, 1, 0, 1, 0, 1, 0]
            ],
            'night': [
                [0, 0, 0, 1, 1, 1, 0, 0],
                [0, 0, 1, 1, 1, 1, 1, 0],
                [0, 1, 1, 1, 1, 1, 1, 0],
                [1, 1, 1, 1, 1, 1, 0, 0],
                [1, 1, 1, 1, 1, 0, 0, 1],
                [1, 1, 1, 1, 0, 0, 0, 0],
                [0, 1, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 1, 0, 0]
            ]
        }

    def fetch_weather_data(self) -> Optional[Dict[str, Any]]:
        """Fetch weather data from Open-Meteo API"""
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": self.SF_LATITUDE,
                "longitude": self.SF_LONGITUDE,
                "hourly": ["temperature_2m", "precipitation_probability", "rain"],
                "daily": "uv_index_max",
                "timezone": "America/Los_Angeles",
                "forecast_days": 1
            }
            
            responses = self.openmeteo.weather_api(url, params=params)
            response = responses[0]
            
            # Get current hour data
            hourly = response.Hourly()
            current_hour_index = 0  # Current hour
            
            # Extract current conditions
            current_temp_c = hourly.Variables(0).ValuesAsNumpy()[current_hour_index]
            current_precip_prob = hourly.Variables(1).ValuesAsNumpy()[current_hour_index]
            current_rain = hourly.Variables(2).ValuesAsNumpy()[current_hour_index]
            
            # Get next hour temperature
            next_temp_c = None
            if len(hourly.Variables(0).ValuesAsNumpy()) > 1:
                next_temp_c = hourly.Variables(0).ValuesAsNumpy()[1]
            
            # Get UV index
            daily = response.Daily()
            uv_index = daily.Variables(0).ValuesAsNumpy()[0]
            
            # Convert Celsius to Fahrenheit
            current_temp_f = int(current_temp_c * 9/5 + 32)
            next_temp_f = int(next_temp_c * 9/5 + 32) if next_temp_c else None
            
            weather_data = {
                'current_temp_f': current_temp_f,
                'precipitation_prob': int(current_precip_prob),
                'rain_mm': float(current_rain),
                'uv_index': int(uv_index),
                'next_temp_f': next_temp_f,
                'fetch_time': time.time()
            }
            
            self.logger.info(f"Updated SF weather: {current_temp_f}°F, {int(current_precip_prob)}% rain, UV {int(uv_index)}")
            return weather_data
            
        except Exception as e:
            log_network_error("api.open-meteo.com", e, "weather")
            return None

    def get_weather_icon_type(self) -> str:
        """Determine which weather icon to display"""
        if not self.weather_data:
            return 'cloudy'
        
        precip_prob = self.weather_data.get('precipitation_prob', 0)
        current_hour = time.localtime().tm_hour
        
        # Check if it's night time (8 PM - 6 AM)
        if current_hour >= 20 or current_hour < 6:
            if precip_prob < 30:
                return 'night'
        
        # Day time weather
        if precip_prob > 50:
            return 'rainy'
        elif precip_prob > 20:
            return 'cloudy'
        else:
            return 'sunny'

    def draw_weather_icon(self, icon_type: str, start_x: int = 56, start_y: int = 1):
        """Draw 8x8 weather icon on the matrix"""
        icon = self.weather_icons.get(icon_type, self.weather_icons['cloudy'])
        
        # Color based on icon type
        if icon_type == 'sunny':
            color = graphics.Color(255, 255, 0)  # Yellow
        elif icon_type == 'rainy':
            color = graphics.Color(100, 150, 255)  # Light blue
        elif icon_type == 'night':
            color = graphics.Color(200, 200, 255)  # Light purple
        else:  # cloudy
            color = graphics.Color(180, 180, 180)  # Gray
        
        # Convert weather icon to PIL Image and use fast SetImage
        from PIL import Image
        
        img_data = []
        for y in range(8):
            for x in range(8):
                if icon[y][x] == 1:
                    img_data.extend([color.red, color.green, color.blue])
                else:
                    img_data.extend([0, 0, 0])  # Transparent (black)
        
        # Create 8x8 RGB image and use fast SetImage
        icon_img = Image.frombytes('RGB', (8, 8), bytes(img_data))
        self.canvas.SetImage(icon_img, start_x, start_y)

    def update_data(self):
        """Fetch and update weather data"""
        current_time = time.time()
        
        # Fetch new data if needed
        if (current_time - self.last_fetch_time > self.REFRESH_RATE_SECONDS or 
            self.weather_data is None):
            new_data = self.fetch_weather_data()
            if new_data:
                self.weather_data = new_data
            self.last_fetch_time = current_time

    def draw_frame(self):
        """Draw the current weather to the canvas"""
        if not self.canvas:
            return

        # Don't clear canvas - let new content overwrite old for better performance
        
        # Colors
        white = graphics.Color(255, 255, 255)
        yellow = graphics.Color(255, 255, 0)
        blue = graphics.Color(100, 150, 255)
        green = graphics.Color(0, 255, 0)
        
        if not self.weather_data:
            # Display error message
            graphics.DrawText(self.canvas, self.font, 8, 16, white, "WEATHER")
            graphics.DrawText(self.canvas, self.font, 4, 24, white, "UNAVAILABLE")
            return
        
        # Draw weather icon
        icon_type = self.get_weather_icon_type()
        self.draw_weather_icon(icon_type)
        
        # Header: "SF Weather"
        graphics.DrawText(self.canvas, self.font, 1, 6, yellow, "SF Weather")
        
        # Current temperature (large display)
        temp_text = f"{self.weather_data['current_temp_f']}°F"
        graphics.DrawText(self.canvas, self.font, 1, 14, white, temp_text)
        
        # Rain probability and UV index
        rain_text = f"Rain: {self.weather_data['precipitation_prob']}%"
        uv_text = f"UV: {self.weather_data['uv_index']}"
        graphics.DrawText(self.canvas, self.font, 1, 22, blue, rain_text)
        graphics.DrawText(self.canvas, self.font, 35, 22, green, uv_text)
        
        # Next hour temperature
        if self.weather_data.get('next_temp_f'):
            next_hour = (time.localtime().tm_hour + 1) % 24
            next_period = "AM" if next_hour < 12 else "PM"
            display_hour = next_hour if next_hour <= 12 else next_hour - 12
            if display_hour == 0:
                display_hour = 12
            
            next_text = f"Next: {self.weather_data['next_temp_f']}°F at {display_hour}{next_period}"
            graphics.DrawText(self.canvas, self.font, 1, 30, white, next_text)

    def update_and_draw(self):
        """Update data and draw to the canvas"""
        self.update_data()
        self.draw_frame()