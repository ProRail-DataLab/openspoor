from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SpoortakSubsection:
    """
    Spoortak subsection.

    Parameters
    ----------
    kilometrering_start : float
        Kilometrering in meters.
    kilometrering_end : float
        Kilometrering in meters.

    Notes
    -----
    This is not a Spoortak 2.0 segment.
    """

    identification: str
    kilometrering_start: int
    kilometrering_end: int

    spoortak_model_version: Optional[int] = None

    def limit_start_end(self, start: int, end: int):
        """Creates a new SpoortakSubsection limited to start and end"""
        return SpoortakSubsection(
            self.identification,
            max(self.kilometrering_start, start),
            min(self.kilometrering_end, end),
            self.spoortak_model_version,
        )
