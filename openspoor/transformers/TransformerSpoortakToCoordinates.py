import geopandas as gpd
import pandas as pd


class TransformerSpoortakToCoordinates:
    """
    Transforms dataframes with spoortak and lokale kilometrering information to
    contain coordinates, either Rijksdriehoek or GPS.
    """

    def __init__(
        self, spoortak_column: str, lokale_km_column: str, coordinate_system
    ):
        """
        Parameters
        ----------
        spoortak_column : str
            Name of the spoortak column.
        lokale_km_column : str
            Name of the lokale kilometrering column.
        coordinate_system : str
            The coordinate system in which to return the coordinates
            (Rijksdriehoek or GPS).
        """
        self.spoortak = spoortak_column
        self.lokale_km = lokale_km_column
        if coordinate_system == "Rijksdriehoek":
            self.crs = "epsg:28992"
        elif coordinate_system == "GPS":
            self.crs = "epsg:4326"
        else:
            raise ValueError("coordinate_system is unknown")

        self.spoortak_gdf = None

    def fit(self, spoortak_gdf):
        """
        Adds `spoortak_gdf` to `self`.

        Parameters
        ----------
        spoortak_gdf : geopandas.GeoDataFrame
            GeoDataFrame containing data from the SpoortakMapservices object.

        Returns
        -------
        self
            The updated instance of the class.
        """
        self.spoortak_gdf = spoortak_gdf
        return self

    def transform(self, df: pd.DataFrame):
        """
        Adds x and y columns to a Pandas DataFrame based on
        `self.coordinate_system`.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame containing `self.spoortak` and `self.lokale_km` columns.

        Returns
        -------
        pandas.DataFrame
            DataFrame with added x and y coordinate columns.
        """
        if not isinstance(self.spoortak_gdf, gpd.GeoDataFrame):
            raise ValueError("No spoortak_gdf is set. Use fit method first.")

        df_with_spoortak_info = df.merge(
            self.spoortak_gdf,
            how="left",
            left_on=[self.spoortak],
            right_on=["NAAM_LANG"],
        )
        geometry = gpd.GeoSeries(
            df_with_spoortak_info.apply(
                lambda row: row["geometry"].interpolate(
                    row[self.lokale_km] * 1000
                ),
                axis=1,
            ),
            crs=self.spoortak_gdf.crs,
        )

        geometry = geometry.to_crs(self.crs)
        df_with_xy = df.copy()
        df_with_xy["x"] = geometry.centroid.x
        df_with_xy["y"] = geometry.centroid.y
        return df_with_xy
