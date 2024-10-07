import geopandas as gpd
import pandas as pd
from openspoor.mapservices import MapServicesQuery
from shapely.geometry import Point, LineString, Polygon

class Test:
    def test_transform_geojson_to_gdf_point(self):
        mapservices_data = MapServicesQuery()
        input_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"attribute1": "ABC", "attribute2": 123},
                    "geometry": {"type": "Point", "coordinates": [1, 2]}
                },
                {
                    "type": "Feature",
                    "properties": {"attribute1": "DEF", "attribute2": 456},
                    "geometry": {"type": "Point", "coordinates": [5, 10]}
                }
            ]
        }
        output_data = mapservices_data._transform_dict_to_gdf(input_data)

        expected_output = gpd.GeoDataFrame(
            {"attribute1": ["ABC", "DEF"], "attribute2": [123, 456]},
            geometry=[Point(1, 2), Point(5, 10)]
        )
        pd.testing.assert_frame_equal(output_data, expected_output)

    def test_transform_geojson_to_gdf_polyline(self):
        mapservices_data = MapServicesQuery()
        input_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"attribute1": "ABC", "attribute2": 123},
                    "geometry": {"type": "LineString", "coordinates": [[123, 456], [234, 567], [345, 678]]}
                },
                {
                    "type": "Feature",
                    "properties": {"attribute1": "DEF", "attribute2": 456},
                    "geometry": {"type": "LineString", "coordinates": [[1, 2], [3, 4], [5, 6]]}
                }
            ]
        }
        output_data = mapservices_data._transform_dict_to_gdf(input_data)

        expected_output = gpd.GeoDataFrame(
            {"attribute1": ["ABC", "DEF"], "attribute2": [123, 456]},
            geometry=[
                LineString([(123, 456), (234, 567), (345, 678)]),
                LineString([(1, 2), (3, 4), (5, 6)])
            ]
        )
        pd.testing.assert_frame_equal(output_data, expected_output)

    def test_transform_geojson_to_gdf_polygon(self):
        mapservices_data = MapServicesQuery()
        input_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"attribute1": "ABC", "attribute2": 123},
                    "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
                },
                {
                    "type": "Feature",
                    "properties": {"attribute1": "DEF", "attribute2": 456},
                    "geometry": {"type": "Polygon", "coordinates": [[[10, 20], [20, 20], [20, 30], [15, 35], [10, 20]]]}
                }
            ]
        }
        output_data = mapservices_data._transform_dict_to_gdf(input_data)

        expected_output = gpd.GeoDataFrame(
            {"attribute1": ["ABC", "DEF"], "attribute2": [123, 456]},
            geometry=[
                Polygon([(0, 0), (1, 0), (1, 1), (0, 0)]),
                Polygon([(10, 20), (20, 20), (20, 30), (15, 35), (10, 20)])
            ]
        )
        pd.testing.assert_frame_equal(output_data, expected_output)
