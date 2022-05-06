from pprint import pprint
import pandas as pd

from ..spoortakmodel import SpoortakModelsData


class SpoortakModelInspector:
    def __init__(self, spoortak_model_data: SpoortakModelsData):
        self.data = spoortak_model_data
        self.old_pd_option_values = dict()

    def _set_pd_options(self):

        self.old_pd_option_values['display.max_columns'] = pd.get_option('display.max_columns')
        self.old_pd_option_values['display.max_rows'] = pd.get_option('display.max_rows')
        self.old_pd_option_values['display.expand_frame_repr'] = pd.get_option('display.expand_frame_repr')
        self.old_pd_option_values['mode.chained_assignment'] = pd.get_option('mode.chained_assignment')

        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.expand_frame_repr', False)
        pd.set_option('mode.chained_assignment', None)

    def _reset_pd_options(self):
        for key, value in self.old_pd_option_values.items():
            pd.set_option(key, value)

    def inspect(self, spoortak_identifier: str):
        """ Scans the spoortak model data (including change data) and returns everything related to the given spoortak """
        self._set_pd_options()

        print(f'--- {spoortak_identifier} spoortakmodel data ---')

        baseline_model = 3

        model_data = pd.DataFrame(columns=list(self.data.models[baseline_model].columns) + ['spoortakmodel'])

        for spoortakmodel_version, model in self.data.models.items():
            if spoortak_identifier in model.index:
                df = model.loc[spoortak_identifier]
                df['spoortakmodel'] = spoortakmodel_version
                # model_data = pd.concat([model_data, df], axis=1)
                model_data = model_data.append(df)
        pprint(model_data)

        print(f'--- {spoortak_identifier} spoortakmodel changes ---')

        change_data = pd.DataFrame(columns=list(self.data.model_changes[baseline_model].columns) + ['spoortakmodel'])

        for spoortakmodel_version, model_changes in self.data.model_changes.items():
            df = model_changes[
                (model_changes['MODFWE'] == spoortak_identifier)
                | (model_changes['DASSIGNNAME'] == spoortak_identifier)
                | (model_changes['FWENAME'] == spoortak_identifier)
                ]
            if len(df) > 0:
                df['spoortakmodel'] = spoortakmodel_version
                change_data = pd.concat([change_data, df], axis=0)
        pprint(change_data)

        self._reset_pd_options()
