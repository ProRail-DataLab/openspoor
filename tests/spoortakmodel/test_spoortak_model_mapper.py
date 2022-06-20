import pathlib
import unittest
from unittest import skip

import pytest

from openspoor.spoortakmodel import SpoortakSubsection, SpoortakModelsData
from openspoor.spoortakmodel import SpoortakModelMapper
import platform

MODELS_DATA_DIR = str(pathlib.Path(__file__).parent.resolve().joinpath('..', '..', 'data').resolve())


class TestSpoortakModelMapper(unittest.TestCase):
    @pytest.mark.skipif(platform.system() == "Linux", reason="Fails on ubuntu but succeeds on windows")
    def test_map_happy_flow(self):
        expected_models = [14, 15, 16, 17]
        subsection = SpoortakSubsection('478_1201V_0.6', 535, 570)

        sut = SpoortakModelMapper(SpoortakModelsData(MODELS_DATA_DIR))
        result = sut.map(subsection)
        result_models = [model.spoortak_model_version for model in result]

        self.assertCountEqual(expected_models, result_models)

    @pytest.mark.skipif(platform.system() == "Linux", reason="Fails on ubuntu but succeeds on windows")
    def test_map_happy_flow_bug(self):
        """ test to see if the start and end were the cause of the original test failing """
        expected_models = [14, 15, 16, 17]
        subsection = SpoortakSubsection('478_1201V_0.6', 0, 999999)

        sut = SpoortakModelMapper(SpoortakModelsData(MODELS_DATA_DIR))
        result = sut.map(subsection)
        result_models = [model.spoortak_model_version for model in result]

        self.assertCountEqual(expected_models, result_models)

    @pytest.mark.skipif(platform.system() == "Linux", reason="Fails on ubuntu but succeeds on windows")
    def test_map_spoortak_id_change_assign(self):
        subsection = SpoortakSubsection('087_1321R_24.1', 24059, 25900)

        sut = SpoortakModelMapper(SpoortakModelsData(MODELS_DATA_DIR))
        result = sut.map(subsection)

        self.assertEqual(15, len(result))

    @pytest.mark.skipif(platform.system() == "Linux", reason="Fails on ubuntu but succeeds on windows")
    def test_map_to_happy_flow(self):
        subsection = SpoortakSubsection('087_1321R_24.1', 24059, 25900)

        sut = SpoortakModelMapper(SpoortakModelsData(MODELS_DATA_DIR))
        result = sut.map_to(subsection, 6)

        self.assertEqual(1, len(result))

        # start should not be identical as the search start
        self.assertEqual(24102, result[0].kilometrering_start)

    def test_map_to_split(self):
        # this spoortak split in two between model version 16 and 17
        subsection = SpoortakSubsection('508_2055V_91.2', 91213, 91436)
        sut = SpoortakModelMapper(SpoortakModelsData(MODELS_DATA_DIR))
        result = sut.map_to(subsection, 17)

        self.assertEqual(2, len(result))
        self.assertEqual(result[0].kilometrering_end, result[1].kilometrering_start)

    @skip('Due to the name swap that happens we currently dont support RENAME.')
    def test_map_spoortak_rename(self):
        subsection = SpoortakSubsection('518_107BL_63.5', 63145, 63474)
        sut = SpoortakModelMapper(SpoortakModelsData(MODELS_DATA_DIR))
        result = sut.map(subsection)

        self.assertEqual(15, len(result))

    @skip('Functionality not implemented yet')
    def test_name_swap(self):
        """ TODO - model 6 - Ingnore this edge case or implement?
        9996;2016-01-07;6;RENAME;133_951L_20.9;;;;;;;;;;XXX1;
9997;2016-01-07;6;RENAME;133_951R_20.9;;;;;;;;;;XXX2;
9998;2016-01-07;6;RENAME;133_950L_20.9;;;;;;;;;;133_951L_20.9;
9999;2016-01-07;6;RENAME;133_950R_20.9;;;;;;;;;;133_951R_20.9;
10001;2016-01-07;6;RENAME;XXX1;;;;;;;;;;133_950L_20.9;
10002;2016-01-07;6;RENAME;XXX2;;;;;;;;;;133_950R_20.9;  """
        pass
