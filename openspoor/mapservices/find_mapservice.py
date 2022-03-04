import requests
import pandas as pd
import re


class FeatureServerOverview:
    def __init__(self):
        self.prefix = 'https://mapservices.prorail.nl/'
        self.base_url = "https://mapservices.prorail.nl/arcgis/rest/services"
        self.df = self.get_all_featureserver_layers()

    def _get_layers_in_featureservers(self, featureserver_url):
        featureserver_page = requests.get(featureserver_url)

        featureserver_text = featureserver_page.text
        featureservers = re.findall(r'href="/(.+)">(.+)</a> \(\d+\)', featureserver_text)
        featureservers = [[f'{self.prefix}{fs}', description] for fs, description in featureservers]
        return pd.DataFrame(featureservers, columns=['layer_url', 'description'])

    def get_all_featureserver_layers(self):
        all_services = requests.get(self.base_url).text
        featureserver_redirects = re.findall(r'href="/(.+/FeatureServer)"', all_services)

        featureserver_urls = [f'{self.prefix}{redirect}' for redirect in featureserver_redirects]
        return (
            pd.concat(self._get_layers_in_featureservers(url) for url in featureserver_urls)
            .drop_duplicates('description', keep='last') # Keep only the most recent data
            .reset_index(drop=True)
        )

    def search_for(self, search_for):
        return self.df.loc[lambda d: d.description.str.lower().str.contains(search_for.lower())]
