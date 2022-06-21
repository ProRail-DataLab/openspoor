import pandas as pd
from ..utils.safe_requests import  SafeRequest
from ..utils.common import read_config

config = read_config()


class TransformerGeocodeToCoordinates:
    """
    Transforms dataframes with geocode kilometer information to contain
    coordinates, either Rijksdriehoek or GPS.
    """

    def __init__(self, geocode_column: str, geocode_km_column: str,
                 coordinate_system):
        """
        :param geocode_column: Name of the geocode column
        :param geocode_km_column: Name of the geocode kilometer column
        :param coordinate_system: In which coordinate system to return the
                                  coordinates. (Rijksdriehoek or GPS)
        """

        self.mapservices_url = config['mapservices_url']
        self.geocode = geocode_column
        self.geocode_km = geocode_km_column
        if coordinate_system == 'Rijksdriehoek':
            self.coordinates = 'coordinatesRD'
        elif coordinate_system == 'GPS':
            self.coordinates = 'coordinatesWGS'
        else:
            raise ValueError("coordinate_system is unknown")

    def fit(self):
        """
        Fit is redundant here, but is here to be consistent with other
        Transformers
        :return: self
        """
        return self

    def transform(self, df: pd.DataFrame):
        """
        Takes a Pandas dataframe with geocode and geocode_km columns and adds x
        and y columns, corresponding to self.coordinate_system.

        :param df: A pandas dataframe with self.geocode and self.geocode_km
                   columns.
        :return: A pandas dataframe with x, y coordinate columns
        """
        xy_information = self._geocode_naar_xy(df)

        # The index steps are required to keep the index of df
        index = df.index
        df_with_xy = df.merge(xy_information, how='left',
                              on=[self.geocode, self.geocode_km])
        df_with_xy.index = index

        return df_with_xy

    def _geocode_naar_xy(self, input_df):
        """
        Use the ProRail mapservices to get a dataframe listing all geocode
        kilometer with their matching xy coordinates

        :param input_df: pandas dataframe containing self.geocode and
                         self.geocode_km column
        :return: A dataframe, with columns with geocode location and
                 coordinates.
        """
        input_json = self._make_json_for_geocode_to_xy_api(input_df)

        response_json = SafeRequest().get_json('GET', self.mapservices_url, input_json)
        return self._transform_xy_json_to_df(response_json)

    def _make_json_for_geocode_to_xy_api(self, input_df):
        """
        Prepares input_df to be used as json input for the self.mapservices_url
        call.

        :param input_df: pandas dataframe with self.geocode and self.geocode_km
                         columns
        :return: dictionary
        """
        km_list_grouped_per_geocode = \
            input_df.groupby(self.geocode)[self.geocode_km]\
            .apply(lambda x: list(set(x))).reset_index()

        def make_feature_dict(row):
            return {"geocode": row[self.geocode],
                    "geometry": {"type": "Point",
                                 "coordinatesRD": [0, 0],
                                 "coordinatesWGS": [0, 0]},
                    "properties": {"punten": row[self.geocode_km]}}

        return {
            "name": "JSONFeature", "type": "GeocodePunten",
            "features": list(
                km_list_grouped_per_geocode.apply(make_feature_dict, axis=1)
            )
        }

    def _transform_xy_json_to_df(self, api_response_json):
        """
        Transforms json output of self.mapservices_url into a dataframe

        :param api_response_json: dictionary as from self.mapservices_url
        :return: pandas dataframe with geocode and x, y information
        """
        features_series = pd.Series(api_response_json['features'])
        geocode_series = features_series.apply(
            lambda dictionary: dictionary['geocode']
        )
        geocode_km_series = features_series.apply(
            lambda dictionary: dictionary['properties']['punten'][0]
        )

        x_series = features_series.apply(
            lambda dictionary: dictionary['geometry'][self.coordinates][0]
        )
        x_series = x_series.astype(float)

        y_series = features_series.apply(
            lambda dictionary: dictionary['geometry'][self.coordinates][1]
        )
        y_series = y_series.astype(float)

        return pd.DataFrame(
            {self.geocode: geocode_series, self.geocode_km: geocode_km_series,
             'x': x_series, 'y': y_series}
        )
