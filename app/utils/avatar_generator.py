import hashlib
from typing import Tuple


def generate_avatar_color(username: str) -> Tuple[str, str]:
    """
    Generate background and text colors for avatar based on username
    
    Args:
        username: The username to generate colors for
        
    Returns:
        Tuple of (background_color, text_color) in hex format
    """
    # Create hash from username
    hash_object = hashlib.md5(username.encode())
    hex_dig = hash_object.hexdigest()
    
    # Extract RGB values from hash
    r = int(hex_dig[0:2], 16)
    g = int(hex_dig[2:4], 16) 
    b = int(hex_dig[4:6], 16)
    
    # Ensure colors are not too dark or too light
    r = max(80, min(200, r))
    g = max(80, min(200, g))
    b = max(80, min(200, b))
    
    background_color = f"#{r:02x}{g:02x}{b:02x}"
    
    # Calculate luminance to determine text color
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    text_color = "#ffffff" if luminance < 0.5 else "#333333"
    
    return background_color, text_color


def get_initials(username: str) -> str:
    """
    Get initials from username for avatar display
    
    Args:
        username: The username to extract initials from
        
    Returns:
        String containing 1-2 initials
    """
    if not username:
        return "U"
    
    # Split by common separators
    parts = username.replace("_", " ").replace("-", " ").replace(".", " ").split()
    
    if len(parts) >= 2:
        # Take first letter of first two parts
        return (parts[0][0] + parts[1][0]).upper()
    elif len(parts) == 1:
        # Take first letter, or first two if single word
        word = parts[0]
        if len(word) >= 2:
            return (word[0] + word[1]).upper()
        else:
            return word[0].upper()
    else:
        return "U"


def generate_avatar_svg(username: str, size: int = 100) -> str:
    """
    Generate SVG avatar based on username
    
    Args:
        username: The username to generate avatar for
        size: Size of the avatar in pixels (default: 100)
        
    Returns:
        SVG string for the avatar
    """
    background_color, text_color = generate_avatar_color(username)
    initials = get_initials(username)
    
    # Calculate font size based on avatar size
    font_size = size // 2.5
    
    svg = f'''
<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
    <circle cx="{size//2}" cy="{size//2}" r="{size//2}" fill="{background_color}"/>
    <text x="{size//2}" y="{size//2}" 
          text-anchor="middle" 
          dominant-baseline="central" 
          font-family="Arial, sans-serif" 
          font-size="{font_size}" 
          font-weight="bold" 
          fill="{text_color}">{initials}</text>
</svg>'''.strip()
    
    return svg