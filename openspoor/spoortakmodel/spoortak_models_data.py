import os
from glob import glob
from os.path import basename, join

import numpy as np
from typing import Optional
import logging
import pandas as pd

from openspoor.utils.singleton import Singleton

log = logging.getLogger(__name__)


class SpoortakModelsData(Singleton):
    """ Helper class that loads spoortak model data (only once)

    Improvement backlog:
    - Support V18 (spoortak 2.0)
    """

    models: dict = None
    model_changes: dict = None

    @staticmethod
    def _convert_dutch_number(value: str) -> float:
        """ '55.132,56' => 55132.56"""
        if not value:
            return np.nan
        return float(value.replace('.', '').replace(',', '.'))

    @staticmethod
    def _km_to_meters(km: float) -> float:
        if km is None or np.isnan(km):
            return np.nan
        return km * 1000.0

    @staticmethod
    def _replace_km_columns(df: pd.DataFrame) -> None:
        """ implace correction of the km columns and renaming them to avoid confusion """
        """TO DO: if km column are swapped, GEOCODE_BEGIN en GEOCODE_EIND must be swapped"""
        df['kilometrering_start'] = df[['KM_BEGIN', 'KM_EIND']].values.min(1)
        df['kilometrering_end'] = df[['KM_BEGIN', 'KM_EIND']].values.max(1)

        df_changed = df[df['kilometrering_start'] != df['KM_BEGIN']]
        df_changed_geo = df_changed[df_changed['GEOCODE_BEGIN'] != df_changed['GEOCODE_EIND']]

        # for spoortak, row in df_changed_geo.iterrows():
        #     log.warning(
        #         f'Swapped from & two km for {spoortak} with different geocodes. This might actualy be a different kilometerlint and thus have incorrect results.')

        df.drop(columns=['KM_BEGIN', 'KM_EIND'], inplace=True)

    @staticmethod
    def _replace_km_columns_new(df: pd.DataFrame) -> None:
        """ implace correction of the km columns and renaming them to avoid confusion """
        df['kilometrering_start'] = df[['GEOCODE_KM_VAN', 'GEOCODE_KM_TOT']].values.min(1)*1000
        df['kilometrering_end'] = df[['GEOCODE_KM_VAN', 'GEOCODE_KM_TOT']].values.max(1)*1000

        df.drop(columns=['GEOCODE_KM_VAN', 'GEOCODE_KM_TOT'], inplace=True)

    @staticmethod
    def _get_model_numbers(data_path: str) -> [int]:
        """ Return the available model numbers
        converts ".../Version_17", ".../Version_18" to 17, 18
        """
        dirs = glob(join(data_path, 'Versie_*'))

        return [int(basename(directory).split('_')[1]) for directory in dirs]

    def __init__(self, data_path: str):
        # we've applied the singleton pattern here so we can check if the data is already there.
        if not self.models:
            log.info('loading data...')

            self.models = dict()
            self.new_models = dict()
            self.new_models_map = dict()

            self.model_version_numbers = self._get_model_numbers(data_path)
            unsupported_version_start = 18
            self.new_style_model_versions = [version for version in self.model_version_numbers if
                                          version >= unsupported_version_start]
            self.model_version_numbers_old = [version for version in self.model_version_numbers if
                                          version < unsupported_version_start]
            
            try:
                self.map_v2 = pd.read_csv(os.path.join(data_path,
                                                       'BBMS_MAPPING_SPOORTAK_SEGMENT_BOTH_18_RICHTING.csv'),
                                                       delimiter=';',
                                                       header=0,
                                                       index_col='NEW_SEGMENT',
                                                       encoding='latin1',)
            except ValueError:
                log.error(f'Failed to read mapping v2 tabel')
                raise


            try:
                for model_version in self.model_version_numbers_old:
                    self.models[model_version] = pd.read_csv(os.path.join(data_path,
                                                                          f'Versie_{model_version:02d}',
                                                                          f'SPOORTAK_{model_version}.csv'),
                                                             delimiter=';',
                                                             header=0,
                                                             converters={
                                                                 'KM_BEGIN': lambda km: self._km_to_meters(
                                                                     self._convert_dutch_number(km)),
                                                                 'KM_EIND': lambda km: self._km_to_meters(
                                                                     self._convert_dutch_number(km)),
                                                                 'LENGTE': lambda km: self._km_to_meters(
                                                                     self._convert_dutch_number(
                                                                         km))
                                                             },
                                                             index_col='SPOORTAK_IDENTIFICATIE',
                                                             encoding='latin1',
                                                             )

                    self._replace_km_columns(self.models[model_version])
            except ValueError:
                log.error(f'Failed to read model {model_version}')
                raise

            try:
                for model_version in self.new_style_model_versions:
                    #TODO: Deze inleesfunctie moet compleet anders
                    self.new_models[model_version] = pd.read_csv(os.path.join(data_path,
                                                                          f'Versie_{model_version:02d}',
                                                                          f'BBMS_SEGMENT_{model_version}.csv'),
                                                             delimiter=';',
                                                             header=0,
                                                             converters={
                                                                 'KM_BEGIN': lambda km: self._km_to_meters(
                                                                     self._convert_dutch_number(km)),
                                                                 'KM_EIND': lambda km: self._km_to_meters(
                                                                     self._convert_dutch_number(km)),
                                                                 'LENGTE': lambda km: self._km_to_meters(
                                                                     self._convert_dutch_number(
                                                                         km))
                                                             },
                                                             index_col=None,
                                                             encoding='latin1',
                                                             )

                    self._replace_km_columns_new(self.new_models[model_version])
                    
                    self.new_models_map[model_version] = pd.merge(self.map_v2, self.new_models[model_version],
                                                                          left_on='NEW_SEGMENT', 
                                                                          right_on='SEGMENT_IDENTIFICATIE')
                    #self.new_models_map[model_version].set_index("OLD_SEGMENT", inplace = True)
                    
                                                              
            except ValueError:
                log.error(f'Failed to read model {model_version}')
                raise

            
            self.model_changes = {
                model_version: pd.read_csv(
                    os.path.join(data_path, f'Versie_{model_version:02d}', f'BBMS_BERICHT_{model_version}.csv'),
                    delimiter=';',
                    header=0,
                    encoding='latin1'
                )
                for model_version in self.model_version_numbers_old
            }

            self.model_changes_v2 = {
                model_version: pd.merge(pd.read_csv(
                    os.path.join(data_path, f'Versie_{model_version:02d}', f'BBMS_BERICHT_{model_version}.csv'),
                    delimiter=';',
                    header=0,
                    encoding='latin1'
                ),self.new_models[model_version][['kilometrering_start', 'kilometrering_end', 
                                                  'GEOCODE', 'NAAM', 'SEGMENT_IDENTIFICATIE']], 
                                                  left_on='NEW_SEGMENT', 
                                                                          right_on='SEGMENT_IDENTIFICATIE')
                for model_version in self.new_style_model_versions if model_version != 18

            }

            self.model_changes_v2_oud = {
                            model_version: pd.merge(pd.read_csv(
                                os.path.join(data_path, f'Versie_{model_version:02d}', f'BBMS_BERICHT_{model_version}.csv'),
                                delimiter=';',
                                header=0,
                                encoding='latin1'
                            ),self.new_models[model_version-1][['kilometrering_start', 'kilometrering_end', 
                                                            'GEOCODE', 'NAAM', 'SEGMENT_IDENTIFICATIE']], 
                                                            left_on='OLD_SEGMENT', 
                                                                                    right_on='SEGMENT_IDENTIFICATIE')
                            for model_version in self.new_style_model_versions if model_version != 18

                        }
