import geopandas as gpd
import pandas as pd
from openspoor.transformers import TransformerCoordinatesToSpoor
from shapely.geometry import Point, LineString


class Test:
    def test__get_geo_km_as_df(self):
        coordinates_transformer = TransformerCoordinatesToSpoor()
        input_df = gpd.GeoDataFrame(
            {
                "x": [112734.526, 112732.526, 112679.485, 95659.390, 0, 95648.723],
                "y": [480849.498, 480846.498, 480767.155, 433499.239, 0, 433520.105],
                "GEOSUBCODE": ["133_a", "133_a", "133_a", "664_b", None, "664_b"],
            },
            geometry=[
                Point(112734.526, 480849.498),
                Point(112732.526, 480846.498),
                Point(112679.485, 480767.155),
                Point(95659.390, 433499.239),
                Point(0, 0),
                Point(95648.723, 433520.105),
            ],
            index=[5, 10, 7, 8, 2, 1],
        )
        matched_index = input_df["GEOSUBCODE"].notnull()
        output_df = coordinates_transformer._get_geo_km_as_df(
            input_df[matched_index], one_point=False
        )

        expected_output = pd.DataFrame(
            {
                "geocode_kilometrering": [13.565, 13.665, 13.569, 43.097, 43.076],
                "GEOSUBCODE": ["133_a", "133_a", "133_a", "664_b", "664_b"],
                "index": [5, 7, 10, 1, 8],
            }
        )
        pd.testing.assert_frame_equal(output_df, expected_output)

    def test_prep_dictionary_for_mapservices_call_sample_input(self):
        input_df = gpd.GeoDataFrame(
            {"x": [6, 1, 4], "y": [0, -5, 7]},
            geometry=[Point(1, 4), Point(2, 5), Point(3, 6)],
            index=[4, 2, 1],
        )

        output = TransformerCoordinatesToSpoor._prep_dictionary_for_mapservices_call(
            input_df
        )

        expected_output = {
            "features": [
                {
                    "geometry": {"coordinates": [1, 4], "type": "Point"},
                    "properties": {"FID": "4"},
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": [2, 5], "type": "Point"},
                    "properties": {"FID": "2"},
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": [3, 6], "type": "Point"},
                    "properties": {"FID": "1"},
                    "type": "Feature",
                },
            ],
            "name": "RD_Coordinaten",
            "type": "FeatureCollection",
        }
        assert output == expected_output

    def test_transform_json_to_km_dataframe_sample_input(self):
        input_dict = {
            "features": [
                {
                    "properties": {
                        "KM_GEOCODE": "10,2",
                        "GEOSUBCODE": "101_",
                        "FID": "3",
                    }
                },
                {
                    "properties": {
                        "KM_GEOCODE": "100,9",
                        "GEOSUBCODE": "176_a",
                        "FID": "6",
                    }
                },
                {"properties": {"KM_GEOCODE": "5,3", "GEOSUBCODE": "100", "FID": "1"}},
            ]
        }
        output_df = TransformerCoordinatesToSpoor._transform_json_to_km_dataframe(
            input_dict, one_point=False
        )

        expected_output = pd.DataFrame(
            {
                "geocode_kilometrering": [5.3, 10.2, 100.9],
                "GEOSUBCODE": ["100", "101_", "176_a"],
                "index": [1, 3, 6],
            }
        )
        pd.testing.assert_frame_equal(output_df, expected_output)

    def test_get_lokale_kilometrering_as_series_with_an_unknown_SPOOR_ID(self):
        spoortak_gdf = gpd.GeoDataFrame(
            {"NAAM_LANG": "ABC", "GEOSUBCODE": "123", "PRORAIL_GEBIED": "Inktpot"},
            geometry=[LineString([(10, 10), (13, 14), (13, 20)])],
            index=[1],
        )
        coordinates_transformer = TransformerCoordinatesToSpoor()
        coordinates_transformer.spoortak_gdf = spoortak_gdf

        input_gdf = gpd.GeoDataFrame(
            {
                "SPOOR_ID": ["ABC", "DEF"],
                "GEOSUBCODE": ["123", "456"],
                "PRORAIL_GEBIED": ["Inktpot", "OCCR"],
            },
            geometry=[Point(14, 18), Point(66, 9)],
            index=[5, 6],
        )

        output_gdf = coordinates_transformer._get_lokale_kilometrering_as_df(input_gdf)

        expected_output = pd.DataFrame(
            {
                "index": [5],
                "GEOSUBCODE": ["123"],
                "SPOOR_ID": ["ABC"],
                "lokale_kilometrering": [0.009],
            }
        )
        pd.testing.assert_frame_equal(output_gdf, expected_output)
