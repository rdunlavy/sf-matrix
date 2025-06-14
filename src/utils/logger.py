import logging
import logging.handlers
import os


class MatrixLogger:
    """Centralized logging system for the SF Matrix display"""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MatrixLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self):
        """Setup the logger with both file and console handlers"""
        self._logger = logging.getLogger('sf_matrix')
        self._logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers if logger already exists
        if self._logger.handlers:
            return
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s - %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
        
        # File handler with rotation
        log_file = os.path.join(os.path.dirname(__file__), '../../matrix_display.log')
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """Get a logger instance for a specific module"""
        if name:
            return logging.getLogger(f'sf_matrix.{name}')
        return self._logger
    
    def info(self, message: str, module: str = None):
        """Log info message"""
        logger = self.get_logger(module) if module else self._logger
        logger.info(message)
    
    def warning(self, message: str, module: str = None):
        """Log warning message"""
        logger = self.get_logger(module) if module else self._logger
        logger.warning(message)
    
    def error(self, message: str, module: str = None):
        """Log error message"""
        logger = self.get_logger(module) if module else self._logger
        logger.error(message)
    
    def network_error(self, url: str, error: Exception, module: str):
        """Log network request errors"""
        logger = self.get_logger(module)
        logger.error(f"Network request failed for {url}: {error}")
    
    def module_switch(self, from_module: str, to_module: str):
        """Log module switching in DisplayController"""
        self._logger.info(f"Switching from {from_module} to {to_module}")
    
    def system_startup(self, num_modules: int):
        """Log system startup"""
        self._logger.info(f"SF Matrix display starting with {num_modules} modules")
    
    def system_shutdown(self):
        """Log system shutdown"""
        self._logger.info("SF Matrix display shutting down")


# Global logger instance
matrix_logger = MatrixLogger()

# Convenience functions for easy importing
def get_logger(module_name: str = None) -> logging.Logger:
    """Get a logger for a specific module"""
    return matrix_logger.get_logger(module_name)

def log_info(message: str, module: str = None):
    """Log info message"""
    matrix_logger.info(message, module)

def log_warning(message: str, module: str = None):
    """Log warning message"""
    matrix_logger.warning(message, module)

def log_error(message: str, module: str = None):
    """Log error message"""
    matrix_logger.error(message, module)

def log_network_error(url: str, error: Exception, module: str):
    """Log network request errors"""
    matrix_logger.network_error(url, error, module)