from loguru import logger
from .MapservicesData import MapservicesData
from ..utils.common import read_config

config = read_config()

class SpoortakMapservices(MapservicesData):
    """
    Loads mapservices data from the Spoortakken. These contain Spoortak_
    identificatie and geometry and therefore lokale kilometrering.
    """
    def __init__(self, cache_location=None):
        """
        :param cache_location: filepath as in MapservicesData class
        """
        logger.info('Initiating SpoortakMapservices object in order to obtain '
                    'spoortak data from mapservices api.')

        MapservicesData.__init__(self, cache_location=cache_location)

        self.spoortakken_url = config['spoor_url']

    def _download_data(self):
        """
        Downloads data from self.spoortakken_url
        """
        return self._load_all_features_to_gdf(self.spoortakken_url, None)
