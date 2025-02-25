import os

import folium
import geopandas as gpd
import pandas as pd
import pytest
from shapely import wkt
from shapely.geometry import LineString, Point, Polygon

from openspoor.visualisations.trackmap import (
    PlottingAreas,
    PlottingLineStrings,
    PlottingPoints,
    TrackMap,
    plottable,
)


@pytest.fixture(scope="session")
def base_trackmap():
    return TrackMap()


@pytest.fixture(scope="session")
def example_plottingdataframe():
    return PlottingPoints(
        {"lat": [52.45, 52.5], "lon": [5.15, 5.2], "name": ["ABC", "DEF"]}
    )


@pytest.fixture()
def prefilled_trackmap(example_plottingdataframe):
    return TrackMap(objects=[example_plottingdataframe])


def test_TrackMap(
    base_trackmap, prefilled_trackmap, example_plottingdataframe
):
    objects_in_base_trackmap = len(base_trackmap._children)
    objects_in_prefilled_trackmap = len(prefilled_trackmap._children)
    assert (
        objects_in_base_trackmap == 1
    ), "Should contain only the aerial photo"
    assert objects_in_prefilled_trackmap == 1 + len(
        example_plottingdataframe.data
    ), "Should contain the aerial photo and some markers"


@pytest.fixture
def points_dataframe():
    return pd.DataFrame(
        data={
            "lat": [52.45, 52.5, 52.55, 52.6],
            "lon": [5.15, 5.2, 5.3, 5.4],
            "name": ["A", "B", "C", "D"],
            "name2": ["AA", "BB", "CC", "DD"],
            "value": [1, 2, 3, 4],
            "marker": ["train", "eye", "train", "eye"],
        }
    )


@pytest.fixture
def lines_geodataframe():
    line1 = LineString([Point(4.9, 52.1), Point(4.95, 51.1)]).wkt
    line2 = LineString([Point(5.0, 52.1), Point(4.95, 51.1)]).wkt
    line3 = LineString([Point(4.8, 52.1), Point(4.95, 51.1)]).wkt

    return (
        pd.DataFrame(
            data={
                "name": ["Q", "R", "S"],
                "name2": ["QQ", "RR", "SS"],
                "geometry": [line1, line2, line3],
            }
        )
        .assign(geometry=lambda d: d.geometry.apply(wkt.loads))
        .pipe(gpd.GeoDataFrame, geometry="geometry", crs="EPSG:4326")
        .assign(geometry=lambda d: d.geometry.to_crs("EPSG:4326"))
    )


@pytest.fixture
def areas_geodataframe():
    area1 = Polygon(
        [
            Point(5.0, 52.0),
            Point(5.1, 52.0),
            Point(5.1, 52.1),
            Point(5.0, 52.1),
            Point(5.0, 52.0),
        ]
    ).wkt
    area2 = Polygon(
        [
            Point(5.5, 52.0),
            Point(5.6, 52.0),
            Point(5.6, 52.1),
            Point(5.5, 52.1),
            Point(5.5, 52.0),
        ]
    ).wkt
    area3 = Polygon(
        [
            Point(6.0, 53.0),
            Point(6.1, 53.0),
            Point(6.1, 53.1),
            Point(6.0, 53.1),
            Point(6.0, 53.0),
        ]
    ).wkt
    area4 = Polygon(
        [
            Point(6.5, 53.0),
            Point(6.6, 53.0),
            Point(6.6, 53.1),
            Point(6.5, 53.1),
            Point(6.5, 53.0),
        ]
    ).wkt

    return (
        pd.DataFrame(
            data={
                "name": ["M", "N", "O", "P"],
                "name2": ["MM", "NN", "OO", "PP"],
                "geometry": [area1, area2, area3, area4],
            }
        )
        .assign(geometry=lambda d: d.geometry.apply(wkt.loads))
        .pipe(gpd.GeoDataFrame, geometry="geometry", crs="EPSG:4326")
        .assign(geometry=lambda d: d.geometry.to_crs("EPSG:4326"))
    )


@pytest.mark.parametrize("add_aerial", [True, False])
def test_add_to_trackmap(
    tmp_path,
    add_aerial,
    points_dataframe,
    lines_geodataframe,
    areas_geodataframe,
):
    m = TrackMap(add_aerial=add_aerial)

    PlottingPoints(points_dataframe, popup=["name2"]).add_to(m)
    PlottingLineStrings(lines_geodataframe, popup=["name2"]).add_to(m)
    PlottingAreas(areas_geodataframe, popup=["name2"]).add_to(m)

    # For the points and areas, 1 child is added for every row in the dataframe
    # 1 child always exists when the aerial photograph is added
    aerial_photograph_children = add_aerial
    # Linestrings always add 2 objects; one for the hover,
    # and one for the lines themselves
    linestring_children = 2
    total_objects = (
        len(points_dataframe)
        + linestring_children
        + len(areas_geodataframe)
        + aerial_photograph_children
    )

    assert len(m._children) == total_objects, "Invalid number of items added"

    m.save(str(tmp_path / "test_output.html"))
    # One more bounds fitted object
    assert (
        len(m._children) == 1 + total_objects
    ), "Invalid number of items added"

    assert "test_output.html" in os.listdir(tmp_path), "No file was created"

    # Make a new map, that should be inferred to show the same data
    # Type is established with plottable, and popup is a string instead
    # of a list
    q = TrackMap()
    plottable(points_dataframe, popup="name").add_to(q)
    plottable(lines_geodataframe, popup="name").add_to(q)
    plottable(areas_geodataframe, popup="name").add_to(q)
    q.save(str(tmp_path / "test_output2.html"))

    for m_child, q_child in zip(m._children, q._children):
        assert type(m_child) is type(q_child), "Unequal type"

    # Popup is a list with 2 elements, and test some additional
    # settings for linestrings and areas
    r = TrackMap()
    PlottingPoints(points_dataframe, popup=["name", "name2"]).add_to(r)
    PlottingLineStrings(
        lines_geodataframe, popup=["name", "name2"], color="blue"
    ).add_to(r)
    PlottingAreas(
        areas_geodataframe, popup=["name", "name2"], color="orange"
    ).add_to(r)
    r.save(str(tmp_path / "test_output3.html"))

    for m_child, r_child in zip(m._children, r._children):
        assert type(m_child) is type(r_child), "Unequal type"


def test_plottingpoint_settings(points_dataframe, tmp_path):
    m = TrackMap()
    PlottingPoints(
        points_dataframe, popup=["name", "name2"], rotation_column="lat"
    ).add_to(m)
    PlottingPoints(
        points_dataframe, popup=["name", "name2"], marker_column="marker"
    ).add_to(m)
    PlottingPoints(
        points_dataframe, popup=["name", "name2"], markertype="train"
    ).add_to(m)
    PlottingPoints(
        points_dataframe,
        popup=["name", "name2"],
        markertype="circle",
        radius_column="lat",
    ).add_to(m)
    markers_added = len(
        [child for child in m._children if child.split("_")[0] == "marker"]
    )
    circles_added = len(
        [child for child in m._children if child.split("_")[0] == "circle"]
    )

    num_expected_markers = 3 * len(points_dataframe)
    num_expected_circles = 1 * len(points_dataframe)
    assert (
        num_expected_markers == markers_added
    ), "Unexpected amount of objects"
    assert (
        num_expected_circles == circles_added
    ), "Unexpected amount of objects"


def test_fix_zoom(prefilled_trackmap):
    children_before = prefilled_trackmap._children.copy()
    prefilled_trackmap._fix_zoom()
    children_after = prefilled_trackmap._children.copy()
    for child in children_before:
        try:
            if children_before[child]["_name"] == "FitBounds":
                assert False
        except TypeError:
            pass

    fitbounds_found = False
    for child in children_after:
        try:
            if children_after[child]._name == "FitBounds":
                fitbounds_found = True
        except TypeError:
            pass
    assert fitbounds_found


def test_makesmaller(prefilled_trackmap):
    assert type(prefilled_trackmap.show(notebook=False)) is not type(
        prefilled_trackmap.show(notebook=True)
    )


def test_save_trackmap(prefilled_trackmap, tmpdir):
    prefilled_trackmap.save(os.path.join(tmpdir, "output.html"))
    assert os.listdir(tmpdir) == ["output.html"]


def test_colors(points_dataframe):
    # Create map with colors based on unique values in a given column
    m = TrackMap()
    PlottingPoints(points_dataframe, color_column="value").add_to(m)

    markercolors = []
    for _, child in m._children.items():
        if isinstance(child, folium.map.Marker):
            for _, grandchild in child._children.items():
                print(grandchild.options)
                markercolors.append(grandchild.options["marker_color"])
    assert markercolors == [
        "purple",
        "lightblue",
        "darkgreen",
        "blue",
    ], "Incorrect colors for points"

    # Create map with colors based on numeric values in a given column
    q = TrackMap()
    PlottingPoints(
        points_dataframe,
        colors=(
            "value",
            {(-1, 2.0): "green", (2.0, 3.5): "orange", (3.5, 10): "red"},
        ),
    ).add_to(q)

    markercolors = []
    for _, child in q._children.items():
        if isinstance(child, folium.map.Marker):
            for _, grandchild in child._children.items():
                markercolors.append(grandchild.options["marker_color"])
    assert markercolors == [
        "green",
        "orange",
        "orange",
        "red",
    ], "Incorrect colors for points"
