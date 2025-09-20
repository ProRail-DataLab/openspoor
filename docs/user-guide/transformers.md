# Transformers

The Transformers module provides tools for converting between different coordinate systems and reference systems used in the Dutch railway network.

## Overview

Railway infrastructure in the Netherlands uses various coordinate reference systems:

- **Geocode-Kilometer**: ProRail's internal referencing system using track codes and kilometer markers
- **RD New (EPSG:28992)**: The Dutch national coordinate system (Rijksdriehoek)
- **WGS84 (EPSG:4326)**: Global GPS coordinates

The Transformers module handles conversions between these systems.

## Key Classes

::: openspoor.transformers.TransformerGeocodeToCoordinates
    options:
      show_root_heading: true
      show_source: false

## Coordinate Systems

### Geocode-Kilometer System

The geocode-kilometer system is ProRail's internal way of referencing locations:
- **Geocode**: A 3-digit code identifying a track section
- **Kilometer**: Position along that track in kilometers

### Supported Output Systems

- **EPSG:28992**: RD New (Rijksdriehoek) - Dutch national grid
- **EPSG:4326**: WGS84 - Global GPS coordinates

## Basic Usage

### Simple Coordinate Transformation

```python
import pandas as pd
from openspoor.transformers import TransformerGeocodeToCoordinates

# Create sample data
data = pd.DataFrame({
    'track_code': ['001', '002', '003'],
    'km_position': [10.5, 15.2, 8.7],
    'description': ['Station A', 'Bridge B', 'Signal C']
})

# Create transformer for RD coordinates
transformer = TransformerGeocodeToCoordinates(
    geocode_column='track_code',
    geocode_km_column='km_position', 
    coordinate_system='EPSG:28992'
)

# Transform the data
result = transformer.transform(data)
print(result[['track_code', 'km_position', 'x', 'y']])
```

### GPS Coordinates

```python
# Transform to GPS coordinates
gps_transformer = TransformerGeocodeToCoordinates(
    geocode_column='track_code',
    geocode_km_column='km_position',
    coordinate_system='EPSG:4326'
)

gps_result = gps_transformer.transform(data)
print(gps_result[['track_code', 'km_position', 'x', 'y']])
```

## Advanced Usage

### Working with Real Data

```python
# Load data from a CSV file
import pandas as pd

data = pd.read_csv('railway_assets.csv')
# Ensure geocode column is properly formatted
data['geocode'] = data['geocode'].astype(str).str.zfill(3)

# Transform coordinates
transformer = TransformerGeocodeToCoordinates(
    geocode_column='geocode',
    geocode_km_column='kilometrering',
    coordinate_system='EPSG:28992'
)

data_with_coords = transformer.transform(data)
```

### Batch Processing

```python
# Process large datasets efficiently
chunk_size = 1000

for chunk in pd.read_csv('large_dataset.csv', chunksize=chunk_size):
    chunk_transformed = transformer.transform(chunk)
    # Process or save each chunk
    chunk_transformed.to_csv('output.csv', mode='a', header=False)
```

### Error Handling

```python
try:
    result = transformer.transform(data)
except Exception as e:
    print(f"Transformation failed: {e}")
    
    # Check for common issues
    if data['geocode'].isnull().any():
        print("Warning: Found null geocodes")
    
    if data['kilometrering'].isnull().any():
        print("Warning: Found null kilometer values")
```

## Data Validation

### Before Transformation

```python
# Validate input data
def validate_input_data(df, geocode_col, km_col):
    issues = []
    
    if df[geocode_col].isnull().any():
        issues.append("Found null geocodes")
    
    if df[km_col].isnull().any():
        issues.append("Found null kilometer values")
    
    if (df[km_col] < 0).any():
        issues.append("Found negative kilometer values")
    
    return issues

issues = validate_input_data(data, 'track_code', 'km_position')
if issues:
    print("Data validation issues:")
    for issue in issues:
        print(f"- {issue}")
```

### After Transformation

```python
# Validate transformation results
def validate_transformation_results(df):
    issues = []
    
    if df[['x', 'y']].isnull().any().any():
        issues.append("Found null coordinates after transformation")
    
    # Check for reasonable coordinate ranges (RD New)
    if 'x' in df.columns:
        if not df['x'].between(0, 300000).all():
            issues.append("X coordinates outside expected RD range")
        if not df['y'].between(300000, 650000).all():
            issues.append("Y coordinates outside expected RD range")
    
    return issues

result_issues = validate_transformation_results(result)
if result_issues:
    print("Transformation validation issues:")
    for issue in result_issues:
        print(f"- {issue}")
```

## Integration with Other Modules

### Create Visualizations

```python
from openspoor.visualisations import TrackMap, PlottingPoints
import geopandas as gpd
from shapely.geometry import Point

# Transform coordinates
result = transformer.transform(data)

# Create geometries
geometry = [Point(xy) for xy in zip(result.x, result.y)]
gdf = gpd.GeoDataFrame(result, geometry=geometry, crs='EPSG:28992')

# Create map
track_map = TrackMap([
    PlottingPoints(gdf, popup=['description'], color='red')
])
track_map.show()
```

### Export Results

```python
# Save to various formats
result.to_csv('transformed_coordinates.csv', index=False)

# Save as GeoDataFrame
gdf.to_file('railway_points.geojson', driver='GeoJSON')
gdf.to_file('railway_points.gpkg', driver='GPKG')
```

## Tips and Best Practices

!!! tip "Data Preparation"
    - Ensure geocode values are properly formatted (3-digit strings with leading zeros)
    - Validate kilometer values are reasonable (positive numbers)
    - Handle missing data before transformation

!!! warning "API Dependencies"
    - Transformations require access to ProRail's coordinate transformation API
    - Network connectivity is required
    - API rate limits may apply for large datasets

!!! note "Coordinate Systems"
    - RD New (EPSG:28992) is the standard for Dutch mapping
    - WGS84 (EPSG:4326) is needed for web mapping and GPS devices
    - Always specify the correct coordinate system for your use case