import os
import pathlib
import unittest
from unittest import skip
from unittest.mock import patch
from pprint import pprint

from openspoor.spoortakmodel import SpoortakModelInspector, SpoortakModelsData

MODELS_DATA_DIR = str(pathlib.Path(__file__).parents[2].resolve().joinpath('data'))


class TestSpoortakModelInspector(unittest.TestCase):

    @patch('openspoor.spoortakmodel.spoortak_model_inspector.pprint')
    def test_spoortak_in_modfwe(self, mock_pprint):
        expected_spoortak_model_rows = 15
        expected_bericht_rows = 3

        # For development and debugging we still want to see the prints
        mock_pprint.side_effect = pprint

        sut = SpoortakModelInspector(SpoortakModelsData(MODELS_DATA_DIR))
        sut.inspect('603_89R_2.6')
        mock_pprint.assert_called()
        self.assertEqual(expected_spoortak_model_rows, len(mock_pprint.call_args_list[0][0][0]), )
        self.assertEqual(expected_bericht_rows, len(mock_pprint.call_args_list[1][0][0]))

    @patch('openspoor.spoortakmodel.spoortak_model_inspector.pprint')
    def test_spoortak_in_dassignname(self, mock_pprint):
        expected_spoortak_model_rows = 4
        expected_bericht_rows = 9

        # For development and debugging we still want to see the prints
        mock_pprint.side_effect = pprint

        sut = SpoortakModelInspector(SpoortakModelsData(MODELS_DATA_DIR))
        sut.inspect('087_1321R_24.1')
        mock_pprint.assert_called()
        self.assertEqual(expected_spoortak_model_rows, len(mock_pprint.call_args_list[0][0][0]), )
        self.assertEqual(expected_bericht_rows, len(mock_pprint.call_args_list[1][0][0]))

    @patch('openspoor.spoortakmodel.spoortak_model_inspector.pprint')
    def test_spoortak_in_fwename(self, mock_pprint):
        expected_spoortak_model_rows = 4
        expected_bericht_rows = 1

        # For development and debugging we still want to see the prints
        mock_pprint.side_effect = pprint

        sut = SpoortakModelInspector(SpoortakModelsData(MODELS_DATA_DIR))
        sut.inspect('927_3325R_904.6')
        mock_pprint.assert_called()
        self.assertEqual(expected_spoortak_model_rows, len(mock_pprint.call_args_list[0][0][0]), )
        self.assertEqual(expected_bericht_rows, len(mock_pprint.call_args_list[1][0][0]))

    @patch('openspoor.spoortakmodel.spoortak_model_inspector.pprint')
    def test_spoortak_478_1201V_0_6(self, mock_pprint):
        """ Bug test: Gives issues on linux, but works on windows """
        expected_spoortak_model_rows = 4
        expected_bericht_rows = 1

        # For development and debugging we still want to see the prints
        mock_pprint.side_effect = pprint

        sut = SpoortakModelInspector(SpoortakModelsData(MODELS_DATA_DIR))
        sut.inspect('478_1201V_0.6')
        mock_pprint.assert_called()
        self.assertEqual(expected_spoortak_model_rows, len(mock_pprint.call_args_list[0][0][0]), )
        self.assertEqual(expected_bericht_rows, len(mock_pprint.call_args_list[1][0][0]))

    @skip('Development only test, comment this skip to enable it')
    def test_develop(self):
        """ quickly inspect the data of a spoortak"""
        sut = SpoortakModelInspector(SpoortakModelsData(MODELS_DATA_DIR))
        sut.inspect('518_107BL_63.5')
