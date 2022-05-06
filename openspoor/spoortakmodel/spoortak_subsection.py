from dataclasses import dataclass


@dataclass(frozen=True)
class SpoortakSubsection:
    """ Spoortak subsection


    :param kilometrering_start: Kilometrering in meters
    :param kilometrering_end: Kilometrering in meters

    Remarks: This is not a spoortak 2.0 segment

    """

    identification: str
    kilometrering_start: int
    kilometrering_end: int

    spoortak_model_version: int = None

    def limit_start_end(self, start: int, end: int):
        """ creates a new SpoortakSubsection limited to start and end"""
        return SpoortakSubsection(
            self.identification,
            max(self.kilometrering_start, start),
            min(self.kilometrering_end, end),
            self.spoortak_model_version
        )
