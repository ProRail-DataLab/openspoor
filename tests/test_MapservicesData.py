import geopandas as gpd
import pandas as pd
from openspoor.mapservices import MapServicesQuery
from shapely.geometry import Point, LineString, Polygon

class Test:
    def test_transform_dict_to_gdf_point(self):
        mapservices_data = MapServicesQuery()
        input_data = {'geometryType': 'esriGeometryPoint',
                      'features': [{'attributes': {'attribute1': 'ABC', 'attribute2': 123},
                                    'geometry': {'x': 1, 'y': 2}},
                                   {'attributes': {'attribute1': 'DEF', 'attribute2': 456},
                                    'geometry': {'x': 5, 'y': 10}},
                                   ]}
        output_data = mapservices_data._transform_dict_to_gdf(input_data)

        expected_output = gpd.GeoDataFrame({'attribute1': ['ABC', 'DEF'], 'attribute2': [123, 456]},
                                           geometry=[Point(1, 2), Point(5, 10)])
        pd.testing.assert_frame_equal(output_data, expected_output)

    def test_transform_dict_to_gdf_poly_line(self):
        mapservices_data = MapServicesQuery()
        input_data = {'geometryType': 'esriGeometryPolyline',
                      'features': [{'attributes': {'attribute1': 'ABC', 'attribute2': 123},
                                    'geometry': {'paths': [[[123, 456], [234, 567], [345, 678]]]}},
                                   {'attributes': {'attribute1': 'DEF', 'attribute2': 456},
                                    'geometry': {'paths': [[[1, 2], [3, 4], [5, 6]]]}},
                                   ]}
        output_data = mapservices_data._transform_dict_to_gdf(input_data)

        expected_output = gpd.GeoDataFrame({'attribute1': ['ABC', 'DEF'], 'attribute2': [123, 456]},
                                           geometry=[LineString([(123, 456), (234, 567), (345, 678)]),
                                                     LineString([(1, 2), (3, 4), (5, 6)])])
        pd.testing.assert_frame_equal(output_data, expected_output)

    def test_transform_dict_to_gdf_polygon(self):
        mapservices_data = MapServicesQuery()
        input_data = {'geometryType': 'esriGeometryPolygon',
                      'features': [{'attributes': {'attribute1': 'ABC', 'attribute2': 123},
                                    'geometry': {'rings': [[[0, 0], [1, 0], [1, 1]]]}},
                                   {'attributes': {'attribute1': 'DEF', 'attribute2': 456},
                                    'geometry': {'rings': [[[10, 20], [20, 20], [20, 30], [15, 35]]]}},
                                   ]}
        output_data = mapservices_data._transform_dict_to_gdf(input_data)

        expected_output = gpd.GeoDataFrame({'attribute1': ['ABC', 'DEF'], 'attribute2': [123, 456]},
                                           geometry=[Polygon([(0, 0), (1, 0), (1, 1)]),
                                                     Polygon([(10, 20), (20, 20), (20, 30), (15, 35)])])
        pd.testing.assert_frame_equal(output_data, expected_output)