import pandas as pd
from loguru import logger
from .MapservicesData import MapservicesData
from ..utils.common import read_config

config = read_config()

class PUICMapservices(MapservicesData):
    """
    Loads mapservices data from the Geleidingssystemen. These contains PUIC data for spoor, wissels and kruisingbenen.
    """
    def __init__(self, cache_location=None):
        """
        :param cache_location: filepath as in MapservicesData class
        """
        logger.info('Initiating PUICMapservices object in order to obtain '
                    'spoor, wissel and kruisingbeen data from '
                    'Geleidingsystemen mapservices api.')

        MapservicesData.__init__(self, cache_location)

        self.spoor_url = config['spoor_url']

        self.wisselkruisingbeen_url = config['wisselkruisingbeen_url']

        self.spoordata_columns = config['spoordata_columns']


    def _download_data(self):
        """
        Return combined spoortak, wissel and kruising data from
        self.spoor_url and self.wisselkruisingbeen_url
        """
        spoor_gdf = self._load_all_features_to_gdf(self.spoor_url, None)
        spoor_gdf = self._prep_spoor_gdf(spoor_gdf)

        wisselkruisingbeen_gdf = self._load_all_features_to_gdf(
            self.wisselkruisingbeen_url, None
        )
        wisselkruisingbeen_gdf = self._prep_wisselkruisingbeen_gdf(
            wisselkruisingbeen_gdf
        )

        return self._combine_spoor_and_wisselkruisingbeen(
            spoor_gdf, wisselkruisingbeen_gdf
        )

    def _combine_spoor_and_wisselkruisingbeen(self, spoor_gdf,
                                              wisselkruisingbeen_gdf):
        """
        Combine the spoor_gdf with the wisselkruisingbeen_gdf with correct
        columns
        """
        all_data_gdf = pd.concat([spoor_gdf, wisselkruisingbeen_gdf], sort=True)
        all_data_gdf = all_data_gdf.filter(self.spoordata_columns)
        return all_data_gdf.reset_index(drop=True)

    @staticmethod
    def _prep_spoor_gdf(gdf):
        """"
        Prepare spoor_gdf with correct column names.
        """
        spoor_gdf = gdf.loc[gdf['NAAM_LANG'].notnull()]
        spoor_gdf = spoor_gdf.rename(
            {'NAAM_LANG': 'SPOOR_ID', 'REF_FYS_SPOORTAK_PUIC': 'SPOOR_PUIC'},
            axis=1
        )
        spoor_gdf['Type'] = 'Spoortak'
        return spoor_gdf

    @staticmethod
    def _prep_wisselkruisingbeen_gdf(gdf):
        """"
        Prepare wisselbenen and kruisingbenen in  wisselkruisingbeen_gdf with
        correct columns and column names.
        """
        wk_gdf = gdf.rename(
            {'REF_WISSEL_KRUISING_PUIC': 'SPOOR_PUIC',
             'TYPE_WISSELKRUISINGBEEN': 'Type'
             },
            axis=1
        )
        wk_gdf = wk_gdf[wk_gdf['Type'].isin(['Wisselbeen', 'Kruisingbeen'])]
        wk_gdf['SPOOR_ID'] = wk_gdf['REF_WISSEL_KRUISING_NAAM'].astype(str)

        wk_gdf.loc[wk_gdf['Type'] == 'Wisselbeen', 'SPOOR_ID'] = \
            wk_gdf['GEOCODE'].astype(str) + "_" + wk_gdf['SPOOR_ID']

        return wk_gdf