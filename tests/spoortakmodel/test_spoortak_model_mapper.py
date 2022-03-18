import pathlib
import unittest

from openspoor.spoortakmodel import SpoortakSubsection
from openspoor.spoortakmodel import SpoortakModelMapper

MODELS_DATA_DIR = str(pathlib.Path(__file__).parent.resolve().joinpath('..', '..', 'data').resolve())


class TestSpoortakModelMapper(unittest.TestCase):
    def test_map_happy_flow(self):
        subsection = SpoortakSubsection('478_1201V_0.6', 535, 570)
        sut = SpoortakModelMapper(MODELS_DATA_DIR)
        result = sut.map(subsection)

        self.assertEqual(4, len(result))

    def test_map_spoortak_id_change(self):
        subsection = SpoortakSubsection('087_1321R_24.1', 24059, 25900)
        sut = SpoortakModelMapper(MODELS_DATA_DIR)
        result = sut.map(subsection)
        self.assertIsNotNone(result)
        self.assertEqual(15, len(result))

    def test_map_to_happy_flow(self):
        subsection = SpoortakSubsection('087_1321R_24.1', 24059, 25900)

        sut = SpoortakModelMapper(MODELS_DATA_DIR)
        result = sut.map_to(subsection, 6)

        self.assertEqual(1, len(result))

        # start should not be identical as the search start
        self.assertEqual(24102, result[0].kilometrering_start)
