# MapServices

The MapServices module provides access to ProRail's public map services, allowing you to query and retrieve railway infrastructure data.

## Overview

ProRail provides public access to various railway infrastructure datasets through their map services at [mapservices.prorail.nl](https://mapservices.prorail.nl/). The OpenSpoor MapServices module makes it easy to discover, query, and work with this data.

## Key Classes

::: openspoor.mapservices.FeatureServerOverview
    options:
      show_root_heading: true
      show_source: false

::: openspoor.mapservices.MapServicesQuery
    options:
      show_root_heading: true
      show_source: false

::: openspoor.mapservices.FeatureSearchResults
    options:
      show_root_heading: true
      show_source: false

## Basic Usage

### Discovering Available Services

```python
from openspoor.mapservices import FeatureServerOverview

# Get overview of all available services
overview = FeatureServerOverview()
services = overview.get_featureserver_overview()

# Display available services
print(services[['description', 'layer_url']].head(10))
```

### Searching for Specific Data

```python
# Search for services containing specific keywords
stations = services[services['description'].str.contains('station', case=False)]
print(stations[['description', 'layer_url']])
```

### Querying Data

```python
from openspoor.mapservices import MapServicesQuery

# Query a specific layer
url = "https://mapservices.prorail.nl/arcgis/rest/services/Opendata/MapServer/0"
query = MapServicesQuery(url)
data = query.load_data()

print(f"Loaded {len(data)} features")
print(data.columns.tolist())
```

## Advanced Usage

### Filtering Data

```python
# Query with spatial filter
query = MapServicesQuery(url)
query.set_bbox(52.0, 4.0, 52.5, 4.5)  # Amsterdam area
amsterdam_data = query.load_data()
```

### Handling Large Datasets

```python
# For large datasets, consider using pagination
query = MapServicesQuery(url)
query.set_max_records(1000)  # Limit results
data = query.load_data()
```

### Working with Different Geometry Types

```python
# Load data with specific geometry requirements
query = MapServicesQuery(url)
data = query.load_data(return_m=True)  # Include M values for line strings
```

## Data Export

### Save to File

```python
from pathlib import Path

# Save data to GeoPackage
output_dir = Path("./output")
results = FeatureSearchResults(services)
gdf = results.write_gpkg(output_dir, entry_number=0)
```

### Convert to Different Formats

```python
# Save to different formats
data.to_file("stations.geojson", driver="GeoJSON")
data.to_file("stations.shp", driver="ESRI Shapefile")
```

## Error Handling

```python
from openspoor.mapservices import MapServicesQuery

try:
    query = MapServicesQuery(url)
    data = query.load_data()
except Exception as e:
    print(f"Error querying data: {e}")
    # Handle the error appropriately
```

## Available Data Types

Common datasets available through ProRail's map services include:

- **Stations**: Railway station locations and information
- **Tracks**: Railway track geometry and attributes
- **Signals**: Signal locations and types
- **Switches**: Track junction locations
- **Bridges**: Bridge locations and specifications
- **Tunnels**: Tunnel locations and details
- **Areas**: Railway operational areas

## Tips and Best Practices

!!! tip "Performance"
    - Use spatial filters to limit data to your area of interest
    - Set appropriate record limits for large datasets
    - Cache frequently used data locally

!!! warning "API Limitations"
    - Be respectful of ProRail's servers - don't make excessive requests
    - API endpoints and data formats may change over time
    - Some services may have usage limitations

!!! note "Data Quality"
    - Always validate data after loading
    - Check for missing or invalid geometries
    - Be aware that data is updated periodically by ProRail