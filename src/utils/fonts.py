"""
Font loading utilities for the SF Matrix Display
"""
import os
from src.utils.matrix_import import graphics


def load_font(font_name: str) -> graphics.Font:
    """
    Load a BDF font from the matrix fonts directory
    
    Args:
        font_name: Name of the font file without .bdf extension (e.g. "4x6", "7x13")
        
    Returns:
        graphics.Font object
        
    Raises:
        Exception: If font file cannot be loaded
    """
    font = graphics.Font()
    
    # Get absolute path to the project root, then to fonts
    # This works from any module location in the project
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    font_path = os.path.join(project_root, f"submodules/matrix/fonts/{font_name}.bdf")
    
    font.LoadFont(font_path)
    return font