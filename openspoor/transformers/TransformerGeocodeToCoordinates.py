import pandas as pd

from ..utils.common import read_config
from ..utils.safe_requests import SafeRequest

config = read_config()


class TransformerGeocodeToCoordinates:
    """
    Transforms dataframes with geocode kilometer information to contain
    coordinates, either Rijksdriehoek or GPS.
    """

    def __init__(
        self, geocode_column: str, geocode_km_column: str, coordinate_system
    ):
        """
        Parameters
        ----------
        geocode_column : str
            Name of the geocode column.
        geocode_km_column : str
            Name of the geocode kilometer column.
        coordinate_system : str
            The coordinate system in which to return the coordinates
            (Rijksdriehoek or GPS).
        """

        self.mapservices_url = config["mapservices_url"]
        self.geocode = geocode_column
        self.geocode_km = geocode_km_column
        if coordinate_system == "Rijksdriehoek":
            self.coordinates = "coordinatesRD"
        elif coordinate_system == "GPS":
            self.coordinates = "coordinatesWGS"
        else:
            raise ValueError("coordinate_system is unknown")

    def fit(self):
        """
        Fit method is redundant but included for consistency
        with other Transformers.

        Returns
        -------
        self
            The instance itself.
        """
        return self

    def transform(self, df: pd.DataFrame):
        """
        Adds x and y columns to a Pandas DataFrame based on
        `self.coordinate_system`.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame containing `self.geocode` and `self.geocode_km` columns.

        Returns
        -------
        pandas.DataFrame
            DataFrame with added x and y coordinate columns.
        """
        # These steps preserve the original types of the dataframe
        original_index = df.index
        original_geocode_values = df[self.geocode]

        df[self.geocode] = df[self.geocode].apply(lambda x: str(x).zfill(3))
        xy_information = self._geocode_naar_xy(df)

        df_with_xy = df.merge(
            xy_information, how="left", on=[self.geocode, self.geocode_km]
        )

        df_with_xy.index = original_index
        df_with_xy[self.geocode] = original_geocode_values
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

        response_json = SafeRequest().get_json(
            "GET", self.mapservices_url, input_json
        )
        return self._transform_xy_json_to_df(response_json)

    def _make_json_for_geocode_to_xy_api(self, input_df):
        """
        Prepares `input_df` for use as JSON input in the
        `self.mapservices_url` call.

        Parameters
        ----------
        input_df : pandas.DataFrame
            DataFrame containing `self.geocode` and `self.geocode_km` columns.

        Returns
        -------
        dict
            Dictionary formatted for the API request.
        """
        km_list_grouped_per_geocode = (
            input_df.groupby(self.geocode)[self.geocode_km]
            .apply(lambda x: list(set(x)))
            .reset_index()
        )

        def make_feature_dict(row):
            return {
                "geocode": row[self.geocode],
                "geometry": {
                    "type": "Point",
                    "coordinatesRD": [0, 0],
                    "coordinatesWGS": [0, 0],
                },
                "properties": {"punten": row[self.geocode_km]},
            }

        return {
            "name": "JSONFeature",
            "type": "GeocodePunten",
            "features": list(
                km_list_grouped_per_geocode.apply(make_feature_dict, axis=1)
            ),
        }

    def _transform_xy_json_to_df(self, api_response_json):
        """
        Transforms JSON output from `self.mapservices_url`
        into a Pandas DataFrame.

        Parameters
        ----------
        api_response_json : dict
            Dictionary obtained from `self.mapservices_url`.

        Returns
        -------
        pandas.DataFrame
            DataFrame containing geocode and x, y coordinate information.
        """
        features_series = pd.Series(api_response_json["features"])
        geocode_series = features_series.apply(
            lambda dictionary: dictionary["geocode"]
        )
        geocode_km_series = features_series.apply(
            lambda dictionary: dictionary["properties"]["punten"][0]
        )

        x_series = features_series.apply(
            lambda dictionary: dictionary["geometry"][self.coordinates][0]
        )
        x_series = x_series.astype(float)

        y_series = features_series.apply(
            lambda dictionary: dictionary["geometry"][self.coordinates][1]
        )
        y_series = y_series.astype(float)

        return pd.DataFrame(
            {
                self.geocode: geocode_series,
                self.geocode_km: geocode_km_series,
                "x": x_series,
                "y": y_series,
            }
        )
