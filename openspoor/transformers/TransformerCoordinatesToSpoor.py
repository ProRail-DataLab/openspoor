import numpy as np
import geopandas as gpd
from loguru import logger
from functools import lru_cache

from openspoor.utils.common import read_config
from openspoor.mapservices import FeatureServerOverview

config = read_config()


class TransformerCoordinatesToSpoor:
    """
    Transforms coordinates (Rijksdriehoek or GPS) to spoortak, PUIC and Geocode
    with geocode kilometrering and lokale kilometrering

    """

    def __init__(self, buffer_distance=1.2):
        """
        :param buffer_distance: float, max distance in meters used to
                                pinpoint points to spoor referential systems
        """
        logger.info(
            "Initiating TransformerCoordinatesToSpoor object in order to "
            "transform between various ProRail spoor coordinate systems"
        )

        self.buffer_distance = buffer_distance
        self.stgk = self._get_spoortak_met_geokm()
        # Buffer style prevents overflow into next segment; buffer has straight edges at the end
        self.buffered_stgk = self.stgk.assign(geometry=lambda x: x.geometry.buffer(self.buffer_distance, cap_style=2))

    @lru_cache
    def _get_spoortak_met_geokm(self):
        return FeatureServerOverview().search_for('Spoortakdeel met geocode kilometrering') \
            .load_data(return_m=True)

    @staticmethod
    def _determine_geocode_km(gdf_lines, gdf_points):
        """
        Perform the interpolation for a set of line segments and points. Index indicates which lines and points are
        compared.

        :param gdf_lines: A geodataframe with line data
        :param gdf_points: A geodataframe with point data.
        :return: A set of distances for every line to the specified points.
        """
        return (gdf_lines
                .assign(distances=lambda d: d.geometry.project(gdf_points.loc[d.index]))
                .pipe(lambda d: d.interpolate(d.distances).z))

    # TODO: Fix for wissels. These seem to be a in a separate table: 'Spoorwisselbenaming met geocode kilometrering'
    def transform(self, gdf_points: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        For every requested point, check which track segments are close to that location and add them to the data.
        This can result in 0,1 or more matches per point. Every point will occur in the final output at least once, even
        if no match could be made.

        :param gdf_points: A geodataframe with points data for which the geocode and spoortak coordinates are wanted.
        All crs are allowed
        :return: A geodataframe, based on the input dataframe. Every point will occur in the final output at least once,
         even if no match could be made.
        """
        # Coordinates used are RD in the below.
        starting_crs = gdf_points.crs
        gdf_points = gdf_points.to_crs('EPSG:28992')
        close_geocodes = self.buffered_stgk.sjoin(gdf_points)

        points_geocodes = (
            self.stgk.loc[close_geocodes.index]
            .set_index(close_geocodes['index_right'])  # Sample only the list of matching hits
            .assign(geocode_kilometrering=lambda d: self._determine_geocode_km(d, gdf_points))
            .drop(['geometry'], axis=1)
        )

        return (
            gdf_points
            .join(points_geocodes)
            .loc[lambda d: (d.KM_GEOCODE_VAN.isnull()) |
                           ((d.geocode_kilometrering >= d[['KM_GEOCODE_VAN', 'KM_GEOCODE_TOT']].min(axis=1) - 0.0012) &
                            (d.geocode_kilometrering <= d[['KM_GEOCODE_VAN', 'KM_GEOCODE_TOT']].max(axis=1) + 0.0012))]
            .assign(geocode_kilometrering=lambda d: d.groupby(  # This ensures a unique geocode within every segment
                [d.geometry.astype(str),
                 'GEOCODE', 'SUBCODE', 'NAAM_LANG'])['geocode_kilometrering']
                    .transform(np.mean))
            .reset_index()  # Below makes sure every original point is projected, even if the data contained duplicates
            .drop_duplicates()
            .set_index('index')
            .rename_axis(None)
            .to_crs(starting_crs)
        )
