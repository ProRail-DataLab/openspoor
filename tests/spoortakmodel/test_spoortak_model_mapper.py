import pathlib
import unittest

from openspoor.spoortakmodel import SpoortakSubsection
from openspoor.spoortakmodel import SpoortakModelMapper

MODELS_DATA_DIR = str(pathlib.Path(__file__).parent.resolve().joinpath('..', '..', 'data').resolve())


class TestSpoortakModelMapper(unittest.TestCase):
    def test_spoortak_model_mapper(self):
        subsection = SpoortakSubsection('478_1201V_0.6', 535, 570)
        sut = SpoortakModelMapper(MODELS_DATA_DIR)
        result = sut.map(subsection)
        self.assertIsNotNone(result)
