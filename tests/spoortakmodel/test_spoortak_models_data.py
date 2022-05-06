import os
import pathlib
import unittest
from parameterized import parameterized
import pytest

from openspoor.spoortakmodel import SpoortakModelsData

MODELS_DATA_DIR = str(pathlib.Path(__file__).parents[2].resolve().joinpath('data').resolve())


def _test_model_name(func, param_num, param):
    """ expects the first param to be the model number"""
    return f'{func.__name__}_model_v{param.args[0]}'


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

    @parameterized.expand(
        [(3, 13163), (4, 13145), (5, 12952), (6, 12937), (7, 12867), (8, 12662), (9, 12528), (10, 12443), (11, 12390),
         (12, 12256),
         (13, 12217), (14, 12153), (15, 12057), (16, 11935), (17, 11906)], name_func=_test_model_name)
    def test_rows_loaded(self, model, row_count):
        sut = SpoortakModelsData(MODELS_DATA_DIR)
        self.assertEqual(len(sut.models[model]), row_count, f'model {model} has {len(sut.models[model])} rows')

    @parameterized.expand(
        [(3,), (4,), (5,), (6,), (7,), (8,), (9,), (10,), (11,), (12,), (13,), (14,), (15,), (16,), (17,)],
        name_func=_test_model_name)
    def test_columns_loaded(self, model):
        expected = ['ID', 'OBJECTTYPE', 'GEOCODE_BEGIN', 'SUBCODE_BEGIN',
                    'NAAM_GEOCODE_BEGIN', 'NR_BEGIN', 'KANTCODE_BEGIN', 'GEOCODE_EIND',
                    'SUBCODE_EIND', 'NAAM_GEOCODE_EIND', 'NR_EIND', 'KANTCODE_EIND',
                    'NR_SUB', 'LENGTE', 'OBEGINTIJD', 'BEHEERDER', 'LENGTE_GEOM',
                    'kilometrering_start', 'kilometrering_end']
        sut = SpoortakModelsData(MODELS_DATA_DIR)
        self.assertCountEqual(sut.models[model].columns, expected,
                              f'model {model} has {len(sut.models[model].columns)} columns')

#
