import pandas as pd
import geopandas as gpd
from loguru import logger
from ..utils.map_services_requests import secure_map_services_request
from ..utils.common import read_config

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
        self.spoortak_gdf = None
        self.polygons_gdf = None
        self.xy_to_geocode_url = config['xy_to_geocode_url']
        self.crs = config['crs']

    def fit(self, puic_gdf, spoortak_gdf):
        """
        Fits input geopandas dataframes, such that the lines in puic_gdf rows
        are surounded with a polygon at distance self.buffer_distance. This is
        to allow small errors when matching coordinates to the lines in
        polygons_gdf.

        :param puic_gdf: geopandas dataframe containing data as from
                         PUICMapservices object
        :param spoortak_gdf: geopandas dataframe containing data as from
                             SpoortakMapservices object
        """
        self.spoortak_gdf = spoortak_gdf

        polygons_gdf = puic_gdf.copy()

        polygons_gdf.geometry = polygons_gdf.geometry.buffer(
            self.buffer_distance, cap_style=2
        )
        self.polygons_gdf = polygons_gdf[
            [
                "SPOOR_ID",
                "SPOOR_PUIC",
                "GEOCODE_NR",
                "GEOSUBCODE",
                "Type",
                "PRORAIL_GEBIED",
                "geometry",
            ]
        ]
        return self

    def transform(self, points_gdf):
        """
        This function checks if xy coordinates are on a puic based on the
        geometry and adds columns from this puic to the given coordinates.
        Only distances of maximally self.buffer_distance between puic and xy
        coordinate are considered. Then the specific kilometrerings belonging
        to the coordinate are added.

        Note that points_gdf must be in the correct crs. epsg:28992 for
        Rijksdriehoek and epsg:4326 for GPS.

        :param points_gdf: geopandas dataframe containing at the minimum xy
                           coordinates.
        :return: return_gdf: geopandas dataframe, input_points_gdf with
                             additional columns from puic added
        """
        logger.info(
            "Transforming coordinates to include Geocode, Geocode "
            "kilometrering, Spoortak_identificatie and "
            "lokale kilometrering"
        )

        if len(points_gdf) == 1:
            one_point = True
        else:
            one_point = False

        coordinate_points_gdf = points_gdf.copy().to_crs(self.crs)

        coordinate_gdf = gpd.sjoin(
            coordinate_points_gdf, self.polygons_gdf, how="left", op="within"
        )
        # sjoin leaves an unwanted index_right column and some duplicates
        # might appear due to redudancy in polygons_gdf
        coordinate_gdf = coordinate_gdf.drop(["index_right"], axis=1).drop_duplicates()

        matched_index = coordinate_gdf["SPOOR_ID"].notnull()
        if len(coordinate_gdf[~matched_index]) > 0:
            logger.warning(
                "No spoortak matched for \n"
                + str(coordinate_gdf[~matched_index][["x", "y"]])
            )

        # Geocode kilometrering is determined for every geosubcode/index combination to account for intersecting tracks
        geocode_kilometrering_df = self._get_geo_km_as_df(
            coordinate_gdf[matched_index], one_point=one_point
        )
        coordinate_gdf = coordinate_gdf.reset_index()
        coordinate_df = coordinate_gdf.merge(
            geocode_kilometrering_df, on=["GEOSUBCODE", "index"], how="left"
        )
        coordinate_gdf = gpd.GeoDataFrame(coordinate_df).set_index("index")

        # Lokale kilometrering is determined for every geocode_kilometrering/index combination to account for
        # intersecting tracks
        lokale_kilometrering_df = self._get_lokale_kilometrering_as_df(
            coordinate_gdf[matched_index]
        )
        coordinate_gdf = coordinate_gdf.reset_index()
        # When there are multiple points in the input_gdf, the geosubcode and spoor_id sometimes are not unique.
        # Therefore, the 'index' column has to be added in the merge to attach correct lokale kilometrering to the
        # corresponding geocode_kilometrering
        coordinate_df = coordinate_gdf.merge(
            lokale_kilometrering_df, on=["GEOSUBCODE", "index", "SPOOR_ID"], how="left"
        )
        coordinate_gdf = gpd.GeoDataFrame(coordinate_df)

        # Final merge is necessary to ensure duplicates of x, y in original
        # points_gdf are kept
        return_gdf = points_gdf.merge(
            coordinate_gdf, how="left", on=["x", "y"], suffixes=("", "_coordinate")
        )
        return_gdf = return_gdf[
            [col for col in return_gdf.columns if col != "geometry_coordinate"]
        ]
        return return_gdf

    def _get_geo_km_as_df(self, input_df, one_point):
        """
        Get the geocode kilometrering for the XY coordinates in input_df.

        :param input_df: geopandas dataframe containing an x and y column with
                         those respective values
        :return: pandas df, containing the Geocode_KM per geosubcode and the index corresponding to input df
        """
        input_json = self._prep_dictionary_for_mapservices_call(input_df)
        response_json = secure_map_services_request(self.xy_to_geocode_url, input_json)
        return self._transform_json_to_km_dataframe(response_json, one_point=one_point)

    @staticmethod
    def _prep_dictionary_for_mapservices_call(df):
        """
        Prepare a dictionary so it can function as json input for the
        mapservices call to retrieve data about XY points.

        :param df: pandas dataframe with 'x' and 'y' column of coordinates in
                   rijksdriehoek. Index must be unique.
        :return: dictionary for mapservices call
        """

        def make_features_json(row):
            return {
                "geometry": {
                    "coordinates": [row["geometry"].x, row["geometry"].y],
                    "type": "Point",
                },
                "properties": {"FID": str(row.name)},
                "type": "Feature",
            }

        json_dict = {
            "features": list(df.apply(make_features_json, axis=1)),
            "name": "RD_Coordinaten",
            "type": "FeatureCollection",
        }
        return json_dict

    @staticmethod
    def _transform_json_to_km_dataframe(json_dict, one_point=False):
        """
        Transforms dictionary output from api call to dataframe with correct
        index and km value.

        :param json_dict: dictionary as output given by api call to xy to km url
        :return: df, pandas dataframe with km value at correct index
        """

        geosubcode_list = sorted(
            list(
                set(
                    [unit["properties"]["GEOSUBCODE"] for unit in json_dict["features"]]
                )
            )
        )
        if one_point & (len(geosubcode_list) > 1):
            logger.warning(
                "BE AWARE: There are spoortakken in multiple geocodes at this single location! "
                "The geocodes that are considered are: " + str(sorted(geosubcode_list))
            )

        df_list = []
        for geosubcode in geosubcode_list:
            km_out = [
                unit["properties"]["KM_GEOCODE"]
                for unit in json_dict["features"]
                if unit.get("properties")["GEOSUBCODE"] == geosubcode
            ]
            index = [
                int(unit["properties"]["FID"])
                for unit in json_dict["features"]
                if unit.get("properties")["GEOSUBCODE"] == geosubcode
            ]
            df = pd.DataFrame(
                {
                    "geocode_kilometrering": km_out,
                    "GEOSUBCODE": geosubcode,
                    "index": index,
                }
            )
            df_list.append(df)
        df = pd.concat(df_list)
        df["geocode_kilometrering"] = (
            df["geocode_kilometrering"].str.replace(",", ".").astype(float)
        )
        # When multiple equal points are added, there can be duplicates in df. Since we perform a merge in the next
        # step, these duplicates can be dropped.
        df = df.drop_duplicates(ignore_index=True)
        return df

    def _get_lokale_kilometrering_as_df(self, input_df):
        """
        Returns lokale kilometrering of points in input_df as series. Only
        those indices with a lokale kilometrering are returned.

        NOTE: Only returns lokale kilometrering voor spoor, not for wissels
        and kruisingbenen.

        :param input_df: geopandas dataframe with point geometry and SPOOR_ID
                         column with Spoortak_identification
        :return: pandas series of lokale kilometrering
        """
        # TODO: add wissels/kruisingbenen also as lokale kilometering optie
        #  reset_indexing and setting_index is necessary to keep the input_df
        #  index during merge
        input_df_with_spoortak = input_df.reset_index()
        input_df_with_spoortak = input_df_with_spoortak.merge(
            self.spoortak_gdf[
                ["NAAM_LANG", "GEOSUBCODE", "PRORAIL_GEBIED", "geometry"]
            ],
            how="inner",
            left_on=["SPOOR_ID", "GEOSUBCODE", "PRORAIL_GEBIED"],
            right_on=["NAAM_LANG", "GEOSUBCODE", "PRORAIL_GEBIED"],
            suffixes=("_point", "_spoortak"),
        )
        input_df_with_spoortak = input_df_with_spoortak.set_index("index")
        input_df_with_spoortak.index.name = None
        input_df_with_spoortak["lokale_kilometrering"] = input_df_with_spoortak.apply(
            lambda row: row["geometry_spoortak"].project(row["geometry_point"]) / 1000
            if row["geometry_spoortak"] is not None
            else None,
            axis=1,
        )
        return input_df_with_spoortak[
            ["GEOSUBCODE", "SPOOR_ID", "lokale_kilometrering"]
        ].reset_index()
