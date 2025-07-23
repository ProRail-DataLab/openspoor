import pytest

from openspoor.visualisations.colorchecker import is_valid_folium_color


@pytest.mark.parametrize(
    "color, expected",
    [
        ("red", True),
        ("#00FF00", True),
        ("rgb(255,0,0)", True),
        ("rgba(0,0,255,0.5)", True),
        ("notacolor", False),
        ("C0", False),
    ],
)
def test_is_valid_folium_color(color, expected):
    assert is_valid_folium_color(color) == expected
