import feedparser
import time
import os
import requests
from typing import List, Dict, Optional
from PIL import Image
from io import BytesIO
from src.display import DisplayModule
from src.utils.logger import get_logger, log_network_error
from src.utils.matrix_import import graphics

from src.utils.config import NEWS_SOURCES, REFRESH_RATES


class NewsModule(DisplayModule):
    def __init__(self):
        super().__init__()
        
        # Configuration from config.py
        self.REFRESH_RATE_SECONDS = REFRESH_RATES["news"]
        self.SCROLL_SPEED = 4  # Pixels to move each frame
        self.news_sources = NEWS_SOURCES
        
        # State management
        self.current_headlines = []  # List of {title, source, color} dicts
        self.current_headline_index = 0
        self.last_fetch_time = 0  # Force immediate fetch on first call
        self.last_headline_switch_time = time.time()
        self.headlines_loaded = False
        
        # Scrolling state  
        self.scroll_position = 64  # Start off screen (right side)
        self.current_headline_text = ""
        self.current_source_key = ""
        self.current_source_logo = None  # PIL Image object
        self.frame_count = 0  # Track frames for continuous scrolling
        self.headline_start_time = 0  # When current headline started
        self.pause_duration = 2.0  # Seconds to pause before scrolling
        
        # Logo cache
        self.logo_cache = {}  # {source_key: PIL.Image}
        self.logger = get_logger('news')
        
        # Load fonts
        self.font = graphics.Font()
        font_path = os.path.join(
            os.path.dirname(__file__), "../../submodules/matrix/fonts/4x6.bdf"
        )
        self.font.LoadFont(font_path)

    def fetch_headlines_from_source(self, source_key: str, source_info: Dict) -> List[Dict]:
        """Fetch headlines from a single RSS source"""
        try:
            self.logger.info(f"Fetching {source_info['name']} headlines...")
            feed = feedparser.parse(source_info["url"])
            
            headlines = []
            for entry in feed.entries[:10]:  # Limit to 10 headlines per source
                # Clean up title and limit length
                title = entry.title.strip()
                if title:
                    headlines.append({
                        "title": title,
                        "source": source_key,
                        "source_name": source_info["name"]
                    })
            
            self.logger.info(f"Found {len(headlines)} headlines from {source_info['name']}")
            return headlines
            
        except Exception as e:
            log_network_error(source_info["url"], e, "news")
            return []

    def update_data(self):
        """Fetch and update headlines from all RSS sources"""
        current_time = time.time()
        
        # Fetch new headlines periodically OR on first call
        if current_time - self.last_fetch_time > self.REFRESH_RATE_SECONDS or not self.headlines_loaded:
            self.logger.info("Fetching updated news headlines...")
            
            all_headlines = []
            for source_key, source_info in self.news_sources.items():
                headlines = self.fetch_headlines_from_source(source_key, source_info)
                all_headlines.extend(headlines)
            
            if all_headlines:
                self.current_headlines = all_headlines
                self.headlines_loaded = True
                self.logger.info(f"Total headlines collected: {len(self.current_headlines)}")
                
                # Reset to first headline and restart scrolling
                self.current_headline_index = 0
                self._start_new_headline()
            else:
                self.logger.warning("No headlines fetched")
                if not self.headlines_loaded:
                    # Add fallback headlines for testing
                    self.current_headlines = [
                        {"title": "Breaking: Test headline for news display", "source": "TEST", "source_name": "Test"}
                    ]
                    self.headlines_loaded = True
                    self.current_headline_index = 0
                    self._start_new_headline()
                    self.logger.info("Using fallback test headlines")
            
            self.last_fetch_time = current_time

    def fetch_and_resize_favicon(self, source_key: str, favicon_url: str, max_width: int = 12, max_height: int = 12) -> Optional[Image.Image]:
        """Fetch and resize a favicon to fit the matrix."""
        try:
            response = requests.get(favicon_url, timeout=5)
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

            # Boost contrast to make logos more visible on LED matrix
            background = self._boost_contrast(background)

            return background
        except Exception as e:
            log_network_error(favicon_url, e, "news")
            return None

    def _start_new_headline(self):
        """Initialize scrolling for a new headline"""
        if not self.current_headlines:
            return
            
        headline = self.current_headlines[self.current_headline_index]
        self.current_headline_text = headline["title"]
        self.current_source_key = headline["source"]
        
        # Get or fetch logo for this source
        if self.current_source_key in self.logo_cache:
            self.current_source_logo = self.logo_cache[self.current_source_key]
        elif self.current_source_key in self.news_sources:
            favicon_url = self.news_sources[self.current_source_key]["favicon_url"]
            logo = self.fetch_and_resize_favicon(self.current_source_key, favicon_url)
            if logo:
                self.logo_cache[self.current_source_key] = logo
                self.current_source_logo = logo
            else:
                self.current_source_logo = None
        else:
            self.current_source_logo = None
        
        # Reset scrolling state - start at left edge for immediate display
        self.scroll_position = 15  # Start at left edge (after logo space)
        self.headline_start_time = time.time()  # Record when headline started
        
        self.logger.info(f"Starting headline {self.current_headline_index + 1}/{len(self.current_headlines)} from {self.current_source_key}")

    def _boost_contrast(self, image: Image.Image, factor: float = 1.8) -> Image.Image:
        """Boost the contrast of an image to make it more visible on LED matrix"""
        from PIL import ImageEnhance
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        enhanced = enhancer.enhance(factor)
        
        # Also boost brightness slightly for very dark logos
        brightness_enhancer = ImageEnhance.Brightness(enhanced)
        enhanced = brightness_enhancer.enhance(1.2)
        
        return enhanced

    def _get_text_width(self, text: str) -> int:
        """Get the pixel width of text (rough approximation)"""
        # 4x6 font is approximately 4 pixels wide per character
        return len(text) * 4

    def draw_frame(self):
        """Draw the current scrolling headline to the canvas"""
        if not self.canvas:
            return

        self.canvas.Clear()

        if not self.current_headlines or not self.current_headline_text:
            # Display "Loading News" message
            white = graphics.Color(255, 255, 255)
            graphics.DrawText(self.canvas, self.font, 8, 16, white, "LOADING NEWS")
            return

        # Increment frame counter for continuous scrolling
        self.frame_count += 1
        
        # Check if we should start scrolling (after pause period)
        time_since_start = time.time() - self.headline_start_time
        if time_since_start > self.pause_duration:
            # Move scroll position left after pause
            self.scroll_position -= self.SCROLL_SPEED
        
        # Check if we should move to next headline
        text_width = self._get_text_width(self.current_headline_text)
        if self.scroll_position + text_width < 0:
            # Move to next headline only after current one has finished scrolling completely
            if self.current_headlines:
                self.current_headline_index = (self.current_headline_index + 1) % len(self.current_headlines)
                self._start_new_headline()

        # Colors
        white = graphics.Color(255, 255, 255)
        
        # Draw source logo at top left
        if self.current_source_logo:
            for y in range(self.current_source_logo.height):
                for x in range(self.current_source_logo.width):
                    r, g, b = self.current_source_logo.getpixel((x, y))
                    self.canvas.SetPixel(x + 1, y + 1, r, g, b)
        else:
            # Fallback to text if logo not available
            fallback_color = graphics.Color(255, 255, 255)
            graphics.DrawText(self.canvas, self.font, 1, 6, fallback_color, self.current_source_key)
        
        # Draw scrolling headline - simplified single line (lower to make room for logo)
        headline_text = self.current_headline_text  # No length limit for scrolling text
        
        graphics.DrawText(
            self.canvas, 
            self.font, 
            self.scroll_position, 
            20,  # Moved down to make room for favicon
            white, 
            headline_text
        )

    def get_display_duration(self) -> int:
        """Return display duration for news module"""
        # Longer duration to allow multiple headlines to scroll completely
        return 30
    
    def update_and_draw(self):
        """Update data and draw to the canvas"""
        self.update_data()
        
        # Ensure we have a headline ready to display
        if self.current_headlines and not self.current_headline_text:
            self._start_new_headline()
            
        # Draw the frame - this will be called once by DisplayController
        # But we need continuous updates for scrolling, so we'll handle that differently
        self.draw_frame()