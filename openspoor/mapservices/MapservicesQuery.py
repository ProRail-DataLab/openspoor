import os
import pandas as pd
import geopandas as gpd
from typing import Optional
from pathlib import Path
from loguru import logger
from shapely.geometry import Point, LineString, Polygon
import pickle

from ..utils.safe_requests import SafeRequest
from ..utils.common import read_config

config = read_config()


class MapServicesQuery:
    """
    Class to allow easy access to mapservices.prorail.nl. Mainly used as
    abstract parent class to other mapservices classes
    """

    def __init__(self, url: Optional[str] = None, cache_location: Optional[Path] = None, return_m=False):
        """
        :param url: An url of a mapservices.prorail.nl feature server to download from.
                this is the part of the url until /query?
                e.g. https://mapservices.prorail.nl/arcgis/rest/services/Geleidingssysteem_007/FeatureServer/12
        :param cache_location: filepath where pickle file of data will be loaded from (or saved to if file is absent)
        """

        self.standard_featureserver_query = config['standard_featureserver_query'] + \
                                            ('&returnM=true&returnZ=false' if return_m else '')
        self.url = url
        self.crs = config['crs']
        self.cache_location = cache_location

    def load_data(self):
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
    def _get_query_url(dict_query):
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

    def _load_all_features_to_gdf(self, dict_query=None):
        """
        Downloads all available features from a feature server and set correct
        geometry.

        :param dict_query: dictionary with data to filter. keys are column names.
                more than one column are possible and also more than one value for each column
        :return: geopandas dataframe with all data from the api call
        """

        where_query = self._get_query_url(dict_query)

        input_url = self.url + where_query + self.standard_featureserver_query
        logger.info("Load data with api call: " + input_url)
        total_features_count = self._retrieve_max_features_count(input_url)
        output_gdf = pd.DataFrame({})
        logger.info("Initiate downloading " + str(total_features_count) +
                    " of features.")

        # Loop per 1000 features, as feature servers return max 1000 per call
        for features_offset in range(0, total_features_count, 1000):
            temp_gdf = self._retrieve_batch_of_features_to_gdf(input_url, features_offset)
            output_gdf = pd.concat([output_gdf, temp_gdf], ignore_index=True)

        return output_gdf

    @staticmethod
    def _retrieve_max_features_count(input_url):
        """
        Retrieve the total number of features of the given input url.

        :param input_url: string, base_url for features
        :return: int, max_features_count
        """
        return SafeRequest().get_json('GET', input_url + "&returnCountOnly=True")['count']

    def _retrieve_batch_of_features_to_gdf(self, input_url, offset):
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

    def _transform_dict_to_gdf(self, data):
        """
        Transform given json format data from feature servers into a geopandas
        dataframe with given geometry.

        :param data: dictionary, json format as retrieved from feature server
        map_services.prorail.nl
        :return: geopandas dataframe
        """
        attribute_list = [feature['attributes'] for feature in data['features']]
        if data['geometryType'] == 'esriGeometryPoint':
            geometry_list = [Point((f['geometry'])['x'], (f['geometry'])['y'])
                             for f in data['features']]
        elif data['geometryType'] == 'esriGeometryPolyline':
            geometry_list = [LineString([tuple(p) for p in
                                         f['geometry']['paths'][0]])
                             for f in data['features']]
        elif data['geometryType'] == 'esriGeometryPolygon':
            geometry_list = [Polygon([tuple(p) for p in
                                      f['geometry']['rings'][0]])
                             for f in data['features']]
        else:
            raise Exception('Incorrect data format returned')

        return gpd.GeoDataFrame(data=attribute_list, crs=self.crs,
                                geometry=geometry_list)
