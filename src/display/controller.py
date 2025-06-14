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

            # Draw initial frame and display immediately
            try:
                module.update_and_draw()
                # Swap to display the frame (SetImage is much faster now)
                self.canvas = self.matrix.SwapOnVSync(self.canvas)
            except Exception as e:
                self.logger.error(f"Error in {module_name}.update_and_draw(): {e}")
                continue

            # Display for module-specific duration
            module_duration = module.get_display_duration()
            start_time = time.time()
            
            # Only do continuous updates if module actually needs them
            if hasattr(module, 'draw_frame'):
                # This module needs continuous updates (like scrolling)
                while time.time() - start_time < module_duration:
                    try:
                        module.draw_frame()
                        self.canvas = self.matrix.SwapOnVSync(self.canvas)
                    except Exception as e:
                        self.logger.error(f"Error in {module_name}.draw_frame(): {e}")
                        break
                    time.sleep(0.1)
            else:
                # Static content - just sleep, no need for continuous updates
                time.sleep(module_duration)

            # Move to next module
            self.current_module = (self.current_module + 1) % len(self.modules)
