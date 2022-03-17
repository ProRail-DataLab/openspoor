from dataclasses import dataclass


@dataclass
class SpoortakSubsection:
    """ Spoortak subsection


    :param kilometrering_from: Kilometrering in meters
    :param kilometrering_to: Kilometrering in meters

    Remarks: This is not a spoortak 2.0 segment

    """

    identification: str
    kilometrering_from: int
    kilometrering_to: int

    spoortak_model: int = None


