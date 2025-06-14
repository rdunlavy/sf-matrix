import requests
import time
import os
from urllib.parse import quote
from typing import List, Dict, Optional, Tuple
from location_utils import get_bounding_box
from src.display import DisplayModule
from src.utils.logger import get_logger, log_network_error
from src.utils.matrix_import import graphics

from src.utils.config import TARGET_TRANSIT_ADDRESSES, REFRESH_RATES


class SFMTAModule(DisplayModule):
    def __init__(self):
        super().__init__()

        # Configuration from config.py
        self.REFRESH_RATE_SECONDS = REFRESH_RATES["sfmta"]
        self.STOP_DISPLAY_DURATION_SECONDS = 5  # How long to show each stop
        self.target_addresses = TARGET_TRANSIT_ADDRESSES

        # State management
        self.current_data = {}  # {address: {stops: [...], predictions: {...}}}
        self.current_address_index = 0
        self.last_fetch_time = 0
        self.last_display_time = time.time()
        self.processed_stops = []  # Currently displayed stops for current address
        self.current_stop_index = 0
        self.logger = get_logger('sfmta')

        # Load fonts
        self.font = graphics.Font()
        font_path = os.path.join(
            os.path.dirname(__file__), "../../submodules/matrix/fonts/4x6.bdf"
        )
        self.font.LoadFont(font_path)

    def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """Get latitude and longitude coordinates for an address."""
        try:
            geocode_url = (
                f"https://www.sfmta.com/find-a-stop/geocode?address={quote(address)}"
            )
            response = requests.get(geocode_url, timeout=10)
            response.raise_for_status()
            payload = response.json()

            if payload.get("results") and len(payload["results"]) > 0:
                location = payload["results"][0]["geometry"]["location"]
                return location["lat"], location["lng"]
            return None
        except Exception as e:
            log_network_error(geocode_url, e, "sfmta")
            return None

    def get_nearby_stops(self, lat: float, lng: float) -> List[Dict]:
        """Get list of nearby bus stops."""
        try:
            bbox = get_bounding_box(lat, lng)
            stops_url = (
                f"https://www.sfmta.com/find-a-stop/query?"
                f"bbox={bbox['swLng']},{bbox['sw']},{bbox['neLng']},{bbox['neLat']}"
                f"&limit=20&lang=en"
            )
            response = requests.get(stops_url, timeout=10)
            response.raise_for_status()
            stops_data = response.json()

            # Filter stops that have routes and sort by route count (more routes = busier stop)
            useful_stops = [
                stop for stop in stops_data.get("stops", []) if stop.get("routes")
            ]
            useful_stops.sort(key=lambda x: len(x.get("routes", [])), reverse=True)
            return useful_stops[:5]  # Top 5 stops
        except Exception as e:
            log_network_error("SFMTA stops API", e, "sfmta")
            return []

    def get_predictions(self, stop_id: str) -> List[Dict]:
        """Get arrival predictions for a stop."""
        try:
            url = (
                f"https://webservices.umoiq.com/api/pub/v1/agencies/sfmta-cis/stopcodes/"
                f"{stop_id}/predictions?key=0be8ebd0284ce712a63f29dcaf7798c4"
            )
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return []

            predictions = []
            for bus in response.json():
                if bus.get("values"):
                    # Get next 2 arrival times
                    arrival_times = [
                        x["minutes"]
                        for x in bus["values"][:2]
                        if x.get("minutes") is not None
                    ]
                    if arrival_times:  # Only include routes with actual predictions
                        predictions.append(
                            {
                                "route": bus["route"]["title"],
                                "color": bus["route"].get("color", "FFFFFF"),
                                "minutes": arrival_times,
                            }
                        )

            # Sort by soonest arrival
            predictions.sort(key=lambda x: min(x["minutes"]) if x["minutes"] else 999)
            return predictions[:4]  # Top 4 routes per stop
        except Exception as e:
            log_network_error("SFMTA predictions API", e, "sfmta")
            return []

    def update_data(self):
        """Fetch and update transit data for all configured addresses"""
        current_time = time.time()

        # Fetch new data periodically
        if current_time - self.last_fetch_time > self.REFRESH_RATE_SECONDS:
            self.logger.info("Fetching updated SFMTA data...")

            for address in self.target_addresses:
                coords = self.get_coordinates(address)
                if not coords:
                    self.logger.warning(f"Could not get coordinates for {address}")
                    continue

                lat, lng = coords
                stops = self.get_nearby_stops(lat, lng)
                self.logger.info(f"Found {len(stops)} nearby stops for {address}")

                # Get predictions for each stop
                address_data = {"stops": [], "predictions": {}}
                for stop in stops:
                    stop_id = stop.get("stop_id")
                    if stop_id:
                        predictions = self.get_predictions(stop_id)
                        if predictions:  # Only include stops with active predictions
                            address_data["stops"].append(stop)
                            address_data["predictions"][stop_id] = predictions

                self.current_data[address] = address_data

            # Reset display state when data updates
            self.current_address_index = 0
            self.current_stop_index = 0
            self.last_display_time = current_time
            self.last_fetch_time = current_time

            total_addresses = len(
                [addr for addr in self.target_addresses if addr in self.current_data]
            )
            self.logger.info(f"SFMTA update complete: {total_addresses} addresses with transit data")

    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        try:
            hex_color = hex_color.lstrip("#")
            if len(hex_color) == 6:
                return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
            return (255, 255, 255)  # Default to white
        except:
            return (255, 255, 255)

    def draw_frame(self):
        """Draw the current transit data to the canvas"""
        if not self.canvas:
            return

        current_time = time.time()

        # Check if it's time to switch stops/addresses
        if current_time - self.last_display_time >= self.STOP_DISPLAY_DURATION_SECONDS:
            if self.current_data:
                addresses_with_data = [
                    addr
                    for addr in self.target_addresses
                    if addr in self.current_data and self.current_data[addr]["stops"]
                ]
                if addresses_with_data:
                    current_address = addresses_with_data[self.current_address_index]
                    stops = self.current_data[current_address]["stops"]

                    # Move to next stop, or next address if we've cycled through all stops
                    self.current_stop_index = (self.current_stop_index + 1) % len(stops)
                    if (
                        self.current_stop_index == 0
                    ):  # Wrapped around, move to next address
                        self.current_address_index = (
                            self.current_address_index + 1
                        ) % len(addresses_with_data)

                    pass  # Remove verbose logging

            self.last_display_time = current_time

        # Don't clear canvas - let new content overwrite old for better performance

        if not self.current_data:
            # Display a "No Transit Data" message
            white = graphics.Color(255, 255, 255)
            graphics.DrawText(self.canvas, self.font, 5, 16, white, "NO TRANSIT")
            return

        # Get current address and stop data
        addresses_with_data = [
            addr
            for addr in self.target_addresses
            if addr in self.current_data and self.current_data[addr]["stops"]
        ]
        if not addresses_with_data:
            white = graphics.Color(255, 255, 255)
            graphics.DrawText(self.canvas, self.font, 5, 16, white, "NO ROUTES")
            return

        current_address = addresses_with_data[self.current_address_index]
        stops = self.current_data[current_address]["stops"]
        predictions_data = self.current_data[current_address]["predictions"]

        if not stops:
            white = graphics.Color(255, 255, 255)
            graphics.DrawText(self.canvas, self.font, 5, 16, white, "NO STOPS")
            return

        current_stop = stops[self.current_stop_index]
        stop_id = current_stop.get("stop_id")
        predictions = predictions_data.get(stop_id, [])

        # Colors
        white = graphics.Color(255, 255, 255)
        yellow = graphics.Color(255, 255, 0)
        green = graphics.Color(0, 255, 0)

        # Display stop name (truncated)
        stop_name = current_stop.get("title", "Unknown Stop")[:12]
        graphics.DrawText(self.canvas, self.font, 1, 6, yellow, stop_name)

        # Display predictions
        if not predictions:
            graphics.DrawText(self.canvas, self.font, 1, 16, white, "No arrivals")
            return

        y_pos = 14
        for pred in predictions[:3]:  # Show up to 3 routes
            if y_pos > 30:  # Don't go off screen
                break

            route_name = pred["route"][:8]  # Truncate route name
            minutes = pred["minutes"]

            # Use route color if available
            try:
                r, g, b = self.hex_to_rgb(pred["color"])
                route_color = graphics.Color(r, g, b)
            except:
                route_color = white

            # Display route name
            graphics.DrawText(self.canvas, self.font, 1, y_pos, route_color, route_name)

            # Display arrival times
            if len(minutes) >= 2:
                time_text = f"{minutes[0]}m {minutes[1]}m"
            elif len(minutes) == 1:
                time_text = f"{minutes[0]}m"
            else:
                time_text = "N/A"

            graphics.DrawText(self.canvas, self.font, 35, y_pos, green, time_text)
            y_pos += 8

    def update_and_draw(self):
        """Update data and draw to the canvas"""
        self.update_data()
        self.draw_frame()
