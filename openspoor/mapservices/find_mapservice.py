import requests
import pandas as pd
import re


class FeatureServerOverview:
    """
    Class used to find all the available featureservers in mapservices.
    This can be used to navigate the API through python, allowing some more efficient searching.
    """
    def __init__(self):
        self.prefix = 'https://mapservices.prorail.nl/'
        self.base_url = "https://mapservices.prorail.nl/arcgis/rest/services"
        self.df = self.get_all_featureserver_layers()

    def _get_layers_in_featureservers(self, featureserver_url: str) -> pd.DataFrame:
        """
        For a given featureserver submenu within the mapservices environment give all the possible layers.

        :param featureserver_url: The url of the selected featureserver
        :return: A pandas dataframe, listing the urls and descriptions of the found layers
        """
        featureserver_page = requests.get(featureserver_url)

        featureserver_text = featureserver_page.text
        featureservers = re.findall(r'href="/(.+)">(.+)</a> \(\d+\)', featureserver_text)
        featureservers = [[f'{self.prefix}{fs}', description] for fs, description in featureservers]
        return pd.DataFrame(featureservers, columns=['layer_url', 'description'])

    def get_all_featureserver_layers(self) -> pd.DataFrame:
        """
        Find all available layers within the mapservices featureservers.

        :return: A pandas dataframe, listing the urls and descriptions of the found layers in all featureservers
        """
        all_services = requests.get(self.base_url).text
        featureserver_redirects = re.findall(r'href="/(.+/FeatureServer)"', all_services)

        featureserver_urls = [f'{self.prefix}{redirect}' for redirect in featureserver_redirects]
        return (
            pd.concat(self._get_layers_in_featureservers(url) for url in featureserver_urls)
            .drop_duplicates('description', keep='last') # Keep only the most recent data
            .reset_index(drop=True)
        )

    def search_for(self, search_for: str) -> pd.DataFrame:
        """
        Find all layers which include a certain phrase.

        :param search_for: A case unsensitive string for which you want to find all available layers
        :return: A pandas dataframe, listing the urls and descriptions of the found layers in all featureservers
        """
        return self.df.loc[lambda d: d.description.str.lower().str.contains(search_for.lower())]
