from typing import Optional, List

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

        for model_version in self._data.model_version_numbers_old:
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

    def map_v1(self, spoortak_subsection: SpoortakSubsection, _ignore_list: [str] = None) -> [SpoortakSubsection]:
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
        for model_version in self._data.model_version_numbers_old[::-1]:

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

        #Add spoortak V2.0

        limited = self._limit_start_end(found_subsections, spoortak_subsection.kilometrering_start,
                                        spoortak_subsection.kilometrering_end)
        cleaned = self._remove_duplicates(limited)

        ordered = sorted(cleaned, key=lambda x: (x.spoortak_model_version, x.kilometrering_start), reverse=True)

        return ordered
    
    def _retrieve_spoortak_segment(self, spoortak_segment: str, model_version: int) -> Optional[pd.Series]:
        """ Retrieve the spoortak data for a specific model version """
        if self._data.new_models[model_version].index.name != "NAAM":
            self._data.new_models[model_version].set_index("NAAM", drop = False, inplace = True)

        if spoortak_segment not in self._data.new_models[model_version].index:
            return None

        return self._data.new_models[model_version].loc[spoortak_segment]


    def _retrieve_spoortak_v2(self, OLD_SEGMENT: str, model_version: int) -> List[SpoortakSubsection]:
        """ Maps a spoortak from v1 to segments in v2 """
        if self._data.new_models_map[18].index.name != "OLD_SEGMENT":
            self._data.new_models_map[18].set_index("OLD_SEGMENT", inplace = True)

        if OLD_SEGMENT not in self._data.new_models_map[model_version].index:
            return None
        
        return self._data.new_models_map[model_version].loc[OLD_SEGMENT]

        # mapped = self._data.new_models_map[spoortak_version]
        # mapped_new = mapped.loc[(mapped['OLD_SEGMENT'] == spoortak_subsection.identification)]
        # return mapped_new
        # # TODO: Alles
    
    def _retrieve_spoortak_v1(self, NAAM_v2: str) -> List[SpoortakSubsection]:
        """ Maps a spoortak from v1 to segments in v2 """
        if self._data.new_models_map[18].index.name != "NAAM":
            self._data.new_models_map[18].set_index("NAAM", inplace = True)
        
        if NAAM_v2 not in self._data.new_models_map[18].index:
            return None
        
        return self._data.new_models_map[18].loc[NAAM_v2]
    
    def map_v1_to_v2(self, spoortak_subsection: SpoortakSubsection) -> List[SpoortakSubsection]:
        """
        map_section_to_v2
        Map a spoortak subsection to a specific model version and find the relevant subsections in the spoortak v2.0

        :param spoortak_subsection: subsection to map
        :param kilometrering_van: start of the section
        :param kilometrering_tot: end of the section
        """
       
        Subsectie_v2 = []
      
        for row in self._retrieve_spoortak_v2(spoortak_subsection.identification, 18).itertuples():
            if (not row.kilometrering_end <= spoortak_subsection.kilometrering_start) & (not row.kilometrering_start >= spoortak_subsection.kilometrering_end):
                Subsectie_v2.append(SpoortakSubsection(row.NAAM, round(max(row.kilometrering_start, spoortak_subsection.kilometrering_start),0), 
                                                    round(min(row.kilometrering_end, spoortak_subsection.kilometrering_end),0),  row.VERSIE_NUMMER_y))

        return Subsectie_v2
    
    def map_v2_to_v1(self, spoortak_subsection: SpoortakSubsection) -> List[SpoortakSubsection]:
        
        Subsectie_v1 = []
      
        df = self._retrieve_spoortak_v1(spoortak_subsection.identification)

        if df is None:
            Subsectie_v1
        else:
            if ((not df.kilometrering_end <= spoortak_subsection.kilometrering_start) & (not df.kilometrering_start >= spoortak_subsection.kilometrering_end)):
                Subsectie_v1.append(SpoortakSubsection(df.OLD_SEGMENT, round(max(df.kilometrering_start, spoortak_subsection.kilometrering_start),0), 
                                                    round(min(df.kilometrering_end, spoortak_subsection.kilometrering_end),0),  17))

        return Subsectie_v1


    def map_v2_backward(self, spoortak_subsection: SpoortakSubsection, _ignore_list: [str] = None) -> [SpoortakSubsection]:
        if not _ignore_list:
            _ignore_list = []

        huidige_lengte = -1
        found_subsections = []

        model_version = self._data.new_style_model_versions[::-1][0]
    
        while ((len(found_subsections) - huidige_lengte > 0) & (model_version >= 18)):
            huidige_lengte = len(found_subsections)

            spoortak_data = self._retrieve_spoortak_segment(spoortak_subsection.identification, model_version)

            if not spoortak_data is None:
                found_subsections.append(
                    SpoortakSubsection(str(spoortak_data.name),
                                    max(spoortak_subsection.kilometrering_start, spoortak_data['kilometrering_start']),
                                    min(spoortak_subsection.kilometrering_end, spoortak_data['kilometrering_end']),
                                    model_version))
            elif model_version < max(self._data.new_style_model_versions[::-1]):               
                df_changes = self._data.model_changes_v2[model_version+1]
                waarde = df_changes[df_changes.NAAM == spoortak_subsection.identification].dropna(subset=['OLD_SEGMENT']).OLD_SEGMENT.values[0]
                df_model = self._data.new_models[model_version]
                spoortak_data_old = df_model[df_model.SEGMENT_IDENTIFICATIE == waarde]
                if not spoortak_data_old is None:
                    
                    spoortak_subsection = SpoortakSubsection(str(spoortak_data_old.NAAM.values[0]),
                                        max(spoortak_subsection.kilometrering_start, spoortak_data_old['kilometrering_start'].values[0]),
                                        min(spoortak_subsection.kilometrering_end, spoortak_data_old['kilometrering_end'].values[0]),
                                        model_version)
                    found_subsections.append(spoortak_subsection
                        )
            model_version = model_version-1

        return found_subsections
    
    def map_v2_forward(self, spoortak_subsection: SpoortakSubsection, _ignore_list: [str] = None) -> [SpoortakSubsection]:
        if not _ignore_list:
            _ignore_list = []

        huidige_lengte = -1
        found_subsections = []

        model_version = self._data.new_style_model_versions[0]

        while ((len(found_subsections) - huidige_lengte > 0) & (model_version <= max(self._data.new_style_model_versions))):

            huidige_lengte = len(found_subsections)

            spoortak_data = self._retrieve_spoortak_segment(spoortak_subsection.identification, model_version)

            if not spoortak_data is None:
                found_subsections.append(
                    SpoortakSubsection(str(spoortak_data.name),
                                    max(spoortak_subsection.kilometrering_start, spoortak_data['kilometrering_start']),
                                    min(spoortak_subsection.kilometrering_end, spoortak_data['kilometrering_end']),
                                    model_version))
            elif 18 < model_version < max(self._data.new_style_model_versions[::-1]):         
                df_changes = self._data.model_changes_v2_oud[model_version]
                waarde = df_changes[df_changes.NAAM == spoortak_subsection.identification].dropna(subset=['OLD_SEGMENT']).OLD_SEGMENT.values[0]
                df_model = self._data.new_models[model_version]
                spoortak_data_old = df_model[df_model.SEGMENT_IDENTIFICATIE == waarde]
                if not spoortak_data_old is None:
                    
                    spoortak_subsection = SpoortakSubsection(str(spoortak_data_old.NAAM.values[0]),
                                        max(spoortak_subsection.kilometrering_start, spoortak_data_old['kilometrering_start'].values[0]),
                                        min(spoortak_subsection.kilometrering_end, spoortak_data_old['kilometrering_end'].values[0]),
                                        model_version)
                    found_subsections.append(spoortak_subsection
                        )

            model_version = model_version+1

        return found_subsections

    def map_v2(self, spoortak_subsection: SpoortakSubsection, _ignore_list: [str] = None) -> [SpoortakSubsection]:
        V1_en_V2 =self.map_v2_forward(spoortak_subsection, _ignore_list) + self.map_v2_backward(spoortak_subsection, _ignore_list)
        cleaned = self._remove_duplicates(V1_en_V2)
        ordered = sorted(cleaned, key=lambda x: (x.spoortak_model_version, x.kilometrering_start), reverse=True)

        return ordered
    
 
    def map_v2_to_all(self, spoortak_subsection: SpoortakSubsection) -> List[SpoortakSubsection]:
        
        found_subsections_v2 = self.map_v2(spoortak_subsection)

        spoortak_v2_18 = [x for x in found_subsections_v2 if x.spoortak_model_version==18]

        if not spoortak_v2_18:
            found_subsections_v1 = []
        else:
            spoortak_v1_17 = self.map_v2_to_v1(spoortak_v2_18[0])
            found_subsections_v1 = self.map_v1(spoortak_v1_17[0])

        return found_subsections_v2 + found_subsections_v1
    

    
    def map_v1_to_all(self, spoortak_subsection: SpoortakSubsection) -> List[SpoortakSubsection]:

        found_subsections_v1 = self.map_v1(spoortak_subsection)
        
        spoortak_v1_17 = [x for x in found_subsections_v1 if x.spoortak_model_version==17]

        if spoortak_v1_17 is None:
            found_subsections_v2 = []

        else:
            spoortak_v2_18 = self.map_v1_to_v2(spoortak_v1_17[0])
            found_subsections_v2 = self.map_v2(spoortak_v2_18[0])

        return found_subsections_v2 + found_subsections_v1



    def map_to(self, spoortak_subsection: SpoortakSubsection, model_version: int) -> [SpoortakSubsection]:
        """ Maps a spoortak subsection to a specific model version """
        results = self.map(spoortak_subsection)
        return [result for result in results if result.spoortak_model_version == model_version]
