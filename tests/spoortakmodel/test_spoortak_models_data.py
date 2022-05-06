import pathlib
import unittest

from openspoor.spoortakmodel import SpoortakModelsData

MODELS_DATA_DIR = str(pathlib.Path(__file__).parent.resolve().joinpath('..', '..', 'data').resolve())


class TestSpoortakModelsData(unittest.TestCase):
    def test_basic_load_test(self):
        sut = SpoortakModelsData(MODELS_DATA_DIR)

        self.assertGreaterEqual(15, len(sut.models))
        self.assertGreaterEqual(15, len(sut.model_changes))

    def test_data_unique_spoortak(self):
        """ This is a data integrity test"""
        sut = SpoortakModelsData(MODELS_DATA_DIR)
        self.assertFalse(any(any(model.index.duplicated()) for model in sut.models.values()))
