# Spoortak Models

The Spoortak Models module provides tools for working with railway track sections (spoortakken) and their associated data models in the Dutch railway system.

## Overview

In the Dutch railway system, "spoortakken" are standardized track sections that form the basis for infrastructure management and operational planning. The Spoortak Models module helps you:

- Work with spoortak definitions and boundaries
- Map between different reference systems
- Inspect and analyze spoortak data
- Handle subsections within spoortakken

## Key Classes

::: openspoor.spoortakmodel.SpoortakModelsData
    options:
      show_root_heading: true
      show_source: false

::: openspoor.spoortakmodel.SpoortakSubsection
    options:
      show_root_heading: true
      show_source: false

::: openspoor.spoortakmodel.SpoortakModelInspector
    options:
      show_root_heading: true
      show_source: false

::: openspoor.spoortakmodel.SpoortakModelMapper
    options:
      show_root_heading: true
      show_source: false

## Basic Usage

### Loading Spoortak Data

```python
from openspoor.spoortakmodel import SpoortakModelsData

# Load spoortak models data
spoortak_data = SpoortakModelsData()
spoortakken = spoortak_data.load_spoortak_models()

print(f"Loaded {len(spoortakken)} spoortak models")
print(spoortakken.columns.tolist())
```

### Inspecting Spoortak Models

```python
from openspoor.spoortakmodel import SpoortakModelInspector

# Create inspector
inspector = SpoortakModelInspector(spoortakken)

# Get overview of spoortak models
overview = inspector.get_overview()
print(f"Total spoortakken: {overview['total_count']}")
print(f"Average length: {overview['average_length']:.2f} km")
```

### Working with Subsections

```python
from openspoor.spoortakmodel import SpoortakSubsection

# Get subsections for a specific spoortak
spoortak_id = "001A"
subsection = SpoortakSubsection(spoortak_id)
subsections = subsection.get_subsections()

print(f"Spoortak {spoortak_id} has {len(subsections)} subsections")
```

## Advanced Usage

### Mapping Between Reference Systems

```python
from openspoor.spoortakmodel import SpoortakModelMapper

# Create mapper
mapper = SpoortakModelMapper(spoortakken)

# Map geocode-kilometer to spoortak reference
geocode_km_data = pd.DataFrame({
    'geocode': ['001', '002', '003'],
    'kilometrering': [10.5, 15.2, 8.7]
})

spoortak_mapping = mapper.map_to_spoortak(geocode_km_data)
print(spoortak_mapping[['geocode', 'kilometrering', 'spoortak_id', 'spoortak_km']])
```

### Historical Spoortak Data

```python
# Load historical spoortak models
historical_data = SpoortakModelsData(include_historical=True)
historical_spoortakken = historical_data.load_spoortak_models()

# Compare with current data
inspector = SpoortakModelInspector(historical_spoortakken)
changes = inspector.analyze_changes(spoortakken)
print(f"Found {len(changes['added'])} new spoortakken")
print(f"Found {len(changes['removed'])} removed spoortakken")
```

## Data Analysis

### Spoortak Statistics

```python
# Analyze spoortak characteristics
stats = inspector.get_detailed_statistics()

print("Spoortak Length Distribution:")
print(f"Min: {stats['length']['min']:.2f} km")
print(f"Max: {stats['length']['max']:.2f} km")
print(f"Mean: {stats['length']['mean']:.2f} km")
print(f"Median: {stats['length']['median']:.2f} km")
```

### Geographic Analysis

```python
# Analyze geographic distribution
geographic_stats = inspector.analyze_geographic_distribution()

print("Geographic Distribution:")
for region, count in geographic_stats.items():
    print(f"{region}: {count} spoortakken")
```

### Connectivity Analysis

```python
# Analyze spoortak connectivity
connectivity = inspector.analyze_connectivity()

print(f"Connected components: {connectivity['components']}")
print(f"Average connections per spoortak: {connectivity['avg_connections']:.2f}")
```

## Visualization

### Spoortak Maps

```python
from openspoor.visualisations import TrackMap, PlottingLineStrings

# Create map showing spoortakken
spoortak_map = TrackMap([
    PlottingLineStrings(
        spoortakken, 
        color='spoortak_id', 
        popup=['spoortak_id', 'length_km'],
        weight=3
    )
])
spoortak_map.show()
```

### Subsection Visualization

```python
# Visualize subsections within a spoortak
spoortak_subsections = subsection.get_subsections_with_geometry()

subsection_map = TrackMap([
    PlottingLineStrings(
        spoortak_subsections, 
        color='subsection_type', 
        popup=['subsection_id', 'type', 'length'],
        weight=2
    )
])
subsection_map.show()
```

## Data Export and Integration

### Export Spoortak Data

```python
# Export to various formats
spoortakken.to_file('spoortakken.geojson', driver='GeoJSON')
spoortakken.to_file('spoortakken.gpkg', driver='GPKG')
spoortakken.to_csv('spoortakken_attributes.csv')
```

### Integration with Other Modules

```python
from openspoor.transformers import TransformerGeocodeToCoordinates
from openspoor.mapservices import MapServicesQuery

# Combine with coordinate transformations
transformer = TransformerGeocodeToCoordinates('geocode', 'kilometrering', 'EPSG:28992')
spoortak_with_coords = transformer.transform(spoortak_mapping)

# Combine with additional mapservices data
signals_query = MapServicesQuery("signals_url")
signals = signals_query.load_data()

# Spatial join with spoortakken
signals_with_spoortak = gpd.sjoin(signals, spoortakken, how='left', op='intersects')
```

## Quality Control

### Data Validation

```python
# Validate spoortak data quality
validation_results = inspector.validate_data_quality()

print("Data Quality Report:")
print(f"Missing geometries: {validation_results['missing_geometries']}")
print(f"Invalid geometries: {validation_results['invalid_geometries']}")
print(f"Topology errors: {validation_results['topology_errors']}")
```

### Consistency Checks

```python
# Check for consistency between different reference systems
consistency_check = mapper.check_mapping_consistency()

if consistency_check['issues']:
    print("Mapping consistency issues found:")
    for issue in consistency_check['issues']:
        print(f"- {issue}")
```

## Performance Optimization

### Spatial Indexing

```python
# Enable spatial indexing for large datasets
inspector = SpoortakModelInspector(spoortakken, use_spatial_index=True)

# Faster spatial queries
nearby_spoortakken = inspector.find_nearby_spoortakken(
    point=(52.3676, 4.9041), 
    distance=1000  # meters
)
```

### Caching

```python
# Cache frequently used data
spoortak_data = SpoortakModelsData(enable_caching=True)
spoortakken = spoortak_data.load_spoortak_models()  # Loaded from source
spoortakken_cached = spoortak_data.load_spoortak_models()  # Loaded from cache
```

## Error Handling

```python
try:
    spoortakken = spoortak_data.load_spoortak_models()
except DataLoadError as e:
    print(f"Error loading spoortak data: {e}")
except ValidationError as e:
    print(f"Data validation error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Use Cases

### Infrastructure Planning

```python
# Find optimal locations for new infrastructure
optimal_locations = inspector.find_optimal_infrastructure_locations(
    infrastructure_type='signal',
    spacing_requirements=2000,  # meters
    constraints=['curve_radius', 'gradient']
)
```

### Asset Management

```python
# Map assets to spoortakken for management purposes
asset_spoortak_mapping = mapper.map_assets_to_spoortakken(assets_df)

# Analyze asset distribution
asset_distribution = inspector.analyze_asset_distribution(asset_spoortak_mapping)
```

### Maintenance Planning

```python
# Group maintenance activities by spoortak
maintenance_by_spoortak = mapper.group_by_spoortak(maintenance_activities)

# Optimize maintenance scheduling
schedule = inspector.optimize_maintenance_schedule(
    maintenance_by_spoortak,
    constraints=['possession_windows', 'resource_availability']
)
```

## Tips and Best Practices

!!! tip "Data Management"
    - Keep spoortak data updated regularly
    - Validate data quality before analysis
    - Use spatial indexing for large datasets

!!! warning "Reference Systems"
    - Be aware of different spoortak numbering systems over time
    - Validate mappings between geocode-km and spoortak references
    - Handle historical changes in spoortak definitions

!!! note "Performance"
    - Cache frequently used spoortak data
    - Use appropriate spatial operations for large datasets
    - Consider using simplified geometries for overview analysis