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
        df['kilometrering_start'] = df[['KM_BEGIN', 'KM_EIND']].values.min(1)
        df['kilometrering_end'] = df[['KM_BEGIN', 'KM_EIND']].values.max(1)

        df_changed = df[df['kilometrering_start'] != df['KM_BEGIN']]
        df_changed_geo = df_changed[df_changed['GEOCODE_BEGIN'] != df_changed['GEOCODE_EIND']]

        for spoortak, row in df_changed_geo.iterrows():
            log.warning(
                f'Swapped from & two km for {spoortak} with different geocodes. This might actualy be a different kilometerlint and thus have incorrect results.')

        df.drop(columns=['KM_BEGIN', 'KM_EIND'], inplace=True)

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

            self.model_version_numbers = self._get_model_numbers(data_path)
            unsupported_version_start = 18
            self.model_version_numbers = [version for version in self.model_version_numbers if
                                          version < unsupported_version_start]

            try:
                for model_version in self.model_version_numbers:
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

            self.model_changes = {
                model_version: pd.read_csv(
                    os.path.join(data_path, f'Versie_{model_version:02d}', f'BBMS_BERICHT_{model_version}.csv'),
                    delimiter=';',
                    header=0,
                    encoding='latin1'
                )
                for model_version in self.model_version_numbers
            }
