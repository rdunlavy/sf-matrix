import requests
import os
import time
from src.display import DisplayModule
from src.utils.logger import get_logger, log_network_error
from src.utils.matrix_import import graphics

from src.utils.config import TARGET_BIKE_STATIONS, STATION_SWITCH_INTERVAL


class BayWheelsModule(DisplayModule):
    def __init__(self):
        super().__init__()
        self.target_stations = TARGET_BIKE_STATIONS
        self.current_data = {}
        self.current_station_index = 0
        self.station_switch_interval = STATION_SWITCH_INTERVAL
        self.last_switch_time = time.time()
        self.logger = get_logger("bay_wheels")
        self.font = graphics.Font()
        font_path = os.path.join(
            os.path.dirname(__file__), "../../submodules/matrix/fonts/4x6.bdf"
        )
        self.font.LoadFont(font_path)

        # Define icons as 9x9 bitmap patterns
        # Wheel icon (regular bike) - circular rim with spokes
        self.wheel_icon = [
            [0, 0, 1, 1, 1, 1, 1, 0, 0],
            [0, 1, 0, 0, 1, 0, 0, 1, 0],
            [1, 0, 0, 0, 1, 0, 0, 0, 1],
            [1, 0, 0, 0, 1, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 1, 0, 0, 0, 1],
            [1, 0, 0, 0, 1, 0, 0, 0, 1],
            [0, 1, 0, 0, 1, 0, 0, 1, 0],
            [0, 0, 1, 1, 1, 1, 1, 0, 0],
        ]

        # Lightning bolt icon (green for old gen ebikes) - classic zigzag pattern
        self.lightning_icon = [
            [0, 0, 1, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 1, 0, 0],
            [1, 1, 1, 1, 1, 1, 0, 0, 0],
            [0, 0, 1, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 1, 0, 0],
        ]

        # Enhanced lightning bolt icon (blue for next gen ebikes) - wider jagged pattern
        self.next_gen_icon = [
            [0, 1, 1, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 1, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 1, 1, 0, 0],
            [1, 1, 1, 1, 1, 1, 1, 0, 0],
            [0, 1, 1, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 1, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 1, 1, 0, 0],
        ]

        # GraphQL query to get Bay Wheels station and bike data
        self.query = """
        query GetSystemSupply($input: SupplyInput) {
          supply(input: $input) {
            stations {
              stationId
              stationName
              location {
                lat
                lng
              }
              bikesAvailable
              bikeDocksAvailable 
              ebikesAvailable
              ebikes {
                rideableName
                batteryStatus {
                  distanceRemaining {
                    value
                    unit
                  }
                }
              }
            }
          }
        }"""

        self.url = "https://account.baywheels.com/bikesharefe-gql"
        self.payload = {
            "operationName": "GetSystemSupply",
            "variables": {"input": {"regionCode": "SFO", "rideablePageLimit": 1000}},
            "query": self.query,
        }

    def _fetch_data(self):
        """Private method to fetch data from Bay Wheels API"""
        try:
            response = requests.post(self.url, json=self.payload)
            response.raise_for_status()
            return response.json()["data"]["supply"]["stations"]
        except requests.RequestException as e:
            log_network_error("bay-wheels.com", e, "bay_wheels")
            return None

    def _get_station_info(self, station):
        """Private method to format station information"""
        count_next_gen = 0
        count_old_gen = 0
        if station["ebikes"]:
            for ebike in station["ebikes"]:
                range_mi = float(ebike["batteryStatus"]["distanceRemaining"]["value"])
                # Next-gen bikes have a 4-digit end number (e.g. "···3632"), older ones have 3.
                # strip out dots and check if the number is 4 digits
                is_next_gen = len(ebike["rideableName"].replace("···", "")) == 4
                if range_mi > 3.0:
                    if is_next_gen:
                        count_next_gen += 1
                    else:
                        count_old_gen += 1

        return {
            "name": station["stationName"],
            "docks_available": station["bikeDocksAvailable"],
            "bikes_available": station["bikesAvailable"],
            "ebikes_available": station["ebikesAvailable"],
            "next_gen_ebikes": count_next_gen,
            "old_gen_ebikes": count_old_gen,
        }

    def _draw_icon(self, icon, x, y, color):
        """Draw a 9x9 icon at the specified position using fast SetImage"""
        # Create PIL Image from icon data
        from PIL import Image
        
        # Convert icon boolean array to RGB image
        img_data = []
        for row in range(9):
            for col in range(9):
                if icon[row][col]:
                    img_data.extend([color.red, color.green, color.blue])
                else:
                    img_data.extend([0, 0, 0])  # Transparent (black)
        
        # Create 9x9 RGB image and use fast SetImage
        icon_img = Image.frombytes('RGB', (9, 9), bytes(img_data))
        self.canvas.SetImage(icon_img, x, y)

    def update_data(self):
        """Fetch and update station data"""
        stations = self._fetch_data()
        if stations:
            self.current_data = {
                station["stationName"]: self._get_station_info(station)
                for station in stations
                if station["stationName"] in self.target_stations
            }

    def draw_frame(self):
        """Draw the current data to the canvas"""
        if not self.current_data:  # Skip if no data available
            return

        # Don't clear canvas - let new content overwrite old for better performance
        text_color = graphics.Color(255, 255, 255)
        wheel_color = graphics.Color(200, 200, 200)  # Gray for regular bikes
        old_ebike_color = graphics.Color(0, 255, 0)  # Green for old ebikes
        next_gen_color = graphics.Color(0, 100, 255)  # Blue for next gen ebikes

        # Check if it's time to switch stations
        current_time = time.time()
        if current_time - self.last_switch_time >= self.station_switch_interval:
            self.current_station_index = (self.current_station_index + 1) % len(
                self.current_data
            )
            self.last_switch_time = current_time

        # Get current station data
        station_names = list(self.current_data.keys())
        if not station_names:
            return

        station_name = station_names[self.current_station_index]
        info = self.current_data[station_name]

        # Draw station name at top
        graphics.DrawText(self.canvas, self.font, 1, 8, text_color, station_name[:15])

        icon_y = 12  # Start icons below station name
        number_y = 23  # Position numbers below 9px icons
        x_pos = 1

        regular_bikes = info["bikes_available"]
        self._draw_icon(self.wheel_icon, x_pos, icon_y, wheel_color)
        graphics.DrawText(
            self.canvas,
            self.font,
            x_pos + 10,
            number_y,
            text_color,
            str(regular_bikes),
        )
        x_pos += 20  # More space to prevent overlap

        # Old generation ebikes (green lightning) - always show
        self._draw_icon(self.lightning_icon, x_pos, icon_y, old_ebike_color)
        graphics.DrawText(
            self.canvas,
            self.font,
            x_pos + 10,
            number_y,
            text_color,
            str(info["old_gen_ebikes"]),
        )
        x_pos += 20

        # Next generation ebikes (blue lightning) - always show
        self._draw_icon(self.next_gen_icon, x_pos, icon_y, next_gen_color)
        graphics.DrawText(
            self.canvas,
            self.font,
            x_pos + 10,
            number_y,
            text_color,
            str(info["next_gen_ebikes"]),
        )

    def needs_continuous_updates(self) -> bool:
        """BayWheels needs continuous updates to cycle through stations"""
        return True

    def update_and_draw(self):
        """Update data and draw to the canvas"""
        self.update_data()
        self.draw_frame()
