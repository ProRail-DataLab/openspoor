import os
import pandas as pd
import geopandas as gpd
from typing import Optional
from pathlib import Path
from loguru import logger
import pickle
import re
from shapely.geometry import shape, Point, LineString, MultiLineString

from ..utils.safe_requests import SafeRequest
from ..utils.common import read_config

config = read_config()


class MapServicesQuery:
    """
    Class to allow easy access to mapservices.prorail.nl. Mainly used as
    abstract parent class to other mapservices classes
    """

    # def __init__(self, url: Optional[str] = None, cache_location: Optional[Path] = None):
    def __init__(self, url: str, cache_location: Optional[Path] = None):
        """
        :param url: An url of a mapservices.prorail.nl feature server to download from.
                this is the part of the url until /query?
                e.g. https://mapservices.prorail.nl/arcgis/rest/services/Geleidingssysteem_007/FeatureServer/12
        :param cache_location: filepath where pickle file of data will be loaded from (or saved to if file is absent)
        """

        self.standard_featureserver_query = config['standard_featureserver_query']
        self.url = url
        self.crs = config['crs']
        self.cache_location = cache_location

    def load_data(self) -> gpd.GeoDataFrame:
        """
        If there is a self.cache_location then attempts to return from
        pickle file, otherwise it downloads data and (if there is a
        self.cache_location) pickles the data.
        """
        if self.cache_location:
            if os.path.exists(self.cache_location):
                with open(self.cache_location, 'rb') as infile:
                    all_data_gdf = pickle.load(infile)
            else:
                all_data_gdf = self._load_all_features_to_gdf()
                with open(self.cache_location, 'wb') as outfile:
                    pickle.dump(all_data_gdf, outfile)
        else:
            all_data_gdf = self._load_all_features_to_gdf()

        return all_data_gdf

    @staticmethod
    def _get_query_url(dict_query: dict) -> str:
        """
        Create the query url from the given dictionary. This is used to filter
        the data from the feature server.

        :param dict_query: dictionary with filters.
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
                        where_query = where_query + list(dict_query.keys())[i] + "+%3D+%27" + \
                                      list(dict_query.values())[i][val] + "%27+or+"
                    where_query = where_query[:-4] + "%29+and+"
                else:
                    where_query = where_query + list(dict_query.keys())[i] + "+%3D+%27" + \
                                  list(dict_query.values())[
                                      i] + "%27+and+"
            where_query = where_query[:-5] + "&"

        return where_query
    
    def _get_max_recordcount(self, url: str) -> int:
        """
        Retrieve the max record count from the given url.

        :param url: string, base_url for features
        :return: int, max_record_count        
        """
        body = SafeRequest()._request_with_retry('GET', url)._body
        try:
            return int(re.findall(r'MaxRecordCount: </b> (\d+)', str(body))[0])
        except:
            raise ValueError("MaxRecordCount not found in response")

    def _load_all_features_to_gdf(self, dict_query=None) -> gpd.GeoDataFrame:
        """
        Downloads all available features from a feature server and set correct
        geometry.

        :param dict_query: dictionary with data to filter. keys are column names.
                more than one column are possible and also more than one value for each column
        :return: geopandas dataframe with all data from the api call
        """

        where_query = self._get_query_url(dict_query)

        input_url = self.url + where_query + self.standard_featureserver_query
        total_features_count = self._retrieve_max_features_count(input_url)
        output_gdf = pd.DataFrame({})
        logger.info("Initiate downloading " + str(total_features_count) +
                    " of features.")
        
        # Maxrecordcount is either 1000 or 2000. For bigger sets, it is not worth the extra request to check the max recordcount        
        if total_features_count > 2000:
            recordcount = self._get_max_recordcount(self.url)
        else:
            recordcount = 1000

        logger.info("Load data with api call: " + input_url)
        for features_offset in range(0, total_features_count, recordcount):
            temp_m_gdf = self._retrieve_batch_of_features_to_gdf(input_url, features_offset)
            output_gdf = pd.concat([output_gdf, temp_m_gdf], ignore_index=True)

        return output_gdf

    @staticmethod
    def _retrieve_max_features_count(input_url: str) -> int:
        """
        Retrieve the total number of features of the given input url.

        :param input_url: string, base_url for features
        :return: int, max_features_count
        """
        res = SafeRequest().get_json('GET', input_url + "&returnCountOnly=True")
        # some layers do not return geojson when asking for the count only
        # i.e.: 'https://mapservices.prorail.nl/arcgis/rest/services/Kadastraal_004/MapServer/5'
        if 'properties' not in res.keys():
            return res['count']
        return res['properties']['count']

    def _retrieve_batch_of_features_to_gdf(self, input_url: str, offset: int) -> gpd.GeoDataFrame:
        """
        Retrieve a batch of features from the url. As api calls can
        retrieve a maximum of 1000 features, the offset is used to retrieve
        batches by 1000 at a time.

        :param input_url: The url to query data from
        :param offset: int, offset from 0 to retrieve different batches from the
        same api
        :return: geopandas dataframe of features
        """
        data = SafeRequest().get_json('GET', input_url + "&resultOffset=" + str(offset))
        temp_gdf = self._transform_dict_to_gdf(data)
        logger.info("Downloaded " + str(offset + len(temp_gdf)) + " features")
        return temp_gdf

    def _transform_dict_to_gdf(self, data: dict) -> gpd.GeoDataFrame:
        """
        Transform given json format data from feature servers into a geopandas
        dataframe with given geometry.

        :param data: dictionary, json format as retrieved from feature server
        map_services.prorail.nl
        :return: geopandas dataframe with geometry or pandas dataframe without
        """
        geometry_list = [
            shape(feature['geometry']) if feature['geometry'] is not None else None 
            for feature in data['features']]
        attribute_list = [feature['properties'] for feature in data['features']]
        if all(geometry is None for geometry in geometry_list):
            return pd.DataFrame(data=attribute_list)
        return gpd.GeoDataFrame(data=attribute_list, geometry=geometry_list, crs=self.crs)

        
class MapServicesQueryMValues(MapServicesQuery):
    """
    Class for getting M-values from the mapservices.prorail.nl feature servers.
    Unfortunately these are in json format only, so the standard query needs to be adjusted for this.    
    """

    def __init__(self, url: str, cache_location: Optional[Path] = None):
        super().__init__(url, cache_location)
        if not self._has_m_values():
            logger.warning("This layer does not have M values, for this layer MapServicesQuery should be used. "\
                           f"See {url} for more information")
                           
        self.standard_featureserver_query = self.standard_featureserver_query.replace('f=geojson', 'f=json') + \
                                            '&returnM=true&returnZ=false'
        
    def _has_m_values(self):
        body = SafeRequest()._request_with_retry('GET', self.url)._body
        hasmvalues = re.findall(r'HasM: (\w+)', str(body))[0]
        return hasmvalues == 'true'

    def _transform_dict_to_gdf(self, data: dict) -> gpd.GeoDataFrame:
        """
        Transform given json format data from feature servers into a geopandas
        dataframe with given geometry.

        :param data: dictionary, json format as retrieved from feature server
        map_services.prorail.nl
        :return: geopandas dataframe with geometry or pandas dataframe without
        """
        attribute_list = [feature['attributes'] for feature in data['features']]
        if data['geometryType'] == 'esriGeometryPolyline':
            geometry_list = []
            for feature in data['features']:  # Sometimes there are multiple paths in one feature. These can be combined within the same geometry column
                if len(feature['geometry']['paths']) > 1:
                    geometry_list.append(MultiLineString([LineString([tuple(p) for p in path]) for path in feature['geometry']['paths']]))
                else:
                    geometry_list.append(LineString([tuple(p) for p in feature['geometry']['paths'][0]]))
        elif data['geometryType'] == 'esriGeometryPoint':
            logger.warning("Requested m values for point geometry, these are not relevant for these layers")
            geometry_list = [Point((f['geometry'])['x'], (f['geometry'])['y'])
                            for f in data['features']]
        else:
            geometrytype = data['geometryType']
            raise NotImplementedError(f"Requesting m values for this geometry type: ({geometrytype}) is not yet implemented")
        return gpd.GeoDataFrame(data=attribute_list, crs=self.crs,
                            geometry=geometry_list)
