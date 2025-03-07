import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import LineString, Point

from openspoor.transformers import TransformerCoordinatesToSpoor


@pytest.fixture
def lines_gdf():
    return gpd.GeoDataFrame(
        {
            "linename": ["D-A-C-E", "F-B-C-G"],
            "GEOCODE": ["DE", "FG"],
            "SUBCODE": ["1", "1"],
            "NAAM_LANG": ["DtoE", "FtoG"],
            "KM_GEOCODE_VAN": [10, 40],
            "KM_GEOCODE_TOT": [50, 0],
        },
        geometry=[
            LineString([(0, 0, 10), (10, 10, 20), (20, 20, 50)]),
            LineString([(30, 0, 40), (20, 10, 10), (10, 20, 0)]),
        ],
        crs="EPSG:28992",
    )


def test_determine_geocode_km(points_gdf, lines_gdf):
    point_index = [0, 1, 2, 2]

    lines_gdf = pd.concat([lines_gdf] * 2)
    lines_gdf.index = point_index

    out = TransformerCoordinatesToSpoor._determine_geocode_km(
        lines_gdf, points_gdf
    )
    expected_values = pd.Series(index=point_index, data=[26.0, 8.0, 35.0, 5.0])
    pd.testing.assert_series_equal(out, expected_values)


@pytest.fixture
def points_gdf():
    return gpd.GeoDataFrame(
        {"pointname": ["A", "B", "C"]},
        crs="EPSG:28992",
        index=[0, 1, 2],
        geometry=[
            Point(12, 12),  # Lies on first line
            Point(18, 12),  # Lies on second line
            Point(15, 15),
        ],
    )  # Lies on both


@pytest.fixture
def far_points_gdf():
    return gpd.GeoDataFrame(
        {"pointname": ["P", "Q"]},
        crs="EPSG:28992",
        index=[0, 1],
        geometry=[Point(-0.5, 0), Point(0, 30.5)],  # Should be in next segment
    )  # Should be in another segment


@pytest.mark.parametrize("best_match_only", [True, False])
def test_transform(monkeypatch, points_gdf, lines_gdf, best_match_only):

    monkeypatch.setattr(
        TransformerCoordinatesToSpoor,
        "_get_spoortak_met_geokm",
        lambda q: lines_gdf,
    )
    transformer = TransformerCoordinatesToSpoor(
        best_match_only=best_match_only
    )
    out = transformer.transform(points_gdf)

    expected_out = pd.concat([points_gdf, points_gdf.iloc[2:, :]])
    for col in [
        "linename",
        "GEOCODE",
        "SUBCODE",
        "NAAM_LANG",
        "KM_GEOCODE_VAN",
        "KM_GEOCODE_TOT",
    ]:
        expected_out[col] = list(lines_gdf[col].values) * 2
    expected_out["geocode_kilometrering"] = [26.0, 8.0, 35.0, 5.0]
    if best_match_only:
        # The last point has two hits, best takes the first one
        expected_out = expected_out.iloc[:-1, :]
    pd.testing.assert_frame_equal(out, expected_out)


@pytest.mark.parametrize("best_match_only", [True, False])
def test_transform_far_points(
    monkeypatch, far_points_gdf, lines_gdf, best_match_only
):
    monkeypatch.setattr(
        TransformerCoordinatesToSpoor,
        "_get_spoortak_met_geokm",
        lambda q: lines_gdf,
    )

    out = TransformerCoordinatesToSpoor(
        best_match_only=best_match_only
    ).transform(far_points_gdf)

    expected_out = far_points_gdf
    for col in ["linename", "GEOCODE", "SUBCODE", "NAAM_LANG"]:
        expected_out[col] = [None] * 2
    for col in ["KM_GEOCODE_VAN", "KM_GEOCODE_TOT", "geocode_kilometrering"]:
        expected_out[col] = [np.nan] * 2

    if best_match_only:
        # If no hits are good enough, none are returned
        expected_out = expected_out.iloc[[], :]

    expected_out.replace(np.nan, None, inplace=True)
    out.replace(np.nan, None, inplace=True)

    pd.testing.assert_frame_equal(out, expected_out)
