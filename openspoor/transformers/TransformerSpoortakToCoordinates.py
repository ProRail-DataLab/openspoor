import pandas as pd
import geopandas as gpd


class TransformerSpoortakToCoordinates:
    """
    Transforms dataframes with spoortak and lokale kilometrering information to
    contain coordinates, either Rijksdriehoek or GPS.
    """

    def __init__(self, spoortak_column: str, lokale_km_column: str
                 , coordinate_system):
        """
        :param spoortak_column: Name of the spoortak column
        :param lokale_km_column: Name of the lokale kilometrering column
        :param coordinate_system: In which coordinate system to return the
                                  coordinates. (Rijksdriehoek or GPS)
        """
        self.spoortak = spoortak_column
        self.lokale_km = lokale_km_column
        if coordinate_system == 'Rijksdriehoek':
            self.crs = 'epsg:28992'
        elif coordinate_system == 'GPS':
            self.crs = 'epsg:4326'
        else:
            raise ValueError("coordinate_system is unknown")

        self.spoortak_gdf = None

    def fit(self, spoortak_gdf):
        """
        Adds spoortak_gdf to self

        :param spoortak_gdf: geopandas dataframe containing data as from
                             SpoortakMapservices object
        :return: self
        """
        self.spoortak_gdf = spoortak_gdf
        return self

    def transform(self, df: pd.DataFrame):
        """
        Takes a Pandas dataframe with spoortak and lokale_km columns and adds x
        and y columns, corresponding to self.coordinate_system.

        :param df: A pandas dataframe with self.spoortak and self.lokale_km
                   columns.
        :return: A pandas dataframe with x, y information
        """
        df_with_spoortak_info = df.merge(
            self.spoortak_gdf, how='left', left_on=[self.spoortak],
            right_on=['NAAM_LANG']
        )
        geometry = gpd.GeoSeries(
            df_with_spoortak_info.apply(
                lambda row: row['geometry'].interpolate(
                    row[self.lokale_km] * 1000
                ),
                axis=1
            ),
            crs=self.spoortak_gdf.crs
        )
        geometry = geometry.to_crs(self.crs)
        df_with_xy = df.copy()
        df_with_xy['x'] = geometry.centroid.x
        df_with_xy['y'] = geometry.centroid.y
        return df_with_xy
