import pandas as pd
import re
from loguru import logger
from pathlib import Path
import geopandas as gpd

from ..utils.safe_requests import SafeRequest
from openspoor.mapservices.MapservicesQuery import MapServicesQuery
from openspoor.utils.singleton import Singleton


class FeatureSearchResults(pd.DataFrame):

    def load_data(self, entry_number: int = 0, return_m: bool = False) -> gpd.GeoDataFrame:
        """
        Prepare the data for analysis

        :param entry_number: The row giving the url to query
        :param return_m : Whether to return m values (used in some layers)
        :return: A geopandas dataframe
        """
        if len(self) <= entry_number:
            logger.warning("No results found")
            raise IndexError("Invalid entry requested")

        url = self.layer_url.values[entry_number]

        return MapServicesQuery(url, return_m=return_m).load_data()

    def write_gpkg(self, output_dir: Path, entry_number: int = 0) -> None:
        """
        Write the data at the requested url to a local file directory

        :param entry_number: The entry in the dataframe to write
        :param output_dir: The directory which to write to
        :return: None, a file is written in the indicated
        """

        output_gdf = self.load_data(entry_number)
        description = self.description.values[entry_number]

        output_folder = Path(output_dir)
        output_folder.mkdir(exist_ok=True)
        output_gdf.to_file(output_folder / f"{description.replace(' ', '_')}.gpkg", driver='GPKG')
        return output_gdf


class FeatureServerOverview(Singleton):
    """
    Class used to find all the available featureservers in mapservices.
    This can be used to navigate the API through python, allowing some more efficient searching.
    """
    def __init__(self):
        self.prefix = 'https://mapservices.prorail.nl/'
        self.base_url = "https://mapservices.prorail.nl/arcgis/rest/services"
        self.df = None
        self.search_results = None

    def _get_layers_in_featureservers(self, featureserver_url: str) -> pd.DataFrame:
        """
        For a given featureserver submenu within the mapservices environment give all the possible layers.

        :param featureserver_url: The url of the selected featureserver
        :return: A pandas dataframe, listing the urls and descriptions of the found layers
        """
        featureserver_text = SafeRequest().get_string('GET', featureserver_url)
        featureservers = re.findall(r'href="/(.+)">(.+)</a> \(\d+\)', featureserver_text)
        featureservers = [[f'{self.prefix}{fs}', description] for fs, description in featureservers]
        return pd.DataFrame(featureservers, columns=['layer_url', 'description'])

    def get_all_featureserver_layers(self) -> pd.DataFrame:
        """
        Find all available layers within the mapservices featureservers.

        :return: A pandas dataframe, listing the urls and descriptions of the found layers in all featureservers
        """
        all_services = SafeRequest().get_string('GET', self.base_url)
        featureserver_redirects = re.findall(r'href="/(.+/FeatureServer)"', all_services)

        featureserver_urls = [f'{self.prefix}{redirect}' for redirect in featureserver_redirects]
        return (
            pd.concat(self._get_layers_in_featureservers(url) for url in featureserver_urls)
            .assign(server=lambda d: d.layer_url.str.split('/').str[-3].str.split("_").str[0])
            .assign(version=lambda d: d.layer_url.str.split('/').str[-3].str.split("_").str[1])
            .drop_duplicates(['description', 'server'], keep='last')
            .reset_index(drop=True)
        )

    def search_for(self, search_for: str, exact: bool = False) -> pd.DataFrame:
        """
        Find all layers which include a certain phrase.

        :param search_for: A case unsensitive string for which you want to find all available layers
        :param exact: Whether to only return layers that match this string completely
        :return: A pandas dataframe, listing the urls and descriptions of the found layers in all featureservers
        """

        if self.df is None:
            logger.info(f'Retrieving featureserver layers')
            self.df = self.get_all_featureserver_layers()
        logger.info(f'Searching for "{search_for}"')
        if exact:
            return FeatureSearchResults(
                self.df.loc[lambda d: d.description.str.lower() == search_for.lower()]
            )
        else:
            return FeatureSearchResults(
                self.df.loc[lambda d: d.description.str.lower().str.contains(search_for.lower())]
            )
