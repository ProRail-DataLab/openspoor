# Use Cases

This page showcases real-world applications and use cases for OpenSpoor, demonstrating how the library can be used to solve practical problems in railway infrastructure management and analysis.

## Infrastructure Management

### Asset Location Mapping

**Problem**: Railway operators need to map asset locations from internal reference systems to geographic coordinates for integration with GIS systems.

**Solution**:
```python
from openspoor.transformers import TransformerGeocodeToCoordinates
import pandas as pd

# Load asset inventory
assets = pd.read_csv('railway_assets.csv')
# Contains: asset_id, geocode, kilometrering, asset_type, maintenance_due

# Transform to geographic coordinates
transformer = TransformerGeocodeToCoordinates('geocode', 'kilometrering', 'EPSG:4326')
assets_with_coords = transformer.transform(assets)

# Export for GIS integration
assets_with_coords.to_file('assets_for_gis.geojson', driver='GeoJSON')
```

**Benefits**:
- Enables integration with modern GIS systems
- Supports mobile workforce with GPS-enabled devices
- Facilitates spatial analysis and reporting

### Maintenance Planning Visualization

**Problem**: Maintenance teams need to visualize upcoming maintenance activities on a map to optimize routing and resource allocation.

**Solution**:
```python
from openspoor.visualisations import TrackMap, PlottingPoints, PlottingLineStrings

# Create maintenance planning map
maintenance_map = TrackMap([
    PlottingLineStrings(railway_network, color='lightgray', weight=2),
    PlottingPoints(
        maintenance_locations,
        color_column='priority',
        popup=['asset_id', 'maintenance_type', 'due_date'],
        color_palette='RdYlGn_r'  # Red for high priority
    )
])

maintenance_map.save('maintenance_planning.html')
```

**Benefits**:
- Visual planning of maintenance activities
- Optimized routing for maintenance crews
- Priority-based resource allocation

## Operational Planning

### Service Route Analysis

**Problem**: Planning new passenger services requires analysis of existing infrastructure and identification of optimal routes.

**Solution**:
```python
from openspoor.network import shortest_path
from openspoor.mapservices import MapServicesQuery

# Load infrastructure data
stations_query = MapServicesQuery("stations_url")
stations = stations_query.load_data()

tracks_query = MapServicesQuery("tracks_url")
tracks = tracks_query.load_data()

# Analyze potential routes between major stations
major_stations = stations[stations['STATIONSGROOTTE'] == 'groot']

for i, station_a in major_stations.iterrows():
    for j, station_b in major_stations.iterrows():
        if i < j:  # Avoid duplicates
            route = shortest_path(tracks, station_a.geometry, station_b.geometry)
            print(f"Route {station_a['NAAM']} - {station_b['NAAM']}: {route.length:.1f} km")
```

**Benefits**:
- Data-driven route planning
- Infrastructure capacity analysis
- Service optimization

### Capacity Analysis

**Problem**: Understanding network capacity constraints to optimize train scheduling and identify bottlenecks.

**Solution**:
```python
# Analyze track utilization
high_capacity_tracks = tracks[tracks['DAILY_TRAINS'] > 200]
bottlenecks = tracks[tracks['CAPACITY_RATIO'] > 0.9]

# Visualize capacity constraints
capacity_map = TrackMap([
    PlottingLineStrings(tracks, color='CAPACITY_RATIO', popup='track_info'),
    PlottingLineStrings(bottlenecks, color='red', weight=5, popup='Bottleneck')
])
```

## Safety and Compliance

### Signal Coverage Analysis

**Problem**: Ensuring adequate signal coverage and identifying potential safety issues in the railway network.

**Solution**:
```python
# Load signal locations
signals_query = MapServicesQuery("signals_url")
signals = signals_query.load_data()

# Analyze signal spacing
signal_coverage = analyze_signal_coverage(tracks, signals)
coverage_gaps = signal_coverage[signal_coverage['gap_distance'] > 2000]  # > 2km gaps

# Visualize coverage gaps
safety_map = TrackMap([
    PlottingLineStrings(tracks, color='blue'),
    PlottingPoints(signals, color='green', popup='signal_info'),
    PlottingLineStrings(coverage_gaps, color='red', weight=6, popup='Coverage Gap')
])
```

**Benefits**:
- Proactive safety analysis
- Compliance monitoring
- Risk identification

### Emergency Response Planning

**Problem**: Planning emergency response routes and identifying alternative paths when sections are blocked.

**Solution**:
```python
# Simulate track closure
blocked_section = "001_10.5_15.2"  # geocode with km range
alternative_routes = find_alternative_routes(
    tracks, 
    blocked_sections=[blocked_section],
    origin=emergency_depot,
    destinations=stations_in_area
)

# Visualize emergency response options
emergency_map = TrackMap([
    PlottingLineStrings(tracks, color='lightgray'),
    PlottingLineStrings(blocked_tracks, color='red', popup='BLOCKED'),
    PlottingLineStrings(alternative_routes, color='blue', popup='Alternative Route')
])
```

## Research and Analysis

### Historical Infrastructure Analysis

**Problem**: Researchers need to analyze changes in railway infrastructure over time.

**Solution**:
```python
from openspoor.spoortakmodel import SpoortakModelsData

# Load historical data
historical_data = SpoortakModelsData(include_historical=True)
spoortakken_2020 = historical_data.load_spoortak_models(year=2020)
spoortakken_2024 = historical_data.load_spoortak_models(year=2024)

# Analyze changes
changes = analyze_infrastructure_changes(spoortakken_2020, spoortakken_2024)

# Visualize evolution
evolution_map = TrackMap([
    PlottingLineStrings(changes['removed'], color='red', popup='Removed'),
    PlottingLineStrings(changes['added'], color='green', popup='Added'),
    PlottingLineStrings(changes['modified'], color='orange', popup='Modified')
])
```

### Network Connectivity Studies

**Problem**: Understanding how well different parts of the railway network are connected.

**Solution**:
```python
# Analyze network connectivity
connectivity_metrics = analyze_network_connectivity(tracks)
isolated_components = find_isolated_components(tracks)

# Calculate accessibility indices
accessibility = calculate_accessibility_index(stations, tracks)

# Visualize connectivity
connectivity_map = TrackMap([
    PlottingLineStrings(tracks, color='component_id'),
    PlottingPoints(stations, color='accessibility_score', popup='accessibility_info')
])
```

## Integration Examples

### Integration with External Systems

**Problem**: Integrating OpenSpoor data with existing enterprise systems.

**Solution**:
```python
import requests
from openspoor.transformers import TransformerGeocodeToCoordinates

# Sync with asset management system
def sync_with_asset_system():
    # Get data from OpenSpoor
    assets_coords = transformer.transform(internal_assets)
    
    # Update external system via API
    for _, asset in assets_coords.iterrows():
        update_data = {
            'asset_id': asset['asset_id'],
            'latitude': asset['y'],
            'longitude': asset['x'],
            'last_updated': datetime.now().isoformat()
        }
        
        response = requests.post(
            'https://asset-system.company.com/api/locations',
            json=update_data
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to update asset {asset['asset_id']}")

# Schedule regular synchronization
sync_with_asset_system()
```

### Real-time Monitoring Dashboards

**Problem**: Creating real-time dashboards for operational control centers.

**Solution**:
```python
import streamlit as st
from openspoor.visualisations import TrackMap

# Streamlit dashboard
st.title("Railway Operations Dashboard")

# Real-time data refresh
if st.button("Refresh Data"):
    current_positions = get_realtime_train_positions()
    incidents = get_current_incidents()

# Create live map
live_map = TrackMap([
    PlottingLineStrings(tracks, color='lightgray'),
    PlottingPoints(current_positions, color='blue', popup='train_info'),
    PlottingPoints(incidents, color='red', popup='incident_details')
])

# Display in Streamlit
st.components.v1.html(live_map._repr_html_(), height=600)
```

## Mobile Applications

### Field Worker Apps

**Problem**: Field workers need mobile access to infrastructure data with offline capabilities.

**Solution**:
```python
# Generate offline map data
def generate_offline_maps(region_bbox):
    # Get relevant data for region
    region_tracks = tracks.cx[region_bbox[0]:region_bbox[2], 
                             region_bbox[1]:region_bbox[3]]
    region_assets = assets.cx[region_bbox[0]:region_bbox[2], 
                             region_bbox[1]:region_bbox[3]]
    
    # Create offline map
    offline_map = TrackMap([
        PlottingLineStrings(region_tracks, popup='track_info'),
        PlottingPoints(region_assets, popup='asset_info')
    ])
    
    offline_map.save(f'offline_map_{region_id}.html')
    
    # Export data for mobile app
    region_tracks.to_file(f'tracks_{region_id}.geojson', driver='GeoJSON')
    region_assets.to_file(f'assets_{region_id}.geojson', driver='GeoJSON')

# Generate maps for all operational regions
for region in operational_regions:
    generate_offline_maps(region['bbox'])
```

## Performance Optimization Cases

### Large Dataset Handling

**Problem**: Processing nationwide railway data efficiently.

**Solution**:
```python
# Optimize for large datasets
def process_large_dataset():
    # Use chunking for memory efficiency
    chunk_size = 10000
    
    for chunk in pd.read_csv('large_asset_file.csv', chunksize=chunk_size):
        # Transform coordinates in chunks
        chunk_transformed = transformer.transform(chunk)
        
        # Process and save results
        chunk_transformed.to_csv('output.csv', mode='a', header=False)
    
    # Use spatial indexing for queries
    spatial_index = tracks.sindex
    
    # Efficient spatial queries
    nearby_tracks = tracks.iloc[list(spatial_index.intersection(query_bbox))]
```

### Caching Strategies

**Problem**: Avoiding repeated expensive operations.

**Solution**:
```python
import functools
import pickle

# Cache expensive transformations
@functools.lru_cache(maxsize=1000)
def cached_transformation(geocode, km, coord_system):
    transformer = TransformerGeocodeToCoordinates('geocode', 'km', coord_system)
    return transformer.transform_single(geocode, km)

# Persistent caching
def save_processed_data(data, cache_file):
    with open(cache_file, 'wb') as f:
        pickle.dump(data, f)

def load_cached_data(cache_file):
    try:
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None
```

## Best Practices from Real Projects

### Error Handling in Production

```python
import logging
from contextlib import contextmanager

@contextmanager
def openspoor_error_handling():
    try:
        yield
    except MapServicesError as e:
        logging.error(f"Map service unavailable: {e}")
        # Fallback to cached data
        return load_cached_data()
    except TransformationError as e:
        logging.error(f"Coordinate transformation failed: {e}")
        # Skip problematic records
        return None
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise

# Usage in production
with openspoor_error_handling():
    data = query.load_data()
    transformed = transformer.transform(data)
```

### Data Validation Workflows

```python
def validate_openspoor_data(data):
    validation_results = {
        'valid_geometries': 0,
        'invalid_geometries': 0,
        'missing_attributes': 0,
        'errors': []
    }
    
    for idx, row in data.iterrows():
        # Validate geometry
        if row.geometry is None or not row.geometry.is_valid:
            validation_results['invalid_geometries'] += 1
            validation_results['errors'].append(f"Invalid geometry at row {idx}")
        else:
            validation_results['valid_geometries'] += 1
    
    return validation_results
```

These use cases demonstrate OpenSpoor's versatility in solving real-world railway infrastructure challenges. The library's modular design allows for flexible integration into existing workflows while providing powerful tools for spatial analysis and visualization.