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
    current_dir = os.getcwd()
    utils_dir = os.path.dirname(__file__)
    calculated_root = os.path.abspath(os.path.join(utils_dir, "../.."))
    
    # Try multiple possible font paths in order of preference
    possible_paths = [
        # Standard calculated path
        os.path.join(calculated_root, f"submodules/matrix/fonts/{font_name}.bdf"),
        # Current working directory
        os.path.join(current_dir, f"submodules/matrix/fonts/{font_name}.bdf"),
        # Absolute hardcoded path (as last resort)
        f"/home/ryandunlavy/sf-matrix/submodules/matrix/fonts/{font_name}.bdf"
    ]
    
    font_path = None
    for path in possible_paths:
        if os.path.exists(path):
            font_path = path
            break
    
    # If none found, use the first one for error reporting
    if font_path is None:
        font_path = possible_paths[0]
    
    # Debug info for troubleshooting
    print(f"Loading font: {font_name}")
    print(f"Trying paths in order:")
    for i, path in enumerate(possible_paths):
        exists = os.path.exists(path)
        print(f"  {i+1}. {path} -> {'EXISTS' if exists else 'NOT FOUND'}")
    print(f"Selected font path: {font_path}")
    print(f"Final check - File exists: {os.path.exists(font_path)}")
    
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