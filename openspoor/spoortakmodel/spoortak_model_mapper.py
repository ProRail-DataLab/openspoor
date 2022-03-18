import numpy as np
import pandas as pd

from .spoortak_subsection import SpoortakSubsection
from .spoortak_models_data import SpoortakModelsData

import logging

log = logging.getLogger(__name__)


class SpoortakModelMapper:
    def __init__(self, data_path: str):
        self._data = SpoortakModelsData(data_path)

    def _is_new_spoortak(self, spoortak_identifier, spoortak_model: int):
        changes = self._data.model_changes[spoortak_model]
        action_new = changes[(changes['FWENAME'] == spoortak_identifier) & (changes['ACTION'] == 'NEWTOP')]
        return len(action_new) > 0

    def _retrieve_spoortak(self, spoortak_identifier: str, model_version: int) -> pd.Series:
        """ Retrieve the spoortak data for a specific model version """
        return self._data.spoortakken[model_version][spoortak_identifier]

    def _related_spoortakken(self, spoortak_identifier: str, geocodes: [int]) -> [(str, int)]:

        related_spoortakken = []

        for model_version in self._data.model_version_numbers:
            temp_related_spoortakken = set()
            model_changes = self._data.model_changes[model_version]
            mask = (
                    (model_changes['MODFWE'] == spoortak_identifier)
                    | (model_changes['DASSIGNNAME'] == spoortak_identifier)
                    | (model_changes['FWENAME'] == spoortak_identifier)
            )
            changes = model_changes[mask]
            if len(changes) > 0:
                temp_related_spoortakken.update(changes['MODFWE'].unique())
                temp_related_spoortakken.update(changes['DASSIGNNAME'].unique())
                temp_related_spoortakken.update(changes['FWENAME'].unique())

            if np.nan in temp_related_spoortakken:
                temp_related_spoortakken.remove(np.nan)
            if spoortak_identifier in temp_related_spoortakken:
                temp_related_spoortakken.remove(spoortak_identifier)

            for entry in temp_related_spoortakken:
                related_spoortakken.append((entry, model_version))

        return related_spoortakken

    @staticmethod
    def _limit_start_end(subsections: [SpoortakSubsection], km_start: int, km_end: int) -> [SpoortakSubsection]:
        """ perforce the limit in place """
        return [subsection.limit_start_end(km_start, km_end) for subsection in subsections]

    @staticmethod
    def _remove_duplicates(subsections: [SpoortakSubsection]) -> [SpoortakSubsection]:
        deduped = set(subsections)
        return list(deduped)

    def map(self, spoortak_subsection: SpoortakSubsection) -> [SpoortakSubsection]:
        """ Maps a spoortak subsection to all other spoortak models

        TODO:
        - now assume the input exists in 17 and we are searching backward... Make this more flexible to search forward from 'midway'
        - Probably should have a validation that we have the same 'length' for all spoortak models in our output

        changes as described in BBMS_BERICHT_xx.csv
        ASSIGN - TODO (form of delete, but also a section of track is reassigned to an ohter spoortak. We don't understand the format yet)
        NEWTOP - implemented
        EDITCORR - Don't need (?)
        EDITREAL - Don't need (?)
        RENAME - TODO (it is wierd, one example has a rename, but still the old and new new were present in the new spoortak_xx.csv)

        """

        found_subsections = []
        spoortak_found = False

        # scan backwards
        for model_version in self._data.model_version_numbers[::-1]:
            model = self._data.models[model_version]

            # step 1: if it still exists under the same name
            mask = (
                    (model['SPOORTAK_IDENTIFICATIE'] == spoortak_subsection.identification) &
                    # overlap
                    (model['kilometrering_start'] <= spoortak_subsection.kilometrering_end) &
                    (model['kilometrering_end'] >= spoortak_subsection.kilometrering_start)
            )

            subsections = model[mask]

            if spoortak_found and len(subsections) == 0:
                raise ValueError(f'The spoortak was not new, but could not find it in version {model_version}.')

            if len(subsections) > 0:
                spoortak_found = True
                assert len(subsections) == 1, f'Expected only one entry, but found {len(subsections)}'
                geocodes = [subsections.iloc[0]['GEOCODE_BEGIN'], subsections.iloc[0]['GEOCODE_EIND']]

            for _, row in subsections.iterrows():
                found_subsections.append(
                    SpoortakSubsection(row['SPOORTAK_IDENTIFICATIE'],
                                       max(spoortak_subsection.kilometrering_start, row['kilometrering_start']),
                                       min(spoortak_subsection.kilometrering_end, row['kilometrering_end']),
                                       model_version))

            if self._is_new_spoortak(spoortak_subsection.identification, model_version):
                log.info(f'Spoortak was new, not searching further back in the model history')
                break

        # find anything that is related, assume same km lint and just add them all to the list
        # todo: we can limit this by comparing the geocode (start and ends) at least 1 of them should match
        related_spoortakken = self._related_spoortakken(spoortak_subsection.identification, geocodes)
        for related_spoortak, related_model_version in related_spoortakken:
            related_segments = self.map(SpoortakSubsection(related_spoortak, spoortak_subsection.kilometrering_start,
                                                           spoortak_subsection.kilometrering_end,
                                                           related_model_version))
            found_subsections.extend(related_segments)

        limited = self._limit_start_end(found_subsections, spoortak_subsection.kilometrering_start,
                                        spoortak_subsection.kilometrering_end)
        cleaned = self._remove_duplicates(limited)

        return cleaned

    def map_to(self, spoortak_subsection: SpoortakSubsection, model_version: int) -> [SpoortakSubsection]:
        """ Maps a spoortak subsection to a specific model version """
        results = self.map(spoortak_subsection)
        return [result for result in results if result.model_version == model_version]
