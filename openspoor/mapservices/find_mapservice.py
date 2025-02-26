import re
from functools import cache
from pathlib import Path

import geopandas as gpd
import pandas as pd
from loguru import logger

from openspoor.mapservices.MapservicesQuery import (
    MapServicesQuery,
    MapServicesQueryMValues,
)
from openspoor.utils.singleton import Singleton

from ..utils.safe_requests import SafeRequest


class FeatureSearchResults(pd.DataFrame):

    def load_data(
        self, entry_number: int = 0, return_m: bool = False
    ) -> gpd.GeoDataFrame:
        """
        Prepares the data for analysis.

        Parameters
        ----------
        entry_number : int
            The row index containing the URL to query.
        return_m : bool, optional
            Whether to return M values (used in some layers). Default is False.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing the processed data.
        """
        if len(self) <= entry_number:
            logger.warning("No results found")
            raise IndexError("Invalid entry requested")

        url = self.layer_url.values[entry_number]

        if not return_m:
            return MapServicesQuery(url).load_data()
        else:
            return MapServicesQueryMValues(url).load_data()

    def write_gpkg(
        self, output_dir: Path, entry_number: int = 0
    ) -> gpd.GeoDataFrame:
        """
        Writes the data at the requested URL to a local file directory.

        Parameters
        ----------
        entry_number : int
            The entry in the DataFrame to write.
        output_dir : str
            The directory to which the file will be written.

        Returns
        -------
        None
            A file is written in the specified directory.
        """

        output_gdf = self.load_data(entry_number)
        description = self.description.values[entry_number]

        output_folder = Path(output_dir)
        output_folder.mkdir(exist_ok=True)
        output_gdf.to_file(
            output_folder / f"{description.replace(' ', '_')}.gpkg",
            driver="GPKG",
        )
        return output_gdf


class FeatureServerOverview(Singleton):
    """
    Class used to find all the available featureservers in mapservices.
    This can be used to navigate the API through python, allowing some more
    efficient searching.
    """

    def __init__(self):
        self.prefix = "https://mapservices.prorail.nl/"
        self.base_url = "https://mapservices.prorail.nl/arcgis/rest/services"
        self.df = None
        self.search_results = None

    def _get_layers_in_featureservers(
        self, featureserver_url: str
    ) -> pd.DataFrame:
        """
        Retrieves all possible layers from a given FeatureServer submenu
        within the map services environment.

        Parameters
        ----------
        featureserver_url : str
            The URL of the selected FeatureServer.

        Returns
        -------
        DataFrame
            A pandas DataFrame listing the URLs and descriptions
            of the found layers.
        """
        featureserver_text = SafeRequest().get_string("GET", featureserver_url)
        featureservers = re.findall(
            r'href="/(.+)">(.+)</a> \(\d+\)', featureserver_text
        )
        featureservers = [
            [f"{self.prefix}{fs}", description]
            for fs, description in featureservers
        ]
        return pd.DataFrame(
            featureservers, columns=["layer_url", "description"]
        )

    @cache
    def get_all_featureserver_layers(self) -> pd.DataFrame:
        """
        Finds all available layers within the map services FeatureServers.

        Returns
        -------
        DataFrame
            A pandas DataFrame listing the URLs and descriptions of
            the found layers in all FeatureServers.
        """
        all_services = SafeRequest().get_string("GET", self.base_url)
        featureserver_redirects = re.findall(
            r'href="/(.+/FeatureServer)"', all_services
        )

        featureserver_urls = [
            f"{self.prefix}{redirect}" for redirect in featureserver_redirects
        ]
        return (
            pd.concat(
                self._get_layers_in_featureservers(url)
                for url in featureserver_urls
            )
            .assign(
                server=lambda d: d.layer_url.str.split("/")
                .str[-3]
                .str.split("_")
                .str[0]
            )
            .assign(
                version=lambda d: d.layer_url.str.split("/")
                .str[-3]
                .str.split("_")
                .str[1]
            )
            .drop_duplicates(["description", "server"], keep="last")
            .reset_index(drop=True)
        )

    def search_for(
        self, search_for: str, exact: bool = False
    ) -> FeatureSearchResults:
        """
        Finds all layers that include a specified phrase.

        Parameters
        ----------
        search_for : str
            A case-insensitive string used to search for matching layers.
        exact : bool, optional
            Whether to return only layers that match the string exactly.
            Default is False.

        Returns
        -------
        FeatureSearchResults
            A pandas DataFrame listing the URLs and descriptions of
            the found layers in all FeatureServers.
        """

        if self.df is None:
            logger.info("Retrieving featureserver layers")
            self.df = self.get_all_featureserver_layers()
        logger.info(f'Searching for "{search_for}"')
        if exact:
            return FeatureSearchResults(
                self.df.loc[
                    lambda d: d.description.str.lower() == search_for.lower()
                ]
            )
        else:
            return FeatureSearchResults(
                self.df.loc[
                    lambda d: d.description.str.lower().str.contains(
                        search_for.lower()
                    )
                ]
            )
