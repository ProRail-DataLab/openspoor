import re

import matplotlib.colors as mcolors


def is_valid_folium_color(color: str) -> bool:
    """Check if a string is a valid color for Folium.

    Args:
        color (str): The color string to check.

    Returns:
        bool: True if the color is valid, False otherwise.
    """

    color = color.strip().lower()

    if color in mcolors.CSS4_COLORS:
        return True
    if re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", color):
        return True
    if re.fullmatch(r"rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)", color):
        return True
    if re.fullmatch(
        r"rgba\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*(0|1|0?\.\d+)\s*\)", color
    ):
        return True
    return False
