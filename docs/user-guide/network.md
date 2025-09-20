# Network Analysis

The Network module provides tools for analyzing railway network connectivity, finding shortest paths, and working with railway network topology.

## Overview

Railway networks are complex graph structures where tracks, switches, and stations form nodes and edges. The Network module helps you:

- Find shortest paths between locations
- Analyze network connectivity
- Work with railway topology
- Calculate distances and travel times

## Key Features

- **Shortest Path Calculation**: Find optimal routes between railway locations
- **Network Topology**: Understand track connections and junctions
- **Distance Calculations**: Measure distances along railway routes
- **Connectivity Analysis**: Identify connected components and isolated sections

## Basic Usage

### Finding Shortest Paths

```python
from openspoor.network import shortest_path
import geopandas as gpd

# Load railway network data
network_query = MapServicesQuery("https://mapservices.prorail.nl/arcgis/rest/services/Opendata/MapServer/1")
railway_network = network_query.load_data()

# Define start and end points
start_point = (52.3676, 4.9041)  # Amsterdam Central
end_point = (52.0907, 5.1214)   # Utrecht Central

# Find shortest path
path = shortest_path(railway_network, start_point, end_point)
print(f"Path length: {len(path)} segments")
```

### Network Analysis

```python
from openspoor.network import NetworkAnalyzer

# Analyze network properties
analyzer = NetworkAnalyzer(railway_network)

# Get network statistics
stats = analyzer.get_network_statistics()
print(f"Total network length: {stats['total_length']} km")
print(f"Number of nodes: {stats['node_count']}")
print(f"Number of edges: {stats['edge_count']}")
```

## Advanced Analysis

### Route Optimization

```python
# Find multiple routes with different criteria
routes = analyzer.find_alternative_routes(
    start_point, 
    end_point,
    max_routes=3,
    criteria=['shortest', 'fastest', 'scenic']
)

for i, route in enumerate(routes):
    print(f"Route {i+1}: {route['distance']} km, {route['type']}")
```

### Accessibility Analysis

```python
# Find all stations within a certain distance
accessible_stations = analyzer.find_accessible_locations(
    center_point=start_point,
    max_distance=50,  # km
    location_type='station'
)

print(f"Found {len(accessible_stations)} stations within 50km")
```

### Network Visualization

```python
from openspoor.visualisations import TrackMap, PlottingLineStrings

# Visualize shortest path
path_map = TrackMap([
    PlottingLineStrings(
        railway_network, 
        color='lightblue', 
        weight=2, 
        opacity=0.6,
        popup='Background Network'
    ),
    PlottingLineStrings(
        path, 
        color='red', 
        weight=5, 
        opacity=0.9,
        popup='Shortest Path'
    )
])
path_map.show()
```

## Working with Specific Network Types

### High-Speed Lines

```python
# Filter for high-speed railway lines
high_speed_network = railway_network[
    railway_network['MAXSNELHEID'] >= 200
]

# Analyze high-speed connectivity
hs_analyzer = NetworkAnalyzer(high_speed_network)
hs_paths = hs_analyzer.find_shortest_path(start_point, end_point)
```

### Freight Networks

```python
# Filter for freight-capable lines
freight_network = railway_network[
    railway_network['FREIGHT_CAPABLE'] == True
]

# Find freight routes
freight_analyzer = NetworkAnalyzer(freight_network)
freight_path = freight_analyzer.find_shortest_path(start_point, end_point)
```

## Performance Considerations

### Large Networks

```python
# For large networks, consider spatial indexing
analyzer = NetworkAnalyzer(railway_network, use_spatial_index=True)

# Or limit analysis to specific regions
bbox = (4.0, 52.0, 5.0, 53.0)  # Amsterdam region
regional_network = railway_network.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
regional_analyzer = NetworkAnalyzer(regional_network)
```

### Caching Results

```python
# Cache frequently used calculations
analyzer.enable_caching()

# Subsequent calls with same parameters will be faster
path1 = analyzer.find_shortest_path(point_a, point_b)
path2 = analyzer.find_shortest_path(point_a, point_b)  # Retrieved from cache
```

## Integration with Other Modules

### With Coordinate Transformers

```python
from openspoor.transformers import TransformerGeocodeToCoordinates

# Convert geocode references to coordinates for network analysis
geocode_data = pd.DataFrame({
    'start_geocode': ['001', '002'],
    'start_km': [10.5, 15.2],
    'end_geocode': ['003', '004'],
    'end_km': [8.7, 12.1]
})

transformer = TransformerGeocodeToCoordinates('start_geocode', 'start_km', 'EPSG:4326')
start_coords = transformer.transform(geocode_data[['start_geocode', 'start_km']])

transformer = TransformerGeocodeToCoordinates('end_geocode', 'end_km', 'EPSG:4326')
end_coords = transformer.transform(geocode_data[['end_geocode', 'end_km']])

# Use coordinates for network analysis
for i in range(len(start_coords)):
    start = (start_coords.iloc[i]['x'], start_coords.iloc[i]['y'])
    end = (end_coords.iloc[i]['x'], end_coords.iloc[i]['y'])
    path = analyzer.find_shortest_path(start, end)
```

### With Visualizations

```python
# Create comprehensive network visualization
network_map = TrackMap([
    # Background network
    PlottingLineStrings(railway_network, color='lightgray', weight=1),
    # Calculated paths
    PlottingLineStrings(calculated_paths, color='red', weight=3),
    # Key stations
    PlottingPoints(major_stations, color='blue', popup='NAAM')
])
network_map.show()
```

## Error Handling

```python
try:
    path = analyzer.find_shortest_path(start_point, end_point)
    if not path:
        print("No path found between the specified points")
except NetworkError as e:
    print(f"Network analysis error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Tips and Best Practices

!!! tip "Network Preparation"
    - Ensure network data has proper topology (connected segments)
    - Clean duplicate or overlapping segments
    - Validate that start/end points are accessible from the network

!!! warning "Performance"
    - Large networks can be computationally expensive
    - Consider using spatial indexing for frequent queries
    - Cache results when possible

!!! note "Coordinate Systems"
    - Network analysis works best with projected coordinate systems
    - Ensure consistent coordinate systems across all data
    - Consider using appropriate projections for distance calculations

## Common Use Cases

### Service Planning

```python
# Find optimal routes for new services
service_routes = analyzer.find_service_routes(
    stations_to_connect=['Amsterdam', 'Utrecht', 'Rotterdam'],
    service_type='intercity',
    constraints={'max_detour': 1.2, 'min_frequency': 4}
)
```

### Infrastructure Analysis

```python
# Identify critical network segments
critical_segments = analyzer.find_critical_infrastructure(
    importance_metric='betweenness_centrality'
)

# Analyze impact of closures
closure_impact = analyzer.analyze_closure_impact(
    segment_id='segment_123',
    affected_services=['intercity', 'regional']
)
```

### Capacity Analysis

```python
# Analyze network capacity constraints
capacity_analysis = analyzer.analyze_capacity(
    time_period='peak_hours',
    service_types=['passenger', 'freight']
)
```