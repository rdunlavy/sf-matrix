from samplebase import SampleBase

# Import matrix_import first to set up the correct modules
import src.utils.matrix_import

from src.display.controller import DisplayController
from src.data_sources.espn import ESPNModule
from src.data_sources.bay_wheels import BayWheelsModule
from src.data_sources.sfmta import SFMTAModule
from src.data_sources.news import NewsModule
from src.data_sources.weather import WeatherModule
from src.utils.logger import matrix_logger


class MatrixApp(SampleBase):
    def run(self):
        # Initialize logging
        matrix_logger.system_startup(5)  # 5 modules total
        
        controller = DisplayController(self.matrix)
        controller.add_module(ESPNModule())
        controller.add_module(BayWheelsModule())
        controller.add_module(SFMTAModule())
        controller.add_module(NewsModule())
        controller.add_module(WeatherModule())

        try:
            # Start the display loop
            controller.run()
        except KeyboardInterrupt:
            matrix_logger.system_shutdown()
        except Exception as e:
            matrix_logger.error(f"Fatal error in main loop: {e}")
            raise


if __name__ == "__main__":
    app = MatrixApp()
    if not app.process():
        app.print_help()
