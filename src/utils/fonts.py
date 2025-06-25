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
    
    # Debug info for troubleshooting
    print(f"Loading font: {font_name}")
    print(f"Font path: {font_path}")
    print(f"File exists: {os.path.exists(font_path)}")
    print(f"File readable: {os.access(font_path, os.R_OK)}")
    
    try:
        font.LoadFont(font_path)
        print(f"Successfully loaded font: {font_name}")
        return font
    except Exception as e:
        print(f"Font loading failed: {e}")
        # Try fallback to a smaller font that might work better
        if font_name != "4x6":
            print(f"Trying fallback font: 4x6")
            fallback_path = os.path.join(project_root, "submodules/matrix/fonts/4x6.bdf")
            font.LoadFont(fallback_path)
            return font
        else:
            raise e