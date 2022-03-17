from openspoor.transformers import TransformerGeocodeToCoordinates
import pandas as pd


class Test:
    def test_make_json_for_geocode_to_xy_api(self):
        geocode_transformer = TransformerGeocodeToCoordinates(
            geocode_column='Geocode', geocode_km_column='geocode_km',
            coordinate_system='Rijksdriehoek'
        )
        input_data = pd.DataFrame(
            data={'Geocode': ['112', '112', '112', '009', '009', '009'],
                  'geocode_km': [77, 76, 77, 115.208, 115.183, 115.208],
                  'some_data': ['a', 'b', 'c', 'd', 'e', 'f']},
            index=[66, 11, 55, 44, 33, 22])
        result_json = geocode_transformer._make_json_for_geocode_to_xy_api(
            input_data
        )
        expected_json = {
            'name': 'JSONFeature', 'type': 'GeocodePunten',
            'features': [{'geocode': '009',
                          'geometry': {
                              'type': 'Point',
                              'coordinatesRD': [0, 0],
                              'coordinatesWGS': [0, 0]
                          },
                          'properties': {'punten': [115.183, 115.208]}
                          },
                         {'geocode': '112',
                          'geometry': {
                              'type': 'Point',
                              'coordinatesRD': [0, 0],
                              'coordinatesWGS': [0, 0]
                          },
                          'properties': {'punten': [76.0, 77.0]}
                          }]
        }

        assert result_json == expected_json

    def test_transform_xy_json_to_df_rd_sample(self):
        geocode_transformer = TransformerGeocodeToCoordinates(
            geocode_column='Geocode', geocode_km_column='geocode_km',
            coordinate_system='Rijksdriehoek'
        )
        input_json = {
            'features': [{'geocode': 'A',
                          'properties': {'punten': [123]},
                          'geometry': {'coordinatesRD': ['2.0', '3.1']}
                          },
                         {'geocode': 'A',
                          'properties': {'punten': [456]},
                          'geometry': {'coordinatesRD': ['13.0', '10.1']}
                          },
                         {'geocode': 'B',
                          'properties': {'punten': [333]},
                          'geometry': {'coordinatesRD': ['5.0', '333.1']}
                          }
                         ]
        }

        output_df = geocode_transformer._transform_xy_json_to_df(input_json)

        expected_df = pd.DataFrame({'Geocode': ['A', 'A', 'B'],
                                    'geocode_km': [123, 456, 333],
                                    'x': [2.0, 13.0, 5.0],
                                    'y': [3.1, 10.1, 333.1]})

        pd.testing.assert_frame_equal(output_df, expected_df)

    def test_transform_xy_json_to_df_gps_sample(self):
        geocode_transformer = TransformerGeocodeToCoordinates(
            geocode_column='Geocode', geocode_km_column='geocode_km',
            coordinate_system='GPS'
        )
        input_json = {
            'features': [{'geocode': 'A',
                          'properties': {'punten': [123]},
                          'geometry': {'coordinatesWGS': ['2.0', '3.1']}}]}

        output_df = geocode_transformer._transform_xy_json_to_df(input_json)

        expected_df = pd.DataFrame({'Geocode': ['A'],
                                    'geocode_km': [123],
                                    'x': [2.0],
                                    'y': [3.1]})

        pd.testing.assert_frame_equal(output_df, expected_df)
