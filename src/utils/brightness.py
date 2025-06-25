"""
Dynamic brightness calculation based on time of day and sunrise/sunset data
"""
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from src.utils.logger import get_logger


class BrightnessController:
    def __init__(self, min_brightness: int = 20, max_brightness: int = 100):
        """
        Initialize brightness controller
        
        Args:
            min_brightness: Minimum brightness (nighttime), range 1-100
            max_brightness: Maximum brightness (daytime), range 1-100
        """
        self.min_brightness = max(1, min(min_brightness, 100))
        self.max_brightness = max(1, min(max_brightness, 100))
        self.logger = get_logger('brightness')
        
        # Cache for weather data to avoid frequent lookups
        self._cached_weather_data = None
        self._cache_timestamp = 0
        self._cache_duration = 3600  # 1 hour cache
        
    def calculate_brightness(self, weather_data: Optional[Dict[str, Any]] = None) -> int:
        """
        Calculate brightness based on current time and sunrise/sunset data
        
        Args:
            weather_data: Optional weather data containing sunrise/sunset timestamps
            
        Returns:
            Brightness value between min_brightness and max_brightness
        """
        current_time = time.time()
        current_hour = datetime.now().hour
        
        # If we have weather data with sunrise/sunset, use it
        if (weather_data and 
            'sunrise_timestamp' in weather_data and 'sunset_timestamp' in weather_data and
            weather_data['sunrise_timestamp'] is not None and weather_data['sunset_timestamp'] is not None):
            
            sunrise_ts = weather_data['sunrise_timestamp']
            sunset_ts = weather_data['sunset_timestamp']
            
            # Convert timestamps to hours for easier calculation
            sunrise_hour = datetime.fromtimestamp(sunrise_ts, tz=timezone.utc).hour
            sunset_hour = datetime.fromtimestamp(sunset_ts, tz=timezone.utc).hour
            
            brightness = self._calculate_brightness_with_sun_data(current_hour, sunrise_hour, sunset_hour)
            self.logger.debug(f"Using sun data: sunrise={sunrise_hour}h, sunset={sunset_hour}h, brightness={brightness}%")
            return brightness
        
        # Fallback to time-based calculation (San Francisco averages)
        brightness = self._calculate_brightness_time_based(current_hour)
        self.logger.debug(f"Using time-based calculation: hour={current_hour}, brightness={brightness}%")
        return brightness
    
    def _calculate_brightness_with_sun_data(self, current_hour: int, sunrise_hour: int, sunset_hour: int) -> int:
        """Calculate brightness using actual sunrise/sunset data"""
        
        # Night time (after sunset or before sunrise)
        if current_hour >= sunset_hour or current_hour < sunrise_hour:
            return self.min_brightness
            
        # Day time - create smooth transition
        # Peak brightness at midday
        midday = (sunrise_hour + sunset_hour) / 2
        daylight_duration = sunset_hour - sunrise_hour
        
        if daylight_duration <= 0:
            return self.max_brightness
            
        # Calculate how far we are from midday (0 = midday, 1 = sunrise/sunset)
        distance_from_midday = abs(current_hour - midday) / (daylight_duration / 2)
        distance_from_midday = min(1.0, distance_from_midday)  # Cap at 1.0
        
        # Use cosine curve for smooth transition
        import math
        brightness_factor = math.cos(distance_from_midday * math.pi / 2)
        
        brightness = int(self.min_brightness + (self.max_brightness - self.min_brightness) * brightness_factor)
        return max(self.min_brightness, min(self.max_brightness, brightness))
    
    def _calculate_brightness_time_based(self, current_hour: int) -> int:
        """Fallback time-based brightness calculation"""
        
        # San Francisco typical daylight hours (approximation)
        # Adjust for seasons: winter ~7am-6pm, summer ~6am-8pm
        month = datetime.now().month
        
        if month in [12, 1, 2]:  # Winter
            sunrise_approx, sunset_approx = 7, 18
        elif month in [6, 7, 8]:  # Summer  
            sunrise_approx, sunset_approx = 6, 20
        else:  # Spring/Fall
            sunrise_approx, sunset_approx = 6.5, 19
            
        return self._calculate_brightness_with_sun_data(current_hour, sunrise_approx, sunset_approx)
    
    def set_matrix_brightness(self, matrix, brightness: int) -> bool:
        """
        Set the matrix brightness
        
        Args:
            matrix: The RGBMatrix object
            brightness: Brightness value 1-100
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try brightness property first (newer API)
            if hasattr(matrix, 'brightness'):
                matrix.brightness = brightness
                self.logger.info(f"Set matrix brightness to {brightness}% (property)")
                return True
            # Fall back to SetBrightness method
            elif hasattr(matrix, 'SetBrightness'):
                matrix.SetBrightness(brightness)
                self.logger.info(f"Set matrix brightness to {brightness}% (method)")
                return True
            else:
                self.logger.warning("Matrix object does not support brightness control (emulator mode?)")
                return False
        except Exception as e:
            self.logger.error(f"Failed to set matrix brightness: {e}")
            return False