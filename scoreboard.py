import time
import requests
import argparse
import datetime
import os
import sys
from zoneinfo import ZoneInfo
from typing import List, Optional
from PIL import Image
from io import BytesIO
from espn_types import ESPNScoreboardResponse

# Attempt to import the matrix libraries
RGBMatrix = None
RGBMatrixOptions = None
graphics = None
hardware_available = False
emulator_available = False

try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

    hardware_available = True
except ImportError:
    print("INFO: RGBMatrix library not found. Hardware mode will be unavailable.")

try:
    from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions, graphics

    emulator_available = True
except ImportError:
    print(
        "INFO: RGBMatrixEmulator library not found. Emulator mode will be unavailable."
    )

if not hardware_available and not emulator_available:
    print("ERROR: Neither RGBMatrix nor RGBMatrixEmulator could be imported. Exiting.")
    sys.exit(1)


# --- Configuration ---
MATRIX_ROWS = 32
MATRIX_COLS = 64
REFRESH_RATE_SECONDS = 10  # How often to fetch new data
GAME_DISPLAY_DURATION_SECONDS = 8  # How long to show each game
TIMEZONE = "America/Los_Angeles"

# ESPN API Endpoints from https://gist.github.com/akeaswaran/b48b02f1c94f873c6655e7129910fc3b
API_URLS = {
    "MLB": "http://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
    # "NFL": "http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    "NBA": "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
    "NHL": "http://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
    "WNBA": "http://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard",
    # "NCAAF": "http://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard",
    # "NCAAM": "http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard",
}

# --- Helper Functions ---


def fetch_scores(league: str) -> Optional[ESPNScoreboardResponse]:
    """Fetches scores for a given league."""
    url = API_URLS.get(league.upper())
    if not url:
        print(f"Error: League {league} not supported.")
        return None
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {league} scores: {e}")
        return None


def fetch_and_resize_logo(
    logo_url: str, max_width: int = 32, max_height: int = 32
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
        background.paste(img, (0, 0), img.split()[3] if img.mode == "RGBA" else None)

        # Resize maintaining aspect ratio
        background.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        return background
    except Exception as e:
        print(f"Error fetching logo: {e}")
        return None


def process_game_data(
    data: Optional[ESPNScoreboardResponse], league: str
) -> List[dict]:
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
            competition.get("status", {}).get("type", {}).get("name", "STATUS_UNKNOWN")
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
                    local_tz = ZoneInfo(TIMEZONE)
                    game_date = game_date_utc.astimezone(local_tz)
                except ImportError:
                    print("WARNING: pytz not installed, using UTC time")
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
                    game_info["time_str"] = game_date.strftime("%m/%d %I:%M%p").lstrip(
                        "0"
                    )  # e.g., 5/15 7:00PM
            else:
                game_info["date"] = None
                game_info["time_str"] = "TBD"

        except ValueError as ve:
            print(f"Error parsing date for event {event.get('id')}: {ve}")
            game_info["date"] = None
            game_info["time_str"] = "TBD"

        competitors = competition.get("competitors", [])
        if len(competitors) < 2:
            continue

        # Determine home and away teams
        # ESPN API usually lists away team first, home team second if homeAway is present
        # otherwise, we might need to infer or it might not matter for basic display
        team1 = competitors[0]
        team2 = competitors[1]

        if team1.get("homeAway") == "away":
            away_team = team1
            home_team = team2
        elif team2.get("homeAway") == "away":  # Should be "home" but check just in case
            away_team = team2
            home_team = team1
        else:  # Default if homeAway is not clear, may need league-specific logic
            away_team = team1
            home_team = team2

        # Add team logos
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


def display_game_on_matrix(matrix, game_data, font, small_font):
    """Displays a single game's data on the matrix."""
    if not matrix or not game_data:
        return

    canvas = matrix.CreateFrameCanvas()
    canvas.Clear()

    # Colors
    white = graphics.Color(255, 255, 255)
    red = graphics.Color(255, 0, 0)
    green = graphics.Color(0, 255, 0)
    blue = graphics.Color(0, 0, 255)
    yellow = graphics.Color(255, 255, 0)

    # League at top
    # graphics.DrawText(canvas, small_font, 1, 6, yellow, game_data["league"])

    # Away team logo (left side)
    away_logo = None
    if "away_logo" in game_data:
        away_logo = fetch_and_resize_logo(game_data["away_logo"])
        if away_logo:
            # Center the logo vertically
            y_offset = (MATRIX_ROWS - away_logo.height) // 2
            for y in range(away_logo.height):
                for x in range(away_logo.width):
                    r, g, b = away_logo.getpixel((x, y))
                    canvas.SetPixel(x, y + y_offset, r, g, b)

    # Home team logo (right side)
    home_logo = None
    if "home_logo" in game_data:
        home_logo = fetch_and_resize_logo(game_data["home_logo"])
        if home_logo:
            # Center the logo vertically
            y_offset = (MATRIX_ROWS - home_logo.height) // 2
            for y in range(home_logo.height):
                for x in range(home_logo.width):
                    r, g, b = home_logo.getpixel((x, y))
                    canvas.SetPixel(MATRIX_COLS - x - 1, y + y_offset, r, g, b)

    # Center content
    # Away team and score
    away_team_text = f"{game_data['away_team']}"
    away_score_text = f"{game_data['away_score']}"
    away_text = f"{away_team_text} {away_score_text}"
    away_text_len = graphics.DrawText(
        canvas, font, 0, 0, white, away_text
    )  # Dry run for length
    away_x = (MATRIX_COLS - away_text_len) // 2
    graphics.DrawText(canvas, font, away_x, 15, white, away_text)

    # Home team and score
    home_team_text = f"{game_data['home_team']}"
    home_score_text = f"{game_data['home_score']}"
    home_text = f"{home_team_text} {home_score_text}"
    home_text_len = graphics.DrawText(
        canvas, font, 0, 0, white, home_text
    )  # Dry run for length
    home_x = (MATRIX_COLS - home_text_len) // 2
    graphics.DrawText(canvas, font, home_x, 23, white, home_text)

    # Game status
    status_color = white
    if game_data["status_type"] == "STATUS_IN_PROGRESS":
        status_color = green
    elif game_data["status_type"] == "STATUS_SCHEDULED":
        status_color = blue
    elif game_data["status_type"] == "STATUS_FINAL":
        status_color = red

    status_text = game_data.get("display_status", "").upper()
    status_len = graphics.DrawText(canvas, font, 0, 0, status_color, status_text)
    status_x = (MATRIX_COLS - status_len) // 2
    if status_x < 1:
        status_x = 1
    graphics.DrawText(canvas, font, status_x, 31, status_color, status_text)

    matrix.SwapOnVSync(canvas)


def get_matrix(mode: str):
    if mode == "hardware":
        if not hardware_available:
            print(
                "ERROR: Hardware mode selected, but RGBMatrix library is not available. Exiting."
            )
            return
        # This import is specific to the hzeller library
        from rgbmatrix import RGBMatrix, RGBMatrixOptions

        print("INFO: Initializing RPi RGB Matrix in HARDWARE mode...")
        options = RGBMatrixOptions()
        options.rows = MATRIX_ROWS
        options.cols = MATRIX_COLS
        options.chain_length = 1
        options.parallel = 1
        options.hardware_mapping = (
            "adafruit-hat"  # Or 'regular', 'adafruit-hat-pwm' etc.
        )
        # options.gpio_slowdown = 2 # If you have issues with rPi4
        # options.drop_privileges = False # If run as root, set to True after init

        return RGBMatrix(options=options)
    elif mode == "emulator":
        if not emulator_available:
            print(
                "ERROR: Emulator mode selected, but RGBMatrixEmulator library is not available. Exiting."
            )
            return
        # This import is specific to the emulator
        from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions

        print("INFO: Initializing RGB Matrix EMULATOR mode...")
        # Emulator specific options might be needed if different from hardware
        # For now, assume options are compatible or emulator handles them.
        emu_options = RGBMatrixOptions()
        emu_options.rows = MATRIX_ROWS
        emu_options.cols = MATRIX_COLS
        emu_options.chain_length = 1
        emu_options.parallel = 1
        # Emulator might have its own window sizing options etc.
        # consult RGBMatrixEmulator documentation for details
        return RGBMatrix(options=emu_options)
    else:
        raise ValueError(f"Invalid mode: {mode}")


# --- Main Application ---
def main():
    parser = argparse.ArgumentParser(description="ESPN Scoreboard for RGB LED Matrix")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["hardware", "emulator"],
        required=True,
        help="Display mode: 'hardware' for RPi matrix, 'emulator' for desktop.",
    )

    args = parser.parse_args()

    matrix = get_matrix(args.mode)

    if not matrix:
        print("ERROR: Could not initialize matrix. Exiting.")
        return

    # --- Load Fonts ---
    # Check if font paths are absolute or relative to script dir
    script_dir = os.path.dirname(os.path.realpath(__file__))
    default_font_dir = os.path.join(script_dir, "submodules/rpi-rgb-led-matrix/fonts")

    font_file_path = os.path.join(default_font_dir, "4x6.bdf")
    small_font_file_path = os.path.join(default_font_dir, "tom-thumb.bdf")

    if not os.path.exists(font_file_path):
        print(f"ERROR: Font file not found at {font_file_path}")
        print(
            "Please ensure you have the 'fonts' directory in submodules/rpi-rgb-led-matrix/fonts or provide a valid path."
        )
        return
    if not os.path.exists(small_font_file_path):
        print(f"ERROR: Small font file not found at {small_font_file_path}")
        return

    font = graphics.Font()
    font.LoadFont(font_file_path)

    small_font = graphics.Font()
    small_font.LoadFont(small_font_file_path)

    # --- Main Loop ---
    all_games_data = []
    last_fetch_time = 0
    current_game_index = 0

    try:
        print("INFO: Starting scoreboard display. Press CTRL+C to exit.")
        while True:
            current_time = time.time()

            # Fetch new data periodically
            if current_time - last_fetch_time > REFRESH_RATE_SECONDS:
                print(f"INFO: Fetching updated scores at {datetime.datetime.now()}...")
                temp_games_data = []
                for league in API_URLS.keys():
                    raw_data = fetch_scores(league)
                    processed_games = process_game_data(raw_data, league)
                    if processed_games:
                        temp_games_data.extend(processed_games)

                if temp_games_data:
                    all_games_data = temp_games_data
                    # Sort all collected games again (live first, then by time across all leagues)
                    all_games_data.sort(
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
                    current_game_index = 0  # Reset to first game after refresh
                else:
                    # Keep old data if fetch fails, but notify
                    print(
                        "WARN: Failed to fetch new data, or no games available. Using previous data if any."
                    )

                last_fetch_time = current_time

            if not all_games_data:
                # Display a "No Games" message or wait
                canvas = matrix.CreateFrameCanvas()
                canvas.Clear()
                no_games_text = "NO GAMES"
                text_len = graphics.DrawText(
                    canvas, font, 0, 0, white, no_games_text
                )  # Dry run
                text_x = (MATRIX_COLS - text_len) // 2
                text_y = (
                    (MATRIX_ROWS // 2) + (font.height // 2) - 2
                )  # Center vertically
                graphics.DrawText(canvas, font, text_x, text_y, white, "NO GAMES")
                matrix.SwapOnVSync(canvas)
                time.sleep(
                    min(GAME_DISPLAY_DURATION_SECONDS, REFRESH_RATE_SECONDS)
                )  # Wait before trying fetch again
                continue

            # Display current game
            game_to_display = all_games_data[current_game_index]
            print(
                f"Displaying: {game_to_display['away_team']} vs {game_to_display['home_team']} ({game_to_display['display_status']})"
            )
            display_game_on_matrix(matrix, game_to_display, font, small_font)

            # Move to next game
            current_game_index = (current_game_index + 1) % len(all_games_data)

            time.sleep(GAME_DISPLAY_DURATION_SECONDS)

    except KeyboardInterrupt:
        print("INFO: Exiting scoreboard display.")
    finally:
        if matrix:
            matrix.Clear()
        print("INFO: Cleanup complete.")


if __name__ == "__main__":
    # Check if running as root for hardware, necessary for hzeller library
    if os.geteuid() != 0 and any(m in sys.argv for m in ["hardware"]):
        print(
            "WARNING: For hardware mode, this script usually needs to be run as root."
        )
        print("Attempting to continue, but may fail to access GPIO.")
    main()
