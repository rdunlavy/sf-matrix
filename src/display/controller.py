import time
from .base import DisplayModule
from src.utils.logger import get_logger
from src.utils.config import DISPLAY_TIME_PER_MODULE
from src.utils.matrix_import import RGBMatrix


class DisplayController:
    def __init__(self, matrix: RGBMatrix):
        self.matrix = matrix
        self.canvas = self.matrix.CreateFrameCanvas()
        self.modules = []
        self.current_module = 0
        self.display_time = DISPLAY_TIME_PER_MODULE
        self.logger = get_logger('controller')

    def add_module(self, module: DisplayModule) -> None:
        """Add a display module and provide it with matrix reference only"""
        # Don't pass canvas reference - modules will get current canvas during render
        module.set_matrix(self.matrix, None)
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

            # Fill canvas with black background instead of clearing (prevents flash)
            self.canvas.Fill(0, 0, 0)  # Black background, not transparent
            try:
                # Give module the current canvas for this render
                module.canvas = self.canvas
                module.update_and_draw()
                # Give Pi Zero time to complete drawing operations
                time.sleep(0.1)
                # Swap to display the completed frame
                self.canvas = self.matrix.SwapOnVSync(self.canvas)
            except Exception as e:
                self.logger.error(f"Error in {module_name}.update_and_draw(): {e}")
                continue

            # Display for module-specific duration
            module_duration = module.get_display_duration()
            start_time = time.time()
            
            # Only do continuous updates for modules that actually need animation/cycling
            if module.needs_continuous_updates():
                # This module needs continuous updates (ESPN games, News scrolling, BayWheels stations)
                while time.time() - start_time < module_duration:
                    # Fill canvas with black background for continuous updates
                    self.canvas.Fill(0, 0, 0)
                    try:
                        # Give module the current canvas for this render
                        module.canvas = self.canvas
                        module.draw_frame()
                        # Give Pi Zero time to complete drawing
                        time.sleep(0.05)
                        self.canvas = self.matrix.SwapOnVSync(self.canvas)
                    except Exception as e:
                        self.logger.error(f"Error in {module_name}.draw_frame(): {e}")
                        break
                    time.sleep(0.1)
            else:
                # Static content (Weather, SFMTA) - just sleep, no re-rendering needed
                time.sleep(module_duration)

            # Move to next module
            self.current_module = (self.current_module + 1) % len(self.modules)
