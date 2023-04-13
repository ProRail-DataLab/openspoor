import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString
import pytest
from unittest import mock
import numpy as np

from openspoor.transformers import TransformerCoordinatesToSpoor


@pytest.fixture
def lines_gdf():
    return gpd.GeoDataFrame({'linename': ['D-A-C-E', 'F-B-C-G'],
                             'GEOCODE': ['DE', 'FG'],
                             'SUBCODE': ['1', '1'],
                             'NAAM_LANG': ['DtoE', 'FtoG'],
                             'KM_GEOCODE_VAN': [10, 40],
                             'KM_GEOCODE_TOT': [50, 0]},
                            geometry=[LineString([(0, 0, 10), (10, 10, 20), (20, 20, 50)]),
                                      LineString([(30, 0, 40), (20, 10, 10), (10, 20, 0)])])


def test_determine_geocode_km(points_gdf, lines_gdf):
    point_index = [0, 1, 2, 2]

    lines_gdf = pd.concat([lines_gdf] * 2)
    lines_gdf.index = point_index

    out = TransformerCoordinatesToSpoor._determine_geocode_km(lines_gdf, points_gdf)
    expected_values = pd.Series(index=point_index, data=[26.0, 8.0, 35.0, 5.0])
    pd.testing.assert_series_equal(out, expected_values)


@pytest.fixture
def points_gdf():
    return gpd.GeoDataFrame({'pointname': ['A', 'B', 'C']},
                            crs='EPSG:28992',
                            index=[0, 1, 2],
                            geometry=[Point(12, 12),  # Lies on first line
                                      Point(18, 12),  # Lies on second line
                                      Point(15, 15)])  # Lies on both


@pytest.fixture
def far_points_gdf():
    return gpd.GeoDataFrame({'pointname': ['P', 'Q']},
                            crs='EPSG:28992',
                            index=[0, 1],
                            geometry=[Point(-0.5, 0),  # Should be in next segment
                                      Point(0, 30.5)])  # Should be in another segment


@mock.patch("openspoor.transformers.TransformerCoordinatesToSpoor._get_spoortak_met_geokm")
def test_transform(mocked_load, points_gdf, lines_gdf):
    mocked_load.return_value = lines_gdf

    out = TransformerCoordinatesToSpoor().transform(points_gdf)

    expected_out = pd.concat([points_gdf, points_gdf.iloc[2:, :]])
    for col in ['linename', 'GEOCODE', 'SUBCODE', 'NAAM_LANG', 'KM_GEOCODE_VAN', 'KM_GEOCODE_TOT']:
        expected_out[col] = list(lines_gdf[col].values) * 2
    expected_out['geocode_kilometrering'] = [26.0, 8.0, 35.0, 5.0]
    pd.testing.assert_frame_equal(out, expected_out)


@mock.patch("openspoor.transformers.TransformerCoordinatesToSpoor._get_spoortak_met_geokm")
def test_transform_far_points(mocked_load, far_points_gdf, lines_gdf):
    mocked_load.return_value = lines_gdf

    out = TransformerCoordinatesToSpoor().transform(far_points_gdf)

    expected_out = far_points_gdf
    for col in ['linename', 'GEOCODE', 'SUBCODE', 'NAAM_LANG']:
        expected_out[col] = [None] * 2
    for col in ['KM_GEOCODE_VAN', 'KM_GEOCODE_TOT', 'geocode_kilometrering']:
        expected_out[col] = [np.nan] * 2
    pd.testing.assert_frame_equal(out, expected_out)
