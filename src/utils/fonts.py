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
    utils_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(utils_dir, "../.."))
    font_path = os.path.join(project_root, f"submodules/matrix/fonts/{font_name}.bdf")
    
    # Debug info for troubleshooting
    print(f"Loading font: {font_name}")
    print(f"__file__: {__file__}")
    print(f"utils_dir: {utils_dir}")
    print(f"project_root: {project_root}")
    print(f"Font path: {font_path}")
    print(f"File exists: {os.path.exists(font_path)}")
    print(f"File readable: {os.access(font_path, os.R_OK)}")
    print(f"Current working dir: {os.getcwd()}")
    print(f"Contents of project_root: {os.listdir(project_root) if os.path.exists(project_root) else 'NOT FOUND'}")
    if os.path.exists(os.path.join(project_root, 'submodules')):
        print(f"Contents of submodules: {os.listdir(os.path.join(project_root, 'submodules'))}")
        if os.path.exists(os.path.join(project_root, 'submodules/matrix')):
            print(f"Contents of matrix: {os.listdir(os.path.join(project_root, 'submodules/matrix'))}")
            if os.path.exists(os.path.join(project_root, 'submodules/matrix/fonts')):
                print(f"Contents of fonts: {os.listdir(os.path.join(project_root, 'submodules/matrix/fonts'))[:5]}...")  # First 5 files
    
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