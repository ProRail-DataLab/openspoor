import geopandas as gpd

from openspoor.visualisations import (
    PlottingLineStrings,
    PlottingPoints,
    TrackMap,
)


class Route(PlottingLineStrings):
    def __init__(
        self, functionele_spoortak, spoortakken, start=None, end=None
    ):
        self.functionele_spoortak = functionele_spoortak
        self.data = functionele_spoortak.loc[
            lambda d: d.PUIC.isin(spoortakken)
        ]
        self.start = start
        self.end = end
        super().__init__(self.data, popup=["PUIC"])

    @property
    def length(self):
        return self.data.length.sum()

    def set_color(self, color):
        self.color = color
        return self

    def quick_plot(self):
        if not self.start or not self.end:
            return TrackMap([self]).show()
        if self.start and self.end:
            gdf_start = gpd.GeoDataFrame(
                geometry=[self.start],
                data={"locatie": ["start"]},
                crs=self.data.crs,
            )
            gdf_end = gpd.GeoDataFrame(
                geometry=[self.end],
                data={"locatie": ["end"]},
                crs=self.data.crs,
            )
            return TrackMap(
                [
                    self,
                    PlottingPoints(gdf_start, popup="locatie", colors="red"),
                    PlottingPoints(gdf_end, popup="locatie", colors="green"),
                ]
            ).show()
