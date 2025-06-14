import time
from RGBMatrixEmulator import RGBMatrix
from .base import DisplayModule
from src.utils.logger import get_logger

from src.utils.config import DISPLAY_TIME_PER_MODULE


class DisplayController:
    def __init__(self, matrix: RGBMatrix):
        self.matrix = matrix
        self.canvas = self.matrix.CreateFrameCanvas()
        self.modules = []
        self.current_module = 0
        self.display_time = DISPLAY_TIME_PER_MODULE
        self.logger = get_logger('controller')

    def add_module(self, module: DisplayModule) -> None:
        """Add a display module and provide it with matrix/canvas references"""
        module.set_matrix(self.matrix, self.canvas)
        self.modules.append(module)
        module_name = module.__class__.__name__
        self.logger.info(f"Added module: {module_name}")

    def run(self):
        """Main display loop"""
        self.logger.info(f"Starting display loop with {len(self.modules)} modules")
        
        while True:
            if not self.modules:
                time.sleep(1)
                continue

            module = self.modules[self.current_module]
            module_name = module.__class__.__name__
            
            # Log module switch
            self.logger.info(f"Switching to {module_name}")

            # Clear canvas before each module draws
            self.canvas.Clear()
            try:
                module.update_and_draw()
            except Exception as e:
                self.logger.error(f"Error in {module_name}.update_and_draw(): {e}")
                continue

            # Display for module-specific duration with continuous updates for scrolling modules
            module_duration = module.get_display_duration()
            start_time = time.time()
            while time.time() - start_time < module_duration:
                # Check if this module needs continuous updates (like news scrolling)
                if hasattr(module, 'draw_frame'):
                    self.canvas.Clear()
                    try:
                        module.draw_frame()
                    except Exception as e:
                        self.logger.error(f"Error in {module_name}.draw_frame(): {e}")
                        break
                self.canvas = self.matrix.SwapOnVSync(self.canvas)
                time.sleep(0.1)

            # Move to next module
            self.current_module = (self.current_module + 1) % len(self.modules)
