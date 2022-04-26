import pandas as pd
import geopandas as gpd
from openspoor.transformers import TransformerSpoortakToCoordinates
from shapely.geometry import LineString

class Test:
    def test_add_xy_sample_with_multiple_spoortakken(self):
        spoortak_gdf = gpd.GeoDataFrame(
            {'NAAM_LANG': ['A', 'B', 'C']},
            geometry=[LineString([(1000, 2000), (2000, 2000)]),
                      LineString([(12000, 0), (12600, 800), (13000, 800)]),
                      LineString([(100, 100), (200, 200)])],
            crs='epsg:28992'
        )
        spoortak_transformer = TransformerSpoortakToCoordinates(
            'spoortak_id', 'lokale_km', 'Rijksdriehoek'
        )
        spoortak_transformer = spoortak_transformer.fit(spoortak_gdf)
        input_df = pd.DataFrame({'spoortak_id': ['A', 'B', 'B'],
                                 'lokale_km': [0.5, 0.5, 1.2]})

        output_df = spoortak_transformer.transform(input_df)

        expected_output = pd.DataFrame({'spoortak_id': ['A', 'B', 'B'],
                                        'lokale_km': [0.5, 0.5, 1.2],
                                        'x': [1500., 12300., 12800.],
                                        'y': [2000., 400., 800.]})

        pd.testing.assert_frame_equal(output_df, expected_output)

    def test_add_xy_coordinates_to_gps(self):
        spoortak_gdf = gpd.GeoDataFrame(
            {'NAAM_LANG': ['A']},
            geometry=[LineString([(1000, 2000), (2000, 2000)])],
            crs='epsg:28992'
        )
        spoortak_transformer = TransformerSpoortakToCoordinates(
            'spoortak_id', 'lokale_km', 'GPS'
        )
        spoortak_transformer = spoortak_transformer.fit(spoortak_gdf)
        input_df = pd.DataFrame({'spoortak_id': ['A'], 'lokale_km': [0.5]})

        output_df = spoortak_transformer.transform(input_df)

        expected_output = pd.DataFrame(
            {
                'spoortak_id': ['A'],
                'lokale_km': [0.5],
                'x': [3.33287],
                'y': [47.993]
            }
        )

        pd.testing.assert_frame_equal(output_df, expected_output)
