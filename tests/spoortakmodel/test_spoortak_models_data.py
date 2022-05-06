import os
import pathlib
import unittest

import pytest

from openspoor.spoortakmodel import SpoortakModelsData

MODELS_DATA_DIR = str(pathlib.Path(__file__).parents[2].resolve().joinpath('data').resolve())


class TestSpoortakModelsData(unittest.TestCase):
    def test_data_dir_exists(self):
        """ Test that the data directory exists and is accesable"""
        self.assertTrue(os.path.exists(MODELS_DATA_DIR), f'{MODELS_DATA_DIR} does not exist')

    def test_basic_load_test(self):
        sut = SpoortakModelsData(MODELS_DATA_DIR)

        self.assertGreaterEqual(15, len(sut.models))
        self.assertGreaterEqual(15, len(sut.model_changes))

    def test_data_unique_spoortak(self):
        """ This is a data integrity test"""
        sut = SpoortakModelsData(MODELS_DATA_DIR)
        self.assertFalse(any(any(model.index.duplicated()) for model in sut.models.values()))

    def test_v16_loaded(self):
        sut = SpoortakModelsData(MODELS_DATA_DIR)
        self.assertEqual((11935, 19), sut.models[16].shape)

    def test_columns_loaded(self):
        models = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]

        expected = ['ID', 'OBJECTTYPE', 'GEOCODE_BEGIN', 'SUBCODE_BEGIN',
                    'NAAM_GEOCODE_BEGIN', 'NR_BEGIN', 'KANTCODE_BEGIN', 'GEOCODE_EIND',
                    'SUBCODE_EIND', 'NAAM_GEOCODE_EIND', 'NR_EIND', 'KANTCODE_EIND',
                    'NR_SUB', 'LENGTE', 'OBEGINTIJD', 'BEHEERDER', 'LENGTE_GEOM',
                    'kilometrering_start', 'kilometrering_end']
        sut = SpoortakModelsData(MODELS_DATA_DIR)
        for model in models:
            with self.subTest(model=model):
                self.assertCountEqual(sut.models[model].columns, expected)

#
