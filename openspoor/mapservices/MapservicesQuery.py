import os
import pickle
import re
from pathlib import Path
from typing import List, Optional, Union

import geopandas as gpd
import pandas as pd
from loguru import logger
from shapely import GeometryCollection
from shapely.geometry import LineString, MultiLineString, Point, shape

from ..utils.common import read_config
from ..utils.safe_requests import SafeRequest

config = read_config()


class MapServicesQuery:
    """
    Class to allow easy access to mapservices.prorail.nl. Mainly used as
    abstract parent class to other mapservices classes
    """

    def __init__(self, url: str, cache_location: Optional[Path] = None):
        """
        Downloads data from a specified ProRail map services FeatureServer.

        Parameters
        ----------
        url : str
            The URL of the FeatureServer to download from. This should be
            the part of the URL up to `/query?`, e.g.,
            `https://mapservices.prorail.nl/arcgis/rest/services/Geleidingssysteem_007/FeatureServer/12`.
        cache_location : str
            The file path where the pickle file of the data will be loaded from
            (or saved to if the file is absent).
        """

        self.standard_featureserver_query = config[
            "standard_featureserver_query"
        ]
        self.url = url
        self.crs = config["crs"]
        self.cache_location = cache_location

    def load_data(self) -> gpd.GeoDataFrame:
        """
        If there is a self.cache_location then attempts to return from
        pickle file, otherwise it downloads data and (if there is a
        self.cache_location) pickles the data.
        """
        if self.cache_location:
            if os.path.exists(self.cache_location):
                with open(self.cache_location, "rb") as infile:
                    all_data_gdf = pickle.load(infile)
            else:
                all_data_gdf = self._load_all_features_to_gdf()
                with open(self.cache_location, "wb") as outfile:
                    pickle.dump(all_data_gdf, outfile)
        else:
            all_data_gdf = self._load_all_features_to_gdf()

        return all_data_gdf

    @staticmethod
    def _get_query_url(dict_query: dict) -> str:
        """
        Creates a query URL from the given dictionary to filter data
        from the FeatureServer.

        Parameters
        ----------
        dict_query : dict
            A dictionary containing filter parameters for the query.

        Returns
        -------
        str
            The constructed query URL
        """
        if dict_query is None:
            where_query = "/query?"
        else:
            value_types = [type(k) for k in dict_query.values()]
            where_query = "/query?where="
            for i in range(len(list(dict_query.values()))):
                if value_types[i] == list:
                    where_query = where_query + "%28"
                    for val in range(len(list(dict_query.values())[i])):
                        where_query = (
                            where_query
                            + list(dict_query.keys())[i]
                            + "+%3D+%27"
                            + list(dict_query.values())[i][val]
                            + "%27+or+"
                        )
                    where_query = where_query[:-4] + "%29+and+"
                else:
                    where_query = (
                        where_query
                        + list(dict_query.keys())[i]
                        + "+%3D+%27"
                        + list(dict_query.values())[i]
                        + "%27+and+"
                    )
            where_query = where_query[:-5] + "&"

        return where_query

    def _get_max_recordcount(self, url: str) -> int:
        """
        Retrieves the maximum record count from the given URL.

        Parameters
        ----------
        url : str
            The base URL for the FeatureServer.

        Returns
        -------
        int
            The maximum record count.
        """
        body = (
            SafeRequest()._request_with_retry("GET", url).data.decode("UTF-8")
        )
        try:
            return int(re.findall(r"MaxRecordCount: </b> (\d+)", str(body))[0])
        except IndexError:
            raise ValueError("MaxRecordCount not found in response")

    def _load_all_features_to_gdf(
        self, dict_query=None
    ) -> Union[gpd.GeoDataFrame, pd.DataFrame]:
        """
        Downloads all available features from a FeatureServer and
        sets the correct geometry.

        Parameters
        ----------
        dict_query : dict
            A dictionary containing filter criteria.
            - Keys represent column names.
            - Multiple columns and multiple values per column are supported.

        Returns
        -------
        GeoDataFrame
            A GeoPandas DataFrame containing all data retrieved
            from the API call.
        """

        where_query = self._get_query_url(dict_query)

        input_url = self.url + where_query + self.standard_featureserver_query
        total_features_count = self._retrieve_max_features_count(input_url)
        output_gdf = pd.DataFrame({})
        logger.info(
            "Initiate downloading "
            + str(total_features_count)
            + " of features."
        )

        # Maxrecordcount is either 1000 or 2000. For bigger sets,
        # it is not worth the extra request to check the max recordcount
        if total_features_count > 2000:
            recordcount = self._get_max_recordcount(self.url)
        else:
            recordcount = 1000

        logger.info("Load data with api call: " + input_url)
        for features_offset in range(0, total_features_count, recordcount):
            temp_m_gdf = self._retrieve_batch_of_features_to_gdf(
                input_url, features_offset
            )
            output_gdf = pd.concat([output_gdf, temp_m_gdf], ignore_index=True)

        return output_gdf

    @staticmethod
    def _retrieve_max_features_count(input_url: str) -> int:
        """
        Retrieves the total number of features from the given URL.

        Parameters
        ----------
        input_url : str
            The base URL for the features.

        Returns
        -------
        int
            The total number of features available.
        """
        res = SafeRequest().get_json(
            "GET", input_url + "&returnCountOnly=True"
        )
        # some layers do not return geojson when asking for the count only
        # i.e.: 'https://mapservices.prorail.nl/
        # arcgis/rest/services/Kadastraal_004/MapServer/5'
        if "properties" not in res.keys():
            return res["count"]
        return res["properties"]["count"]

    def _retrieve_batch_of_features_to_gdf(
        self, input_url: str, offset: int
    ) -> Union[gpd.GeoDataFrame, pd.DataFrame]:
        """
        Retrieves a batch of features from the given URL.

        Since API calls can return a maximum of 1000 features per request,
        the offset parameter is used to retrieve data in batches of 1000.

        Parameters
        ----------
        input_url : str
            The URL to query data from.
        offset : int
            The offset value, starting from 0, used to retrieve different
            batches from the same API.

        Returns
        -------
        GeoDataFrame
            A GeoPandas DataFrame containing the retrieved features.
        """
        data = SafeRequest().get_json(
            "GET", input_url + "&resultOffset=" + str(offset)
        )
        temp_gdf = self._transform_dict_to_gdf(data)
        logger.info("Downloaded " + str(offset + len(temp_gdf)) + " features")
        return temp_gdf

    def _transform_dict_to_gdf(
        self, data: dict
    ) -> Union[gpd.GeoDataFrame, pd.DataFrame]:
        """
        Transforms JSON-formatted data from FeatureServers into a GeoPandas
        DataFrame with geometry.

        Parameters
        ----------
        data : dict
            A dictionary containing JSON-formatted data retrieved from the
            FeatureServer at map_services.prorail.nl.

        Returns
        -------
        GeoDataFrame or DataFrame
            A GeoPandas DataFrame if geometry is present,
            otherwise a Pandas DataFrame.
        """
        geometry_list = [
            (
                shape(feature["geometry"])
                if feature["geometry"] is not None
                else GeometryCollection()
            )
            for feature in data["features"]
        ]
        attribute_list = [
            feature["properties"] for feature in data["features"]
        ]

        if all(
            isinstance(geom, GeometryCollection) and geom.is_empty
            for geom in geometry_list
        ):
            return pd.DataFrame(data=attribute_list)

        return gpd.GeoDataFrame(
            data=attribute_list, geometry=geometry_list, crs=self.crs
        )


class MapServicesQueryMValues(MapServicesQuery):
    """
    Class for getting M-values from the mapservices.prorail.nl feature servers.
    Unfortunately these are in json format only, so the standard query needs
    to be adjusted for this.
    """

    def __init__(self, url: str, cache_location: Optional[Path] = None):
        super().__init__(url, cache_location)
        if not self._has_m_values():
            logger.warning(
                "This layer does not have M values, for this layer "
                "MapServicesQuery should be used. "
                f"See {url} for more information"
            )

        self.standard_featureserver_query = (
            self.standard_featureserver_query.replace("f=geojson", "f=json")
            + "&returnM=true&returnZ=false"
        )

    def _has_m_values(self):
        body = SafeRequest()._request_with_retry("GET", self.url)._body
        hasmvalues = re.findall(r"HasM: (\w+)", str(body))[0]
        return hasmvalues == "true"

    def _transform_dict_to_gdf(self, data: dict) -> gpd.GeoDataFrame:
        """
        Transforms JSON-formatted data from feature servers into a
        GeoPandas DataFrame.

        Parameters
        ----------
        data : dict
            JSON-formatted dictionary as retrieved from the feature server at
            map_services.prorail.nl.

        Returns
        -------
        geopandas.GeoDataFrame or pandas.DataFrame
            A GeoDataFrame with geometry if applicable, otherwise a
            Pandas DataFrame.
        """
        attribute_list = [
            feature["attributes"] for feature in data["features"]
        ]
        if data["geometryType"] == "esriGeometryPolyline":
            geometry_list: List[Union[LineString, Point, MultiLineString]] = []
            for feature in data[
                "features"
            ]:  # Sometimes there are multiple paths in one feature.
                # These can be combined within the same geometry column
                if len(feature["geometry"]["paths"]) > 1:
                    geometry_list.append(
                        MultiLineString(
                            [
                                LineString([tuple(p) for p in path])
                                for path in feature["geometry"]["paths"]
                            ]
                        )
                    )
                else:
                    geometry_list.append(
                        LineString(
                            [tuple(p) for p in feature["geometry"]["paths"][0]]
                        )
                    )
        elif data["geometryType"] == "esriGeometryPoint":
            logger.warning(
                "Requested m values for point geometry, "
                "these are not relevant for these layers"
            )
            geometry_list = [
                Point((f["geometry"])["x"], (f["geometry"])["y"])
                for f in data["features"]
            ]
        else:
            geometrytype = data["geometryType"]
            raise NotImplementedError(
                "Requesting m values for this geometry type: "
                f"({geometrytype}) is not yet implemented"
            )
        return gpd.GeoDataFrame(
            data=attribute_list, crs=self.crs, geometry=geometry_list
        )
