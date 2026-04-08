from unittest.mock import MagicMock, patch

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import LineString, Point, Polygon

from openspoor.mapservices import MapServicesQuery


class Test:
    def test_transform_geojson_to_gdf_point(self):
        mapservices_data = MapServicesQuery(url="")
        input_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"attribute1": "ABC", "attribute2": 123},
                    "geometry": {"type": "Point", "coordinates": [1, 2]},
                },
                {
                    "type": "Feature",
                    "properties": {"attribute1": "DEF", "attribute2": 456},
                    "geometry": {"type": "Point", "coordinates": [5, 10]},
                },
            ],
        }
        output_data = mapservices_data._transform_dict_to_gdf(input_data)

        expected_output = gpd.GeoDataFrame(
            {"attribute1": ["ABC", "DEF"], "attribute2": [123, 456]},
            geometry=[Point(1, 2), Point(5, 10)],
        )
        pd.testing.assert_frame_equal(output_data, expected_output)

    def test_transform_geojson_to_gdf_polyline(self):
        mapservices_data = MapServicesQuery(url="")
        input_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"attribute1": "ABC", "attribute2": 123},
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[123, 456], [234, 567], [345, 678]],
                    },
                },
                {
                    "type": "Feature",
                    "properties": {"attribute1": "DEF", "attribute2": 456},
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[1, 2], [3, 4], [5, 6]],
                    },
                },
            ],
        }
        output_data = mapservices_data._transform_dict_to_gdf(input_data)

        expected_output = gpd.GeoDataFrame(
            {"attribute1": ["ABC", "DEF"], "attribute2": [123, 456]},
            geometry=[
                LineString([(123, 456), (234, 567), (345, 678)]),
                LineString([(1, 2), (3, 4), (5, 6)]),
            ],
        )
        pd.testing.assert_frame_equal(output_data, expected_output)

    def test_transform_geojson_to_gdf_polygon(self):
        mapservices_data = MapServicesQuery(url="")
        input_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"attribute1": "ABC", "attribute2": 123},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
                    },
                },
                {
                    "type": "Feature",
                    "properties": {"attribute1": "DEF", "attribute2": 456},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[10, 20], [20, 20], [20, 30], [15, 35], [10, 20]]
                        ],
                    },
                },
            ],
        }
        output_data = mapservices_data._transform_dict_to_gdf(input_data)

        expected_output = gpd.GeoDataFrame(
            {"attribute1": ["ABC", "DEF"], "attribute2": [123, 456]},
            geometry=[
                Polygon([(0, 0), (1, 0), (1, 1), (0, 0)]),
                Polygon([(10, 20), (20, 20), (20, 30), (15, 35), (10, 20)]),
            ],
        )
        pd.testing.assert_frame_equal(output_data, expected_output)

    @patch("openspoor.mapservices.MapservicesQuery.SafeRequest")
    def test_retrieve_max_features_count_json_format(self, mock_safe_request):
        """Test with JSON format response (f=json)"""
        # Mock the SafeRequest to return JSON format response
        mock_instance = MagicMock()
        mock_safe_request.return_value = mock_instance
        mock_instance.get_json.return_value = {"count": 123}

        result = MapServicesQuery._retrieve_max_features_count("test_url")

        assert result == 123
        mock_instance.get_json.assert_called_once_with(
            "GET", "test_url&returnCountOnly=True"
        )

    @patch("openspoor.mapservices.MapservicesQuery.SafeRequest")
    def test_retrieve_max_features_count_geojson_format(
        self, mock_safe_request
    ):
        """Test with GeoJSON format response (f=geojson)"""
        # Mock the SafeRequest to return GeoJSON format response
        mock_instance = MagicMock()
        mock_safe_request.return_value = mock_instance
        mock_instance.get_json.return_value = {"properties": {"count": 456}}

        result = MapServicesQuery._retrieve_max_features_count("test_url")

        assert result == 456
        mock_instance.get_json.assert_called_once_with(
            "GET", "test_url&returnCountOnly=True"
        )

    @patch("openspoor.mapservices.MapservicesQuery.SafeRequest")
    def test_retrieve_max_features_count_missing_count(
        self, mock_safe_request
    ):
        """Test when count is not found in response"""
        # Mock the SafeRequest to return response without count
        mock_instance = MagicMock()
        mock_safe_request.return_value = mock_instance
        mock_instance.get_json.return_value = {"some_other_key": "value"}

        with pytest.raises(ValueError, match="Count not found in response"):
            MapServicesQuery._retrieve_max_features_count("test_url")
