# Visualizations

The Visualizations module provides tools for creating interactive maps of railway infrastructure data using Folium and other mapping libraries.

## Overview

OpenSpoor's visualization capabilities allow you to create interactive maps that display:

- Railway tracks and infrastructure
- Stations and points of interest  
- Operational areas and boundaries
- Custom markers and overlays
- ProRail aerial photography backgrounds

## Key Classes

::: openspoor.visualisations.TrackMap
    options:
      show_root_heading: true
      show_source: false

::: openspoor.visualisations.PlottingPoints
    options:
      show_root_heading: true
      show_source: false

::: openspoor.visualisations.PlottingLineStrings
    options:
      show_root_heading: true
      show_source: false

::: openspoor.visualisations.PlottingAreas
    options:
      show_root_heading: true
      show_source: false

## Basic Usage

### Creating a Simple Map

```python
from openspoor.visualisations import TrackMap
from openspoor.mapservices import MapServicesQuery

# Get some data
query = MapServicesQuery("https://mapservices.prorail.nl/arcgis/rest/services/Opendata/MapServer/0")
stations = query.load_data()

# Create a basic map
track_map = TrackMap()
track_map.show()  # In Jupyter notebook
```

### Adding Points

```python
from openspoor.visualisations import TrackMap, PlottingPoints

# Create map with station points
station_map = TrackMap([
    PlottingPoints(stations, popup='NAAM', color='red')
])
station_map.show()
```

### Adding Lines

```python
from openspoor.visualisations import PlottingLineStrings

# Get track data
tracks_query = MapServicesQuery("https://mapservices.prorail.nl/arcgis/rest/services/Opendata/MapServer/1")
tracks = tracks_query.load_data()

# Create map with tracks
track_map = TrackMap([
    PlottingLineStrings(tracks, color='blue', popup='GEOCODE')
])
track_map.show()
```

### Adding Areas

```python
from openspoor.visualisations import PlottingAreas

# Get area data
areas_query = MapServicesQuery("https://mapservices.prorail.nl/arcgis/rest/services/Opendata/MapServer/2")
areas = areas_query.load_data()

# Create map with areas
area_map = TrackMap([
    PlottingAreas(areas, color='green', popup='NAAM')
])
area_map.show()
```

## Advanced Visualizations

### Multi-layer Maps

```python
# Combine multiple data types
comprehensive_map = TrackMap([
    PlottingLineStrings(tracks, color='SUBCODE', popup='GEOCODE', buffersize=100),
    PlottingAreas(areas, popup='NAAM', color='red'),
    PlottingPoints(stations, popup=['NAAM', 'STATIONSGROOTTE'], color_column='STATIONSGROOTTE')
])
comprehensive_map.show()
```

### Custom Styling

```python
# Customize colors and appearance
styled_map = TrackMap([
    PlottingPoints(
        stations, 
        popup=['NAAM', 'STATIONSGROOTTE'],
        color_column='STATIONSGROOTTE',
        color_palette='viridis',
        marker_size=8
    ),
    PlottingLineStrings(
        tracks,
        color='blue',
        weight=3,
        opacity=0.7
    )
])
styled_map.show()
```

### Interactive Popups

```python
# Rich popup content
popup_map = TrackMap([
    PlottingPoints(
        stations,
        popup=['NAAM', 'STATIONSGROOTTE', 'PLAATS'],
        popup_template="<b>{NAAM}</b><br>Size: {STATIONSGROOTTE}<br>Location: {PLAATS}"
    )
])
popup_map.show()
```

## Map Customization

### Aerial Photography

TrackMap automatically includes ProRail's aerial photography:

```python
# Aerial photography is included by default
map_with_aerial = TrackMap()
# The map will show recent aerial photos of Dutch railway areas
```

### Custom Basemaps

```python
import folium

# Create map with custom basemap
custom_map = TrackMap()
folium.TileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    name='OpenStreetMap',
    attr='OpenStreetMap'
).add_to(custom_map)
```

### Map Controls

```python
# Add layer control
controlled_map = TrackMap([
    PlottingPoints(stations, popup='NAAM', color='red'),
    PlottingLineStrings(tracks, color='blue', popup='GEOCODE')
])

# Layer control is automatically added when multiple layers are present
controlled_map.show()
```

## Saving and Sharing

### Save to HTML

```python
# Save interactive map
track_map.save('railway_map.html')

# The HTML file can be opened in any web browser
```

### Export Images

```python
# For static images, you'll need additional tools
# This is typically done after saving to HTML and using browser automation
```

## Performance Optimization

### Large Datasets

```python
# Sample large datasets
large_dataset = large_dataset.sample(n=1000)

# Or filter by area
bbox_filtered = large_dataset.cx[4.0:5.0, 52.0:53.0]  # Amsterdam area
```

### Efficient Rendering

```python
# Use appropriate buffer sizes for lines
efficient_map = TrackMap([
    PlottingLineStrings(
        tracks, 
        color='blue', 
        buffersize=50,  # Smaller buffer for better performance
        simplify_tolerance=0.001  # Simplify geometries
    )
])
```

## Integration Examples

### With Coordinate Transformers

```python
from openspoor.transformers import TransformerGeocodeToCoordinates
import geopandas as gpd
from shapely.geometry import Point

# Transform coordinates and visualize
data = pd.DataFrame({
    'geocode': ['001', '002', '003'],
    'km': [10.5, 15.2, 8.7],
    'asset_type': ['Station', 'Bridge', 'Signal']
})

transformer = TransformerGeocodeToCoordinates('geocode', 'km', 'EPSG:28992')
transformed = transformer.transform(data)

# Create geometries
geometry = [Point(xy) for xy in zip(transformed.x, transformed.y)]
gdf = gpd.GeoDataFrame(transformed, geometry=geometry, crs='EPSG:28992')

# Visualize
asset_map = TrackMap([
    PlottingPoints(gdf, popup=['asset_type'], color_column='asset_type')
])
asset_map.show()
```

### With Network Analysis

```python
# Visualize shortest paths
from openspoor.network import shortest_path

# Calculate path (example)
path = shortest_path(start_point, end_point)

# Visualize path
path_map = TrackMap([
    PlottingLineStrings(railway_network, color='gray', opacity=0.5),
    PlottingLineStrings(path, color='red', weight=5, popup='Shortest Path')
])
path_map.show()
```

## Troubleshooting

### Common Issues

**Map Not Displaying**
```python
# Ensure you're in a Jupyter environment or save to HTML
track_map.show()  # Jupyter
track_map.save('map.html')  # Save to file
```

**Performance Issues**
```python
# Reduce data size
data_sample = data.sample(n=500)
# Or use spatial filtering
data_filtered = data.cx[lon_min:lon_max, lat_min:lat_max]
```

**Memory Issues with Large Datasets**
```python
# Process in chunks
chunk_size = 1000
for i in range(0, len(large_data), chunk_size):
    chunk = large_data.iloc[i:i+chunk_size]
    # Process chunk
```

## Tips and Best Practices

!!! tip "Performance"
    - Sample large datasets before visualization
    - Use appropriate buffer sizes for line features
    - Consider the zoom level when setting detail levels

!!! note "Coordinate Systems"
    - Ensure your data is in the correct coordinate system
    - TrackMap expects data in geographic coordinates (WGS84) or will transform automatically

!!! warning "Browser Limitations"
    - Very large datasets may cause browser performance issues
    - Consider using clustering for dense point data
    - Test maps in different browsers