# Quick Start

This guide will get you up and running with OpenSpoor in just a few minutes.

## Basic Usage

### Import OpenSpoor

```python
import openspoor
from openspoor.mapservices import MapServicesQuery
from openspoor.visualisations import TrackMap, PlottingLineStrings
```

### Query Railway Data

Get railway tracks data from ProRail's map services:

```python
# Find available map services
from openspoor.mapservices import FeatureServerOverview

# Get an overview of available services
overview = FeatureServerOverview()
services = overview.get_featureserver_overview()
print(services.head())

# Query specific data (example: stations)
query = MapServicesQuery("https://mapservices.prorail.nl/arcgis/rest/services/Opendata/MapServer/0")
stations = query.load_data()
print(f"Found {len(stations)} stations")
```

### Create Your First Map

```python
# Create a simple map with railway tracks
from openspoor.visualisations import TrackMap, PlottingLineStrings

# Get some track data (example)
tracks_query = MapServicesQuery("https://mapservices.prorail.nl/arcgis/rest/services/Opendata/MapServer/1")
tracks = tracks_query.load_data()

# Create and display map
track_map = TrackMap([
    PlottingLineStrings(tracks, color='blue', popup='GEOCODE')
])
track_map.show()  # In Jupyter notebook
# track_map.save('my_map.html')  # Save to file
```

### Transform Coordinates

Convert between geocode-kilometer references and coordinates:

```python
import pandas as pd
from openspoor.transformers import TransformerGeocodeToCoordinates

# Sample data with geocode and kilometer information
data = pd.DataFrame({
    'geocode': ['001', '002', '003'],
    'kilometrering': [10.5, 15.2, 8.7]
})

# Transform to RD coordinates
transformer = TransformerGeocodeToCoordinates(
    geocode_column='geocode', 
    geocode_km_column='kilometrering',
    coordinate_system='EPSG:28992'  # RD New
)

# Add x, y coordinates
data_with_coords = transformer.transform(data)
print(data_with_coords[['geocode', 'kilometrering', 'x', 'y']])
```

## Interactive Examples

### Example 1: Station Map

```python
# Create an interactive map showing all stations in the Netherlands
from openspoor.mapservices import MapServicesQuery
from openspoor.visualisations import TrackMap, PlottingPoints

# Query stations data
stations_query = MapServicesQuery("https://mapservices.prorail.nl/arcgis/rest/services/Opendata/MapServer/0")
stations = stations_query.load_data()

# Create map with station markers
station_map = TrackMap([
    PlottingPoints(
        stations, 
        popup=['NAAM', 'STATIONSGROOTTE'], 
        color_column='STATIONSGROOTTE'
    )
])
station_map.show()
```

### Example 2: Multi-layer Map

```python
# Combine multiple data layers
tracks_query = MapServicesQuery("https://mapservices.prorail.nl/arcgis/rest/services/Opendata/MapServer/1")
tracks = tracks_query.load_data()

areas_query = MapServicesQuery("https://mapservices.prorail.nl/arcgis/rest/services/Opendata/MapServer/2")
areas = areas_query.load_data()

# Create comprehensive map
multi_map = TrackMap([
    PlottingLineStrings(tracks, color='SUBCODE', popup='GEOCODE', buffersize=100),
    PlottingAreas(areas, popup='NAAM', color='red'),
    PlottingPoints(stations, popup=['NAAM', 'STATIONSGROOTTE'], color_column='STATIONSGROOTTE')
])
multi_map.show()
```

## Next Steps

Now that you've seen the basics, explore more advanced features:

- **[MapServices Guide](user-guide/mapservices.md)**: Learn to query and use ProRail's data services
- **[Visualizations Guide](user-guide/visualizations.md)**: Create advanced interactive maps
- **[Transformers Guide](user-guide/transformers.md)**: Master coordinate transformations
- **[Demo Notebook](examples/demo-notebook.md)**: See comprehensive real-world examples

## Common Patterns

### Save Maps for Sharing

```python
# Save interactive map as HTML
track_map.save('railway_map.html')

# The HTML file can be opened in any web browser
# and shared with others
```

### Handle Large Datasets

```python
# For large datasets, consider filtering or sampling
large_dataset = large_dataset.sample(n=1000)  # Sample 1000 points
# or
filtered_data = large_dataset[large_dataset['some_column'] > threshold]
```

### Error Handling

```python
try:
    data = query.load_data()
except Exception as e:
    print(f"Error loading data: {e}")
    # Handle the error appropriately
```

!!! tip "Performance Tips"
    - Use appropriate buffer sizes for line visualizations
    - Sample large datasets before visualization
    - Cache frequently used data
    - Consider the map extent when querying data