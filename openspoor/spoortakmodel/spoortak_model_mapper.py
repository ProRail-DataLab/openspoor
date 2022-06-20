from typing import Optional

import numpy as np
import pandas as pd

from .spoortak_subsection import SpoortakSubsection
from .spoortak_models_data import SpoortakModelsData

import logging

log = logging.getLogger(__name__)


class SpoortakModelMapper:
    """ Limitations:
          - RENAME keyword not supported
          - can't map if there is no overlapping geocode
          - assumes singular kilometer lint if geocodes match with older segments
          - does not support spoortak 2.0 model (v18) yet
          - unkown what happens if geocode_begin and geocode_end differ and do not share a km lint

     TODO:
        - now assume the input exists in 17 and we are searching backward... Make this more flexible to search forward from 'midway'
        - Probably should have a validation that we have the same 'length' for all spoortak models in our output

        changes as described in BBMS_BERICHT_xx.csv
        ASSIGN - implemented
        NEWTOP - implemented
        EDITCORR - Don't need (?)
        EDITREAL - Don't need (?)
        RENAME - TODO
          rename is often use to swap two names. If we want to support rename we need to keep track of both else we'll
          report back on both the spoortakken that swapped the names

    """

    def __init__(self, spoortak_model_data: SpoortakModelsData):
        self._data = spoortak_model_data
        log.warning("SpoortakModelMapper is a best effort mapper to older/newer models, it is far from perfect.")

    def _is_new_spoortak(self, spoortak_identifier, spoortak_model: int):
        changes = self._data.model_changes[spoortak_model]
        action_new = changes[(changes['FWENAME'] == spoortak_identifier) & (changes['ACTION'] == 'NEWTOP')]
        return len(action_new) > 0

    def _retrieve_spoortak(self, spoortak_identifier: str, model_version: int) -> Optional[pd.Series]:
        """ Retrieve the spoortak data for a specific model version """
        if spoortak_identifier not in self._data.models[model_version].index:
            return None

        return self._data.models[model_version].loc[spoortak_identifier]

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

            # not implemented
            mask = mask & (model_changes['ACTION'] != 'RENAME')

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
                # if there is no geocode overlap we can't assume the kilometrering uses the same 'kilometer lint'
                spoortak = self._retrieve_spoortak(entry, model_version)
                if spoortak is None:
                    spoortak = self._retrieve_spoortak(entry, model_version - 1)
                if spoortak is None:
                    raise ValueError(
                        f"Could not find spoortak {entry} in model {model_version} and {model_version - 1}")

                if spoortak['GEOCODE_BEGIN'] in geocodes or spoortak['GEOCODE_EIND'] in geocodes:
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

    def map(self, spoortak_subsection: SpoortakSubsection, _ignore_list: [str] = None) -> [SpoortakSubsection]:
        """ Maps a spoortak subsection to all other spoortak models

        :param spoortak_subsection: subsection to map
        :param _ignore_list: list of spoortak identifiers to ignore (need this to avoid infinite loops)

        """

        if not _ignore_list:
            _ignore_list = []

        geocodes = []
        found_subsections = []
        spoortak_found = False

        # scan backwards
        for model_version in self._data.model_version_numbers[::-1]:

            # step 1: Scan the model data for all references
            spoortak_data = self._retrieve_spoortak(spoortak_subsection.identification, model_version)

            if spoortak_found and spoortak_data is None:
                raise ValueError(f'The spoortak was not new, but could not find it in version {model_version}.')

            if spoortak_data is None:
                continue

            spoortak_found = True

            # make this nicer, dont need to grab them every time and overwriting them with the oldest?
            geocodes = [spoortak_data['GEOCODE_BEGIN'], spoortak_data['GEOCODE_EIND']]

            found_subsections.append(
                SpoortakSubsection(str(spoortak_data.name),
                                   max(spoortak_subsection.kilometrering_start, spoortak_data['kilometrering_start']),
                                   min(spoortak_subsection.kilometrering_end, spoortak_data['kilometrering_end']),
                                   model_version))

            if self._is_new_spoortak(spoortak_subsection.identification, model_version):
                log.info(f'Spoortak was new, not searching further back in the model history')
                break

        # find anything that is related,
        # assume same km lint if one of the geocodes matches and just add them all to the list
        related_spoortakken = self._related_spoortakken(spoortak_subsection.identification, geocodes)
        for related_spoortak, related_model_version in related_spoortakken:
            if related_spoortak in _ignore_list:
                continue

            spoortak_subsection = SpoortakSubsection(related_spoortak, spoortak_subsection.kilometrering_start,
                                                     spoortak_subsection.kilometrering_end,
                                                     related_model_version)
            related_segments = self.map(spoortak_subsection, _ignore_list + [spoortak_subsection.identification])
            found_subsections.extend(related_segments)

        limited = self._limit_start_end(found_subsections, spoortak_subsection.kilometrering_start,
                                        spoortak_subsection.kilometrering_end)
        cleaned = self._remove_duplicates(limited)

        ordered = sorted(cleaned, key=lambda x: (x.spoortak_model_version, x.kilometrering_start))

        return ordered

    def map_to(self, spoortak_subsection: SpoortakSubsection, model_version: int) -> [SpoortakSubsection]:
        """ Maps a spoortak subsection to a specific model version """
        results = self.map(spoortak_subsection)
        return [result for result in results if result.spoortak_model_version == model_version]
