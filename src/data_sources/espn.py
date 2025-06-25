import time
import requests
import datetime
import os
from zoneinfo import ZoneInfo
from typing import List, Optional
from PIL import Image
from io import BytesIO
from src.display import DisplayModule
from src.utils.logger import get_logger, log_network_error
from src.utils.matrix_import import graphics
from src.utils.fonts import load_font

from src.utils.config import (
    FAVORITE_TEAMS,
    TIMEZONE,
    REFRESH_RATES,
    GAME_DISPLAY_DURATION,
    SPORTS_LEAGUES,
)

# All available ESPN API URLs
ALL_ESPN_API_URLS = {
    "NBA": "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
    "NFL": "http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    "WNBA": "http://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard",
    "NHL": "http://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
    "MLB": "http://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
}

# Filter to only include leagues specified in SPORTS_LEAGUES
ESPN_API_URLS = {
    league: url for league, url in ALL_ESPN_API_URLS.items()
    if league in SPORTS_LEAGUES
}


class ESPNModule(DisplayModule):
    def __init__(self):
        super().__init__()

        # Configuration from config.py
        self.REFRESH_RATE_SECONDS = REFRESH_RATES["espn"]
        self.GAME_DISPLAY_DURATION_SECONDS = GAME_DISPLAY_DURATION
        self.TIMEZONE = TIMEZONE
        self.API_URLS = ESPN_API_URLS

        # State management
        self.all_games_data = []
        self.current_game_index = 0
        self.last_fetch_time = 0
        self.last_display_time = time.time()  # Initialize to current time
        self.games_per_cycle = 3  # Show 3 games per 10-second DisplayController cycle
        self.logger = get_logger("espn")

        # Load fonts
        self.font = load_font("4x6")

    def fetch_scores(self, league: str) -> Optional[dict]:
        """Fetches scores for a given league."""
        url = self.API_URLS.get(league.upper())
        if not url:
            self.logger.error(f"League {league} not supported")
            return None
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            log_network_error(url, e, "espn")
            return None

    def _normalize_logo_size(
        self, image: Image.Image, target_width: int, target_height: int
    ) -> Image.Image:
        """Normalize logo size to ensure consistent visual appearance across different teams"""
        # Calculate the area of the original image
        original_width, original_height = image.size
        original_area = original_width * original_height

        # Target area for consistency (aim for 70% of max area to ensure good visibility)
        target_area = int(target_width * target_height * 0.7)

        # Calculate scale factor based on area rather than just dimensions
        if original_area > 0:
            area_scale = (target_area / original_area) ** 0.5
        else:
            area_scale = 1.0

        # Apply the scale factor
        new_width = int(original_width * area_scale)
        new_height = int(original_height * area_scale)

        # Ensure we don't exceed the target dimensions
        if new_width > target_width:
            scale_factor = target_width / new_width
            new_width = target_width
            new_height = int(new_height * scale_factor)

        if new_height > target_height:
            scale_factor = target_height / new_height
            new_height = target_height
            new_width = int(new_width * scale_factor)

        # Resize the image
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def fetch_and_resize_logo(
        self, logo_url: str, max_width: int = 32, max_height: int = 28
    ) -> Optional[Image.Image]:
        """Fetch and resize a team logo to fit the matrix."""
        try:
            response = requests.get(logo_url, timeout=5)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))

            # Convert to RGBA to handle transparency
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            # Create a new RGB image with black background
            background = Image.new("RGB", img.size, (0, 0, 0))

            # Paste the logo onto the background using the alpha channel as mask
            background.paste(
                img, (0, 0), img.split()[3] if img.mode == "RGBA" else None
            )

            # Normalize logo size for consistent appearance
            background = self._normalize_logo_size(background, max_width, max_height)

            return background
        except Exception as e:
            log_network_error(logo_url, e, "espn")
            return None

    def process_game_data(self, data: Optional[dict], league: str) -> List[dict]:
        """Processes raw API data into a standardized format."""
        games: List[dict] = []
        if not data or "events" not in data:
            return games

        for event in data["events"]:
            game_info: dict = {"league": league}
            competitions = event.get("competitions", [])
            if not competitions:
                continue

            competition = competitions[0]
            status = (
                competition.get("status", {})
                .get("type", {})
                .get("name", "STATUS_UNKNOWN")
            )
            game_info["status_detail"] = (
                competition.get("status", {}).get("type", {}).get("shortDetail", "")
            )
            game_info["status_type"] = status

            # Game start time
            try:
                game_date_str = event.get("date")
                if game_date_str:
                    # Parse UTC time from API
                    game_date_utc = datetime.datetime.fromisoformat(
                        game_date_str.replace("Z", "+00:00")
                    )
                    game_info["date"] = game_date_utc

                    # Convert to local timezone
                    try:
                        local_tz = ZoneInfo(self.TIMEZONE)
                        game_date = game_date_utc.astimezone(local_tz)
                    except ImportError:
                        self.logger.warning("zoneinfo not available, using UTC time")
                        game_date = game_date_utc

                    # Check if game date is today (in local time)
                    today = (
                        datetime.datetime.now(datetime.timezone.utc)
                        .astimezone(datetime.timezone.utc)
                        .date()
                    )
                    if game_date.date() == today:
                        # Just show time for today's games
                        game_info["time_str"] = game_date.strftime("%I:%M%p").lstrip(
                            "0"
                        )  # e.g., 7:00PM
                    else:
                        # Show date and time for future games
                        game_info["time_str"] = game_date.strftime(
                            "%m/%d %I:%M%p"
                        ).lstrip(
                            "0"
                        )  # e.g., 5/15 7:00PM
                else:
                    game_info["date"] = None
                    game_info["time_str"] = "TBD"

            except ValueError as ve:
                self.logger.error(
                    f"Error parsing date for event {event.get('id')}: {ve}"
                )
                game_info["date"] = None
                game_info["time_str"] = "TBD"

            competitors = competition.get("competitors", [])
            if len(competitors) < 2:
                continue

            # Determine home and away teams
            team1 = competitors[0]
            team2 = competitors[1]

            if team1.get("homeAway") == "away":
                away_team = team1
                home_team = team2
            elif team2.get("homeAway") == "away":
                away_team = team2
                home_team = team1
            else:  # Default if homeAway is not clear
                away_team = team1
                home_team = team2

            # Add team data
            away_team_data = away_team.get("team", {})
            home_team_data = home_team.get("team", {})

            game_info["away_team"] = away_team_data.get("abbreviation", "AWAY")
            game_info["home_team"] = home_team_data.get("abbreviation", "HOME")
            game_info["away_score"] = away_team.get("score", "0")
            game_info["home_score"] = home_team.get("score", "0")

            # Add logo URLs
            if "logo" in away_team_data:
                game_info["away_logo"] = away_team_data["logo"]
            if "logo" in home_team_data:
                game_info["home_logo"] = home_team_data["logo"]

            # Extract betting odds for scheduled games
            game_info["odds"] = None
            if status == "STATUS_SCHEDULED":
                try:
                    # ESPN API sometimes includes odds in competition.odds
                    odds_data = competition.get("odds")
                    if odds_data and len(odds_data) > 0:
                        # Use the first available odds provider
                        first_odds = odds_data[0]
                        if "details" in first_odds:
                            game_info["odds"] = first_odds["details"]
                        elif (
                            "homeTeamOdds" in first_odds
                            and "awayTeamOdds" in first_odds
                        ):
                            home_odds = first_odds.get("homeTeamOdds", {}).get(
                                "displayOdds", ""
                            )
                            away_odds = first_odds.get("awayTeamOdds", {}).get(
                                "displayOdds", ""
                            )
                            if home_odds and away_odds:
                                game_info["odds"] = f"{away_odds}/{home_odds}"
                except Exception as e:
                    self.logger.debug(f"Could not extract odds for game: {e}")
                    game_info["odds"] = None

            # Game state specific details
            if status == "STATUS_IN_PROGRESS":
                game_info["display_status"] = game_info[
                    "status_detail"
                ]  # e.g., "Top 5th", "Q2 2:30"
            elif status == "STATUS_SCHEDULED":
                game_info["display_status"] = game_info["time_str"]
            elif status in ["STATUS_FINAL", "STATUS_POSTPONED", "STATUS_CANCELED"]:
                game_info["display_status"] = game_info[
                    "status_detail"
                ]  # e.g. "Final", "Postponed"
            else:
                game_info["display_status"] = " ".join(
                    game_info["status_detail"].split(" ")[0:2]
                )  # Keep it short

            games.append(game_info)

        # Filter out games more than a week away
        one_week_from_now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
        games = [g for g in games if g["date"] is None or g["date"] <= one_week_from_now]

        # Sort games: live games first, then upcoming, then by time
        games.sort(
            key=lambda g: (
                g["status_type"]
                != "STATUS_IN_PROGRESS",  # False for in-progress (comes first)
                g["status_type"]
                != "STATUS_SCHEDULED",  # False for scheduled (comes after in-progress)
                (
                    g["date"]
                    if g["date"]
                    else datetime.datetime.max.replace(tzinfo=datetime.timezone.utc)
                ),  # Sort by date for scheduled
            )
        )
        return games

    def update_data(self):
        """Fetch and update game data from all leagues"""
        current_time = time.time()

        # Fetch new data periodically
        if current_time - self.last_fetch_time > self.REFRESH_RATE_SECONDS:
            self.logger.info("Fetching updated ESPN scores...")
            temp_games_data = []
            for league in self.API_URLS.keys():
                raw_data = self.fetch_scores(league)
                processed_games = self.process_game_data(raw_data, league)
                if processed_games:
                    temp_games_data.extend(processed_games)
                    self.logger.info(f"Found {len(processed_games)} {league} games")

            if temp_games_data:
                self.all_games_data = temp_games_data
                # Sort all collected games again (live first, then by time across all leagues)
                self.all_games_data.sort(
                    key=lambda g: (
                        g["status_type"] != "STATUS_IN_PROGRESS",
                        g["status_type"] != "STATUS_SCHEDULED",
                        (
                            g["date"]
                            if g["date"]
                            else datetime.datetime.max.replace(
                                tzinfo=datetime.timezone.utc
                            )
                        ),
                    )
                )
                self.logger.info(f"Total games found: {len(self.all_games_data)}")
                self.current_game_index = 0  # Reset to first game after refresh
            else:
                # Keep old data if fetch fails, but notify
                self.logger.warning(
                    "Failed to fetch new ESPN data, or no games available. Using previous data if any."
                )

            self.last_fetch_time = current_time

    def draw_frame(self):
        """Draw the current game data to the canvas"""
        if not self.canvas:
            return

        current_time = time.time()

        # Check if it's time to switch games (cycle faster within DisplayController's window)
        if current_time - self.last_display_time >= self.GAME_DISPLAY_DURATION_SECONDS:
            if self.all_games_data and len(self.all_games_data) > 1:
                self.current_game_index = (self.current_game_index + 1) % len(
                    self.all_games_data
                )
            self.last_display_time = current_time

        # Don't clear canvas - let new content overwrite old for better performance

        if not self.all_games_data:
            # Display a "No Games" message
            white = graphics.Color(255, 255, 255)
            no_games_text = "NO GAMES"
            graphics.DrawText(self.canvas, self.font, 20, 16, white, no_games_text)
            return

        # Get current game to display
        game_data = self.all_games_data[self.current_game_index]

        # Colors
        white = graphics.Color(255, 255, 255)
        red = graphics.Color(255, 0, 0)
        green = graphics.Color(0, 255, 0)
        blue = graphics.Color(0, 0, 255)
        yellow = graphics.Color(255, 255, 0)

        # Display team logos - positioned to prevent cutoff
        if "away_logo" in game_data:
            away_logo = self.fetch_and_resize_logo(
                game_data["away_logo"], max_width=18, max_height=28
            )
            if away_logo:
                # Position away logo on far left with small margin
                start_x = 1  # Small margin from left edge
                start_y = 2  # Small margin from top

                # Crop logo to avoid center overlap and use fast SetImage
                crop_width = min(away_logo.width, 19 - start_x)
                if crop_width > 0:
                    cropped_logo = away_logo.crop((0, 0, crop_width, away_logo.height))
                    self.canvas.SetImage(cropped_logo.convert('RGB'), start_x, start_y)

        if "home_logo" in game_data:
            home_logo = self.fetch_and_resize_logo(
                game_data["home_logo"], max_width=18, max_height=28
            )
            if home_logo:
                # Position home logo on far right, ensuring it fits within screen bounds
                start_x = (
                    64 - home_logo.width - 1
                )  # Position from right edge with margin
                start_y = 2  # Small margin from top

                # Ensure logo fits within right section and use fast SetImage
                if start_x >= 45:
                    max_width = 64 - start_x
                    if home_logo.width > max_width:
                        home_logo = home_logo.crop((0, 0, max_width, home_logo.height))
                    self.canvas.SetImage(home_logo.convert('RGB'), start_x, start_y)

        # League indicator at top center (above logos)
        league_text = game_data["league"]
        league_width = len(league_text) * 4  # Approximate width
        league_x = (64 - league_width) // 2
        graphics.DrawText(self.canvas, self.font, league_x, 6, yellow, league_text)

        # Team names and scores in center area (clear of logos)
        center_start = 20  # Start clear of left logo area

        # Away team and score/odds
        away_text = f"{game_data['away_team']}"
        graphics.DrawText(self.canvas, self.font, center_start, 12, white, away_text)

        # Home team and score/odds
        home_text = f"{game_data['home_team']}"
        graphics.DrawText(self.canvas, self.font, center_start, 20, white, home_text)

        # Show scores for in-progress/finished games, odds for scheduled games
        if game_data["status_type"] == "STATUS_SCHEDULED" and game_data.get("odds"):
            # Parse betting line and display as two lines where scores would go
            odds_text = game_data["odds"]
            odds_color = graphics.Color(255, 255, 0)  # Yellow for betting lines
            
            # Try to split odds like "OKC -6.5" or "LAL +3" into team and spread
            if "/" in odds_text:
                # Format like "OKC -6.5/LAL +3" - split by slash
                parts = odds_text.split("/")
                if len(parts) >= 2:
                    away_odds = parts[0].strip()
                    home_odds = parts[1].strip()
                else:
                    away_odds = odds_text
                    home_odds = ""
            else:
                # Single line format - try to parse
                parts = odds_text.split()
                if len(parts) >= 2:
                    away_odds = parts[0]  # Team name
                    home_odds = " ".join(parts[1:])  # Spread/line
                else:
                    away_odds = odds_text
                    home_odds = ""
            
            # Display odds in place of scores
            graphics.DrawText(
                self.canvas, self.font, center_start + 16, 12, odds_color, away_odds[:6]
            )
            graphics.DrawText(
                self.canvas, self.font, center_start + 16, 20, odds_color, home_odds[:6]
            )
        else:
            # Display scores for live/finished games
            away_score = f"{game_data['away_score']}"
            home_score = f"{game_data['home_score']}"
            graphics.DrawText(
                self.canvas, self.font, center_start + 16, 12, white, away_score
            )
            graphics.DrawText(
                self.canvas, self.font, center_start + 16, 20, white, home_score
            )

        # Game status with color coding at bottom center
        status_color = white
        if game_data["status_type"] == "STATUS_IN_PROGRESS":
            status_color = green
        elif game_data["status_type"] == "STATUS_SCHEDULED":
            status_color = blue
        elif game_data["status_type"] == "STATUS_FINAL":
            status_color = red

        status_text = game_data.get("display_status", "").upper()[
            :12
        ]  # Slightly longer for center
        status_width = len(status_text) * 4  # Approximate width
        status_x = (64 - status_width) // 2
        graphics.DrawText(
            self.canvas, self.font, status_x, 30, status_color, status_text
        )

    def get_display_duration(self) -> int:
        """Return dynamic display duration based on number of games"""
        if not self.all_games_data:
            return 10  # Short duration if no games
        elif len(self.all_games_data) == 1:
            return 15  # Medium duration for single game
        elif len(self.all_games_data) <= 3:
            return 25  # Longer duration for few games
        else:
            return 35  # Long duration for many games to cycle through
    
    def needs_continuous_updates(self) -> bool:
        """ESPN needs continuous updates to cycle through games"""
        return True

    def update_and_draw(self):
        """Update data and draw to the canvas"""
        self.update_data()
        # Reset display time when DisplayController switches to this module
        self.last_display_time = time.time()
        self.draw_frame()
