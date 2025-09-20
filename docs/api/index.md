# API Reference

This section provides comprehensive API documentation for all OpenSpoor modules.

## Overview

OpenSpoor is organized into several main modules:

- **[MapServices](#mapservices)**: Query ProRail's public map services
- **[Transformers](#transformers)**: Convert between coordinate systems
- **[Visualizations](#visualizations)**: Create interactive maps
- **[Network](#network)**: Analyze railway network topology
- **[Spoortak Models](#spoortak-models)**: Work with track sections

## MapServices

The MapServices module provides access to ProRail's public geospatial data services.

### Core Classes

::: openspoor.mapservices.FeatureServerOverview

::: openspoor.mapservices.MapServicesQuery

::: openspoor.mapservices.FeatureSearchResults

### Usage Example

```python
from openspoor.mapservices import FeatureServerOverview, MapServicesQuery

# Discover available services
overview = FeatureServerOverview()
services = overview.get_featureserver_overview()

# Query specific data
query = MapServicesQuery(services.iloc[0]['layer_url'])
data = query.load_data()
```

## Transformers

The Transformers module handles coordinate system conversions and reference system mappings.

### Core Classes

::: openspoor.transformers.TransformerGeocodeToCoordinates

### Usage Example

```python
from openspoor.transformers import TransformerGeocodeToCoordinates
import pandas as pd

# Prepare data
data = pd.DataFrame({
    'geocode': ['001', '002'],
    'km': [10.5, 15.2]
})

# Transform coordinates
transformer = TransformerGeocodeToCoordinates('geocode', 'km', 'EPSG:28992')
result = transformer.transform(data)
```

## Visualizations

The Visualizations module creates interactive maps using Folium.

### Core Classes

::: openspoor.visualisations.TrackMap

::: openspoor.visualisations.PlottingPoints

::: openspoor.visualisations.PlottingLineStrings

::: openspoor.visualisations.PlottingAreas

### Usage Example

```python
from openspoor.visualisations import TrackMap, PlottingPoints

# Create interactive map
track_map = TrackMap([
    PlottingPoints(stations, popup='NAAM', color='red')
])
track_map.show()
```

## Network

The Network module provides tools for railway network analysis and pathfinding.

!!! note "Module Documentation"
    Detailed API documentation for the Network module will be available in future releases.

### Key Features

- Shortest path calculation
- Network connectivity analysis
- Route optimization
- Accessibility analysis

## Spoortak Models

The Spoortak Models module works with Dutch railway track section definitions.

### Core Classes

::: openspoor.spoortakmodel.SpoortakModelsData

::: openspoor.spoortakmodel.SpoortakSubsection

::: openspoor.spoortakmodel.SpoortakModelInspector

::: openspoor.spoortakmodel.SpoortakModelMapper

### Usage Example

```python
from openspoor.spoortakmodel import SpoortakModelsData

# Load spoortak data
data = SpoortakModelsData()
spoortakken = data.load_spoortak_models()
```

## Utility Functions

### Helper Functions

::: openspoor.utils.common.read_config

::: openspoor.utils.common.get_package_root

### Configuration

OpenSpoor uses a YAML configuration file for settings:

```python
from openspoor.utils.common import read_config

config = read_config()
print(config)
```

## Error Handling

OpenSpoor defines several custom exception types for better error handling:

```python
from openspoor.mapservices import MapServicesError
from openspoor.transformers import TransformationError

try:
    # OpenSpoor operations
    pass
except MapServicesError as e:
    print(f"Map service error: {e}")
except TransformationError as e:
    print(f"Transformation error: {e}")
```

## Data Types

### Common Data Formats

OpenSpoor works with several data formats:

- **GeoDataFrame**: Primary format for geospatial data
- **DataFrame**: For tabular data without geometry
- **Shapely Geometries**: For geometric operations
- **GeoJSON**: For data exchange

### Coordinate Systems

Supported coordinate reference systems:

- **EPSG:28992**: RD New (Dutch national grid)
- **EPSG:4326**: WGS84 (GPS coordinates)
- **Custom CRS**: As supported by pyproj

## Performance Considerations

### Large Datasets

For optimal performance with large datasets:

```python
# Use spatial filtering
filtered_data = data.cx[xmin:xmax, ymin:ymax]

# Sample large datasets
sample_data = data.sample(n=1000)

# Use appropriate data types
data = data.astype({'column': 'category'})
```

### Memory Management

```python
# Process data in chunks
chunk_size = 1000
for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
    # Process chunk
    pass
```

## Configuration Options

OpenSpoor can be configured through environment variables or configuration files:

```yaml
# config.yaml
mapservices:
  base_url: "https://mapservices.prorail.nl"
  timeout: 30

visualization:
  default_colors: ["blue", "red", "green"]
  map_style: "default"

network:
  cache_enabled: true
  max_cache_size: 100
```

## Version Information

```python
import openspoor
print(f"OpenSpoor version: {openspoor.__version__}")
```

## Further Reading

- [User Guide](../user-guide/mapservices.md): Detailed usage examples
- [Examples](../examples/demo-notebook.md): Real-world use cases
- [Development](../development/contributing.md): Contributing guidelines