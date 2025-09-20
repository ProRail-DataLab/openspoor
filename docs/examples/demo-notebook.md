# Demo Notebook

This page showcases comprehensive examples from the OpenSpoor demonstration notebook, illustrating real-world usage patterns and capabilities.

## Overview

The demo notebook demonstrates OpenSpoor's functionality through practical examples:

- Setting up TrackMap visualizations
- Querying ProRail map services
- Coordinate transformations
- Network analysis and pathfinding
- Custom marker and styling options

!!! note "Interactive Examples"
    The original demo notebook is available in the `demo_notebook/` folder of the repository. These examples show the expected code and output.

## Demo 1: Basic TrackMap Setup

### 1a) Complete Railway Infrastructure Map

Setting up a comprehensive map with all ProRail infrastructure elements:

```python
from openspoor.mapservices import MapServicesQuery
from openspoor.visualisations import TrackMap, PlottingLineStrings, PlottingAreas, PlottingPoints

# Query various infrastructure data
gebieden_query = MapServicesQuery("https://mapservices.prorail.nl/arcgis/rest/services/Opendata/MapServer/2")
gebieden = gebieden_query.load_data()

stations_query = MapServicesQuery("https://mapservices.prorail.nl/arcgis/rest/services/Opendata/MapServer/0")
stations = stations_query.load_data()

hartlijnen_query = MapServicesQuery("https://mapservices.prorail.nl/arcgis/rest/services/Opendata/MapServer/1")
hartlijnen = hartlijnen_query.load_data()

# Create comprehensive map
m = TrackMap([
    PlottingLineStrings(hartlijnen, color='SUBCODE', popup='GEOCODE', buffersize=100),
    PlottingAreas(gebieden, popup='NAAM', color='red'),
    PlottingPoints(stations, popup=['NAAM', 'STATIONSGROOTTE'], color_column='STATIONSGROOTTE')
])

m.show(notebook=True)
```

**Expected Result**: An interactive map showing:
- Railway tracks colored by subcode
- Operational areas in red
- Stations with popups showing name and size
- ProRail aerial photography background

### 1b) Customized Markers

Creating maps with custom marker styling and enhanced interactivity:

```python
# Custom marker styling for different station types
station_colors = {
    'groot': 'red',
    'middel': 'orange', 
    'klein': 'yellow'
}

# Enhanced station visualization
enhanced_map = TrackMap([
    PlottingPoints(
        stations,
        popup=['NAAM', 'STATIONSGROOTTE', 'PLAATS'],
        color_column='STATIONSGROOTTE',
        marker_size=lambda x: {'groot': 12, 'middel': 8, 'klein': 6}.get(x, 6),
        tooltip='NAAM'
    )
])

enhanced_map.show(notebook=True)
```

## Demo 2: Coordinate Transformations

### 2a) Geocode to Coordinates

Converting railway reference systems to geographic coordinates:

```python
import pandas as pd
from openspoor.transformers import TransformerGeocodeToCoordinates

# Sample railway reference data
data = pd.DataFrame({
    'geocode': ['001', '002', '003', '004', '005'],
    'kilometrering': [10.5, 15.2, 8.7, 12.1, 20.3],
    'asset_type': ['Station', 'Bridge', 'Signal', 'Switch', 'Tunnel'],
    'description': ['Central Station', 'River Bridge', 'Entry Signal', 'Junction A', 'City Tunnel']
})

# Transform to RD coordinates
rd_transformer = TransformerGeocodeToCoordinates(
    geocode_column='geocode',
    geocode_km_column='kilometrering', 
    coordinate_system='EPSG:28992'
)

rd_result = rd_transformer.transform(data)
print("RD Coordinates:")
print(rd_result[['geocode', 'kilometrering', 'x', 'y', 'asset_type']])

# Transform to GPS coordinates
gps_transformer = TransformerGeocodeToCoordinates(
    geocode_column='geocode',
    geocode_km_column='kilometrering',
    coordinate_system='EPSG:4326'
)

gps_result = gps_transformer.transform(data)
print("\\nGPS Coordinates:")
print(gps_result[['geocode', 'kilometrering', 'x', 'y', 'asset_type']])
```

### 2b) Visualizing Transformed Points

Creating maps from transformed coordinate data:

```python
import geopandas as gpd
from shapely.geometry import Point

# Create geometries from transformed coordinates
geometry = [Point(xy) for xy in zip(rd_result.x, rd_result.y)]
gdf = gpd.GeoDataFrame(rd_result, geometry=geometry, crs='EPSG:28992')

# Visualize transformed points
transformation_map = TrackMap([
    PlottingPoints(
        gdf, 
        popup=['description', 'asset_type', 'geocode', 'kilometrering'],
        color_column='asset_type',
        tooltip='description'
    )
])

transformation_map.show(notebook=True)
```

## Demo 3: Point-to-Track Analysis

Finding track information for given coordinates:

```python
# Define test coordinate cases
test_cases = pd.DataFrame({
    'case_id': [1, 2, 3, 4, 5],
    'x': [125000, 130000, 135000, 140000, 145000],
    'y': [485000, 490000, 495000, 500000, 505000],
    'description': [
        'Near track point',
        'Inside switch (not supported)',
        'On crossing',
        'Near crossing', 
        'Outside buffer distance'
    ]
})

# Find track information for each point
for index, case in test_cases.iterrows():
    point = (case['x'], case['y'])
    # track_info = find_track_info(point)  # Hypothetical function
    print(f"Case {case['case_id']}: {case['description']}")
    # print(f"  Track: {track_info.get('spoortak', 'Not found')}")
    # print(f"  Geocode: {track_info.get('geocode', 'Not found')}")
```

## Demo 4: Network Analysis

### 4a) Shortest Path Calculation

Finding optimal routes through the railway network:

```python
from openspoor.network import shortest_path

# Define start and end points
start_point = (52.3676, 4.9041)  # Amsterdam Central
end_point = (52.0907, 5.1214)   # Utrecht Central

# Calculate shortest path
path = shortest_path(hartlijnen, start_point, end_point)

# Visualize the path
path_map = TrackMap([
    PlottingLineStrings(
        hartlijnen, 
        color='lightblue', 
        weight=2, 
        opacity=0.6,
        popup='Network'
    ),
    PlottingLineStrings(
        path, 
        color='red', 
        weight=5, 
        opacity=0.9,
        popup='Shortest Path'
    )
])

path_map.show(notebook=True)
```

### 4b) Route Analysis with Multiple Options

Comparing different routing strategies:

```python
# Calculate multiple route options
routes = {
    'shortest': shortest_path(hartlijnen, start_point, end_point, strategy='distance'),
    'fastest': shortest_path(hartlijnen, start_point, end_point, strategy='time'),
    'scenic': shortest_path(hartlijnen, start_point, end_point, strategy='scenic')
}

# Create multi-route visualization
route_colors = {'shortest': 'red', 'fastest': 'blue', 'scenic': 'green'}

route_layers = [
    PlottingLineStrings(hartlijnen, color='lightgray', weight=1, opacity=0.5)
]

for route_type, route_data in routes.items():
    route_layers.append(
        PlottingLineStrings(
            route_data,
            color=route_colors[route_type],
            weight=4,
            popup=f'{route_type.title()} Route'
        )
    )

multi_route_map = TrackMap(route_layers)
multi_route_map.show(notebook=True)
```

## Demo 5: Advanced Filtering and Analysis

### 5a) Regional Analysis

Focusing on specific geographic regions:

```python
# Define region of interest (Amsterdam area)
amsterdam_bbox = (4.7, 52.2, 5.0, 52.5)

# Filter data to region
amsterdam_tracks = hartlijnen.cx[amsterdam_bbox[0]:amsterdam_bbox[2], 
                                amsterdam_bbox[1]:amsterdam_bbox[3]]
amsterdam_stations = stations.cx[amsterdam_bbox[0]:amsterdam_bbox[2], 
                                amsterdam_bbox[1]:amsterdam_bbox[3]]

# Create regional map
regional_map = TrackMap([
    PlottingLineStrings(amsterdam_tracks, color='blue', popup='GEOCODE'),
    PlottingPoints(amsterdam_stations, popup='NAAM', color='red')
])

regional_map.show(notebook=True)
```

### 5b) Infrastructure Type Analysis

Analyzing different types of railway infrastructure:

```python
# Filter by infrastructure characteristics
high_speed_tracks = hartlijnen[hartlijnen['MAXSNELHEID'] >= 140]
major_stations = stations[stations['STATIONSGROOTTE'] == 'groot']

# Create infrastructure analysis map
infra_map = TrackMap([
    PlottingLineStrings(
        high_speed_tracks, 
        color='purple', 
        weight=4,
        popup=['GEOCODE', 'MAXSNELHEID']
    ),
    PlottingPoints(
        major_stations,
        color='gold',
        marker_size=10,
        popup=['NAAM', 'STATIONSGROOTTE']
    )
])

infra_map.show(notebook=True)
```

## Demo 6: Custom Styling and Interactivity

### 6a) Dynamic Color Schemes

Using data-driven styling for enhanced visualization:

```python
# Create custom color mapping
speed_colors = {
    'zeer_hoog': '#8B0000',  # Dark red for very high speed
    'hoog': '#FF4500',       # Orange red for high speed  
    'middel': '#FFD700',     # Gold for medium speed
    'laag': '#90EE90'        # Light green for low speed
}

# Apply speed-based coloring
def get_speed_category(speed):
    if speed >= 200: return 'zeer_hoog'
    elif speed >= 140: return 'hoog'
    elif speed >= 80: return 'middel'
    else: return 'laag'

hartlijnen['speed_category'] = hartlijnen['MAXSNELHEID'].apply(get_speed_category)

# Create speed-themed map
speed_map = TrackMap([
    PlottingLineStrings(
        hartlijnen,
        color='speed_category',
        color_mapping=speed_colors,
        popup=['GEOCODE', 'MAXSNELHEID', 'speed_category'],
        weight=3
    )
])

speed_map.show(notebook=True)
```

### 6b) Interactive Popups with Rich Content

Creating detailed, informative popups:

```python
# Enhanced popup content
def create_rich_popup(row):
    return f"""
    <div style="font-family: Arial; font-size: 12px;">
        <h4 style="margin: 0; color: #2E86AB;">{row['NAAM']}</h4>
        <hr style="margin: 5px 0;">
        <p><b>Type:</b> {row['STATIONSGROOTTE']}</p>
        <p><b>Location:</b> {row['PLAATS']}</p>
        <p><b>Coordinates:</b> {row.geometry.x:.2f}, {row.geometry.y:.2f}</p>
    </div>
    """

# Apply rich popups
rich_popup_map = TrackMap([
    PlottingPoints(
        stations,
        popup_function=create_rich_popup,
        color_column='STATIONSGROOTTE'
    )
])

rich_popup_map.show(notebook=True)
```

## Demo 7: Export and Sharing

### 7a) Saving Maps

Exporting maps for sharing and embedding:

```python
# Save interactive map
comprehensive_map.save('railway_infrastructure_map.html')

# Save with custom title
path_map.save('shortest_path_analysis.html', title='Railway Route Analysis')

print("Maps saved successfully!")
print("- railway_infrastructure_map.html")
print("- shortest_path_analysis.html")
```

### 7b) Data Export

Exporting processed data for further analysis:

```python
# Export transformed coordinate data
rd_result.to_csv('railway_assets_rd_coordinates.csv', index=False)
gps_result.to_csv('railway_assets_gps_coordinates.csv', index=False)

# Export spatial data
gdf.to_file('railway_assets.geojson', driver='GeoJSON')
gdf.to_file('railway_assets.gpkg', driver='GPKG')

print("Data exported successfully!")
print("- CSV files with coordinate data")
print("- GeoJSON and GeoPackage spatial data")
```

## Performance Tips

For working with large datasets:

```python
# Sample large datasets
large_tracks_sample = large_tracks.sample(n=1000)

# Use spatial indexing for better performance
spatial_index = large_tracks.sindex

# Filter by bounding box before detailed operations
bbox_filtered = large_tracks.cx[xmin:xmax, ymin:ymax]
```

## Next Steps

After exploring these examples:

1. **Try the interactive notebook**: Run `demo_notebook/openspoor_example.ipynb`
2. **Experiment with your own data**: Apply these patterns to your datasets
3. **Explore the API**: Check the [API Reference](../api/index.md) for more details
4. **Build custom workflows**: Combine different modules for your specific use cases

!!! tip "Best Practices"
    - Always validate your data before visualization
    - Use appropriate coordinate systems for your use case
    - Consider performance implications with large datasets
    - Save frequently used queries and transformations