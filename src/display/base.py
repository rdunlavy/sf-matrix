from abc import ABC, abstractmethod
import os
from src.utils.matrix_import import RGBMatrix, graphics


class DisplayModule(ABC):
    def __init__(self):
        self.matrix = None
        self.canvas = None
        self.font = graphics.Font()
        font_path = os.path.join(
            os.path.dirname(__file__), "../../submodules/matrix/fonts/7x13.bdf"
        )
        self.font.LoadFont(font_path)

    def set_matrix(self, matrix: RGBMatrix, canvas):
        """Set the matrix and canvas references"""
        self.matrix = matrix
        self.canvas = canvas

    @abstractmethod
    def update_and_draw(self) -> None:
        """Fetch data and draw to the canvas"""
        pass

    @abstractmethod
    def update_data(self) -> None:
        """Fetch/update the data for this module"""
        pass

    @abstractmethod
    def draw_frame(self) -> None:
        """Draw the current data to the canvas"""
        pass

    def get_display_duration(self) -> int:
        """Return the display duration in seconds for this module"""
        # Default duration if not overridden by subclass
        return 20
    
    def needs_continuous_updates(self) -> bool:
        """Return True if this module needs continuous re-rendering (animation/cycling)"""
        # Default: static content, no continuous updates needed
        return False
    
    def get_frame(self):
        """Update data, draw frame, and return canvas"""
        self.update_data()
        self.draw_frame()
        return self.canvas
