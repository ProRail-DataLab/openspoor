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

        # scan backwards
        for model_version in range(self._data.model_end, self._data.model_start - 1, -1):
            model = self._data.models[model_version]

            # step 1: if it still exists under the same name
            mask = (
                    (model['SPOORTAK_IDENTIFICATIE'] == spoortak_subsection.identification) &
                    # overlap
                    (model['kilometrering_from'] <= spoortak_subsection.kilometrering_to) &
                    (model['kilometrering_to'] >= spoortak_subsection.kilometrering_from)
            )

            subsections = model[mask]

            if len(subsections) == 0:
                if not self._is_new_spoortak(spoortak_subsection.identification, model_version + 1):
                    raise ValueError(
                        f'The spoortak was not new, but could not trace it back further.')

                log.info(f'Spoortak was new, not searching further back in the model history')
                break
            else:
                for _, row in subsections.iterrows():
                    found_subsections.append(
                        SpoortakSubsection(row['SPOORTAK_IDENTIFICATIE'],
                                           max(spoortak_subsection.kilometrering_from, row['kilometrering_from']),
                                           min(spoortak_subsection.kilometrering_to, row['kilometrering_to']),
                                           model_version))

        return found_subsections
