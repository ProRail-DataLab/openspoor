import geopandas as gpd
import pandas as pd
from openspoor.mapservices import PUICMapservices
from shapely.geometry import Point, LineString
import pytest


@pytest.fixture(scope='session')
def puic_mapservices():
    return PUICMapservices()


class Test:
    def test_transform_spoor_and_wisselkruisingbeen_to_polygons_simple_example(
            self, puic_mapservices):
        spoor_gdf = gpd.GeoDataFrame(
            {'SPOOR_ID': ['ABC'],
             'SPOOR_PUIC': [123],
             'GEOCODE_NR': [1],
             'GEOSUBCODE': ['a'],
             'KM_GEOCODE_TOT': [10.5],
             'KM_GEOCODE_VAN': [11.4],
             'X_BEGIN': [1],
             'Y_BEGIN': [0],
             'Type': ['Spoortak']
             },
            geometry=[LineString([(10, 0), (10, 1), (10, 2)])]
        )

        wisselkruisingbeen_gdf = gpd.GeoDataFrame(
            {'SPOOR_PUIC': [456],
             'Type': ['Kruisingbeen'],
             'SPOOR_ID': ['2'],
             'GEOCODE': [789],
             'GEOCODE_NR': [2],
             'GEOSUBCODE': ['b'],
             'KM_GEOCODE_TOT': [5.7],
             'KM_GEOCODE_VAN': [3.2],
             'X_BEGIN': [10],
             'Y_BEGIN': [100]
             },
            geometry=[LineString([(10, 100), (15, 100), (20, 100)])]
        )
        output = puic_mapservices._combine_spoor_and_wisselkruisingbeen(
            spoor_gdf, wisselkruisingbeen_gdf
        )

        expected_output = gpd.GeoDataFrame(
            {'SPOOR_ID': ['ABC', '2'],
             'SPOOR_PUIC': [123, 456],
             'GEOCODE_NR': [1, 2],
             'GEOSUBCODE': ['a', 'b'],
             'KM_GEOCODE_TOT': [10.5, 5.7],
             'KM_GEOCODE_VAN': [11.4, 3.2],
             'Type': ['Spoortak',
                      'Kruisingbeen'],
             'X_BEGIN': [1, 10],
             'Y_BEGIN': [0, 100]
             },
            geometry=[LineString([(10, 0), (10, 1), (10, 2)]),
                      LineString([(10, 100), (15, 100),(20, 100)])]
        )
        expected_output = expected_output[
            ['SPOOR_ID', 'SPOOR_PUIC', 'GEOCODE_NR', 'GEOSUBCODE',
             'KM_GEOCODE_TOT', 'KM_GEOCODE_VAN', 'Type', 'X_BEGIN', 'Y_BEGIN',
             'geometry']]
        pd.testing.assert_frame_equal(output, expected_output)

    def test_prep_spoortaken_gdf_minimal_example_with_one_none(self, puic_mapservices):
        spoor_gdf = gpd.GeoDataFrame(
            {'NAAM_LANG': ['ABC', None, 'DEF'],
             'REF_FYS_SPOORTAK_PUIC': [123, 456, 789]
             },
            geometry=[Point(1, 2), Point(3, 4), Point(5, 6)]
        )
        output = puic_mapservices._prep_spoor_gdf(spoor_gdf)

        expected_output = gpd.GeoDataFrame(
            {'SPOOR_ID': ['ABC', 'DEF'], 'SPOOR_PUIC': [123, 789],
             'Type': ['Spoortak', 'Spoortak']
             },
            geometry=[Point(1, 2), Point(5, 6)],
            index=[0, 2]
        )
        expected_output = expected_output[['SPOOR_ID', 'SPOOR_PUIC', 'geometry',
                                           'Type']]

        pd.testing.assert_frame_equal(output, expected_output)

    def test_prep_wisselkruisingbeen_gdf_minimal_example_with_both_wisselbeen_and_kruisingbeen(
            self, puic_mapservices):
        wisselkruisingbeen_gdf = gpd.GeoDataFrame(
            {'REF_WISSEL_KRUISING_PUIC': [123, 456, 789],
             'TYPE_WISSELKRUISINGBEEN': ['Wisselbeen', 'Kruisingbeen',
                                         'Onbekend'],
             'REF_WISSEL_KRUISING_NAAM': [1, 2, 3], 'GEOCODE': [123, 456, 789]
             },
            geometry=[Point(1, 2), Point(3, 4), Point(5, 6)])
        output = puic_mapservices._prep_wisselkruisingbeen_gdf(
            wisselkruisingbeen_gdf
        )

        expected_output = gpd.GeoDataFrame(
            {'SPOOR_PUIC': [123, 456], 'Type': ['Wisselbeen', 'Kruisingbeen'],
             'REF_WISSEL_KRUISING_NAAM': [1, 2], 'GEOCODE': [123, 456],
             'SPOOR_ID': ['123_1', '2']
             },
            geometry=[Point(1, 2), Point(3, 4)])
        expected_output = expected_output[['SPOOR_PUIC', 'Type',
                                           'REF_WISSEL_KRUISING_NAAM',
                                           'GEOCODE', 'geometry', 'SPOOR_ID']]

        pd.testing.assert_frame_equal(output, expected_output)
