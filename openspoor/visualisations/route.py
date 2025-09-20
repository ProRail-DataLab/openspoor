import geopandas as gpd
from typing import Dict, List, Any

from openspoor.visualisations import (
    PlottingLineStrings,
    PlottingPoints,
    TrackMap,
)


class Route(PlottingLineStrings):
    """
    Comprehensive route value object that contains all route information.
    
    This class serves as a complete value object for route data, providing
    distance, travel time estimates, detailed segment information, and 
    visualization capabilities in a single object.
    """
    
    def __init__(
        self, functionele_spoortak, spoortakken, start=None, end=None
    ):
        self.functionele_spoortak = functionele_spoortak
        self.data = functionele_spoortak.loc[
            lambda d: d.PUIC.isin(spoortakken)
        ]
        self.start = start
        self.end = end
        self._spoortakken = spoortakken
        super().__init__(self.data, popup=["PUIC"])

    @property
    def length(self):
        """Total length of the route in meters."""
        # Ensure we're using a projected CRS for accurate length calculation
        if self.data.crs and self.data.crs.is_geographic:
            # Convert to a suitable projected CRS for length calculation
            # Use EPSG:28992 (RD New) for Netherlands, or Web Mercator as fallback
            projected_data = self.data.to_crs('EPSG:28992')
            return projected_data.length.sum()
        return self.data.length.sum()
    
    @property
    def distance(self):
        """Alias for length - total distance of the route in meters."""
        return self.length
    
    @property
    def distance_km(self):
        """Total distance of the route in kilometers."""
        return self.length / 1000.0
    
    @property
    def total_travel_time(self):
        """
        Estimated total travel time for the route in minutes.
        
        Uses a conservative estimate based on typical train speeds
        on different types of track infrastructure.
        """
        # Conservative estimate: average speed of 80 km/h for passenger trains
        # This is a reasonable assumption for mixed track types in Netherlands
        average_speed_kmh = 80.0
        time_hours = self.distance_km / average_speed_kmh
        return time_hours * 60.0  # Convert to minutes
    
    @property
    def route_segments(self) -> List[Dict[str, Any]]:
        """
        Detailed information about individual route segments.
        
        Returns a list of dictionaries, each containing information about
        a track segment including PUIC, length, and estimated travel time.
        """
        segments = []
        
        for idx, row in self.data.iterrows():
            # Calculate length using proper projection if needed
            if self.data.crs and self.data.crs.is_geographic:
                # Reproject just this geometry for length calculation
                geom_proj = gpd.GeoSeries([row.geometry], crs=self.data.crs).to_crs('EPSG:28992')
                segment_length = geom_proj.iloc[0].length
            else:
                segment_length = row.geometry.length
            
            # Estimate travel time for this segment (in minutes)
            segment_time = (segment_length / 1000.0) / 80.0 * 60.0
            
            # The PUIC is now the index due to PlottingLineStrings parent class
            segment_info = {
                'puic': idx,  # idx is the PUIC since it's set as index
                'length_m': segment_length,
                'length_km': segment_length / 1000.0,
                'estimated_time_minutes': segment_time,
                'geometry': row.geometry
            }
            
            # Add any additional fields that might be available
            for col in row.index:
                if col != 'geometry':
                    segment_info[col.lower()] = row[col]
            
            segments.append(segment_info)
        
        return segments
    
    @property
    def segment_count(self):
        """Number of track segments in the route."""
        return len(self.data)
    
    @property
    def summary(self) -> Dict[str, Any]:
        """
        Complete route summary with all key metrics.
        
        Returns a dictionary containing all important route information
        including distance, travel time, segment count, and start/end points.
        """
        # Get track segments - the PUIC values are now in the index
        track_segments = self.data.index.tolist()
        
        return {
            'total_distance_m': self.distance,
            'total_distance_km': self.distance_km,
            'estimated_travel_time_minutes': self.total_travel_time,
            'estimated_travel_time_hours': self.total_travel_time / 60.0,
            'segment_count': self.segment_count,
            'start_point': self.start,
            'end_point': self.end,
            'track_segments': track_segments,
            'has_start_end_coordinates': self.start is not None and self.end is not None
        }

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
