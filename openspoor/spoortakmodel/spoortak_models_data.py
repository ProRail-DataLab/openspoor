import os

import numpy as np
from typing import Optional
import logging

import pandas as pd

from ..spoortakmodel.singleton import Singleton

log = logging.getLogger(__name__)


class SpoortakModelsData(Singleton):
    """ Helper class that loads spoortak model data (only once)

    Improvement backlog:
    - Auto scan for available model version
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
    def _km_to_meters(km: float) -> Optional[int]:
        if km is None or np.isnan(km):
            return None
        return int(km * 1000)

    def __init__(self, data_path: str):
        # we've applied the singleton pattern here so we can check if the data is already there.
        if not self.models:
            print('loading data...')

            self.models = dict()

            # supported models
            self.model_start = 3
            self.model_end = 17

            try:
                for i in range(self.model_start, self.model_end + 1):
                    self.models[i] = pd.read_csv(os.path.join(data_path,
                                                              f'Versie_{i:02d}/SPOORTAK_{i}.csv'),
                                                 delimiter=';',
                                                 header=0,
                                                 converters={
                                                     'KM_BEGIN': lambda km: self._km_to_meters(
                                                         self._convert_dutch_number(km)),
                                                     'KM_EIND': lambda km: self._km_to_meters(
                                                         self._convert_dutch_number(km)),
                                                     'LENGTE': lambda km: self._km_to_meters(
                                                         self._convert_dutch_number(km))
                                                 },
                                                 encoding='latin1'
                                                 )
            except ValueError:
                log.error(f'Failed to read model {i}')
                raise

            # might have been an issue with dutch numbers, and perhaps we dont need to make this consistant
            #       for model_version, model in self.models.items():
            #         # to avoid problems where the KM_EIND < KM_BEGIN we sort them
            #         model['kilometrering_from'] = model[['KM_BEGIN','KM_EIND']].min(axis=1)
            #         model['kilometrering_to'] = model[['KM_BEGIN','KM_EIND']].max(axis=1)

            # missing bericht data were supplied by Maaike Geurts
            self.model_changes = {
                i: pd.read_csv(os.path.join(data_path, f'Versie_{i:02d}/BBMS_BERICHT_{i}.csv'),
                               delimiter=';',
                               header=0,
                               encoding='latin1'
                               )
                for i in range(self.model_start, self.model_end + 1)
            }
