# Testing

This guide covers testing practices and procedures for the OpenSpoor project.

## Test Framework

OpenSpoor uses pytest as the primary testing framework with additional plugins for enhanced functionality:

- **pytest**: Core testing framework
- **pytest-cov**: Coverage reporting
- **pytest-xdist**: Parallel test execution
- **nbmake**: Jupyter notebook testing

## Running Tests

### Basic Test Execution

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=openspoor

# Run tests in parallel
uv run pytest -n auto

# Run specific test file
uv run pytest tests/test_mapservices/test_find_mapservice.py

# Run specific test function
uv run pytest tests/test_mapservices/test_find_mapservice.py::test_feature_server_overview
```

### Including Notebook Tests

```bash
# Run tests including Jupyter notebooks
uv run pytest --nbmake --nbmake-kernel=python3

# Run only notebook tests
uv run pytest --nbmake demo_notebook/
```

### Coverage Reports

```bash
# Generate HTML coverage report
uv run pytest --cov=openspoor --cov-report=html

# Generate XML coverage report (for CI)
uv run pytest --cov=openspoor --cov-report=xml

# Coverage with minimum threshold
uv run pytest --cov=openspoor --cov-fail-under=50
```

## Test Structure

### Directory Organization

```
tests/
├── test_mapservices/
│   ├── test_find_mapservice.py
│   └── test_query.py
├── test_transformers/
│   ├── test_coordinate_transformer.py
│   └── test_geocode_transformer.py
├── test_visualisations/
│   ├── test_trackmap.py
│   └── test_plotting.py
├── test_network/
│   └── test_shortest_path.py
├── test_spoortakmodel/
│   ├── test_spoortak_data.py
│   └── test_inspector.py
├── conftest.py          # Shared fixtures
└── test_utils.py        # Test utilities
```

### Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*` (optional)
- Test functions: `test_*`
- Test fixtures: Descriptive names

## Test Categories

### Unit Tests

Test individual functions and methods in isolation:

```python
import pytest
import pandas as pd
from openspoor.transformers import TransformerGeocodeToCoordinates

def test_transformer_initialization():
    """Test transformer initialization with valid parameters."""
    transformer = TransformerGeocodeToCoordinates(
        geocode_column='geocode',
        geocode_km_column='km',
        coordinate_system='EPSG:28992'
    )
    
    assert transformer.geocode == 'geocode'
    assert transformer.geocode_km == 'km'
    assert transformer.coordinate_system == 'EPSG:28992'

def test_transformer_invalid_coordinate_system():
    """Test transformer raises error for invalid coordinate system."""
    with pytest.raises(ValueError):
        TransformerGeocodeToCoordinates(
            geocode_column='geocode',
            geocode_km_column='km',
            coordinate_system='INVALID:12345'
        )
```

### Integration Tests

Test interactions between components:

```python
def test_mapservices_to_visualization_integration():
    """Test complete workflow from data query to visualization."""
    # Query data
    query = MapServicesQuery(test_url)
    data = query.load_data()
    
    # Create visualization
    track_map = TrackMap([
        PlottingPoints(data, popup='test_column')
    ])
    
    # Verify map creation
    assert isinstance(track_map, TrackMap)
    assert len(track_map._layers) == 1
```

### Parameterized Tests

Test multiple scenarios with different parameters:

```python
@pytest.mark.parametrize("coordinate_system,expected_range", [
    ('EPSG:28992', (0, 300000)),      # RD New X range
    ('EPSG:4326', (-180, 180)),       # WGS84 longitude range
])
def test_coordinate_transformation_ranges(coordinate_system, expected_range):
    """Test coordinate transformation produces values in expected ranges."""
    transformer = TransformerGeocodeToCoordinates(
        'geocode', 'km', coordinate_system
    )
    
    test_data = pd.DataFrame({
        'geocode': ['001'],
        'km': [10.0]
    })
    
    result = transformer.transform(test_data)
    
    assert expected_range[0] <= result['x'].iloc[0] <= expected_range[1]
```

## Test Fixtures

### Common Fixtures

```python
# conftest.py
import pytest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString

@pytest.fixture
def sample_geocode_data():
    """Sample geocode data for testing."""
    return pd.DataFrame({
        'geocode': ['001', '002', '003'],
        'km': [10.0, 15.5, 8.2],
        'description': ['Station A', 'Bridge B', 'Signal C']
    })

@pytest.fixture
def sample_track_data():
    """Sample track geometry data."""
    return gpd.GeoDataFrame({
        'GEOCODE': ['001', '002'],
        'NAAM': ['Track 1', 'Track 2'],
        'geometry': [
            LineString([(4.0, 52.0), (4.1, 52.1)]),
            LineString([(4.1, 52.1), (4.2, 52.2)])
        ]
    }, crs='EPSG:4326')

@pytest.fixture
def mock_mapservices_response():
    """Mock response for MapServices API."""
    return {
        'features': [
            {
                'attributes': {'OBJECTID': 1, 'NAAM': 'Test Station'},
                'geometry': {'x': 125000, 'y': 485000}
            }
        ]
    }
```

### Temporary File Fixtures

```python
@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary directory for test outputs."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return output_dir

def test_map_save_functionality(sample_track_data, temp_output_dir):
    """Test saving map to file."""
    track_map = TrackMap([
        PlottingLineStrings(sample_track_data)
    ])
    
    output_file = temp_output_dir / "test_map.html"
    track_map.save(output_file)
    
    assert output_file.exists()
    assert output_file.stat().st_size > 0
```

## Mocking External Dependencies

### Mock Network Requests

```python
import responses
from openspoor.mapservices import MapServicesQuery

@responses.activate
def test_mapservices_query_with_mock():
    """Test MapServices query with mocked HTTP response."""
    # Mock the API response
    responses.add(
        responses.GET,
        'https://mapservices.prorail.nl/test',
        json={'features': []},
        status=200
    )
    
    query = MapServicesQuery('https://mapservices.prorail.nl/test')
    result = query.load_data()
    
    assert len(result) == 0
```

### Mock File System Operations

```python
from unittest.mock import patch, mock_open

@patch('builtins.open', new_callable=mock_open, read_data='test config')
def test_config_reading(mock_file):
    """Test configuration file reading."""
    from openspoor.utils.common import read_config
    
    config = read_config()
    
    mock_file.assert_called_once()
    # Additional assertions based on expected config structure
```

## Performance Testing

### Benchmarking

```python
import time
import pytest

def test_coordinate_transformation_performance():
    """Test coordinate transformation performance with large dataset."""
    # Create large test dataset
    large_data = pd.DataFrame({
        'geocode': ['001'] * 10000,
        'km': range(10000)
    })
    
    transformer = TransformerGeocodeToCoordinates('geocode', 'km', 'EPSG:28992')
    
    start_time = time.time()
    result = transformer.transform(large_data)
    end_time = time.time()
    
    # Performance assertion
    assert end_time - start_time < 60  # Should complete within 60 seconds
    assert len(result) == 10000
```

### Memory Testing

```python
import psutil
import os

def test_memory_usage_large_dataset():
    """Test memory usage doesn't exceed reasonable limits."""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Perform memory-intensive operation
    large_data = create_large_test_dataset()
    result = process_large_dataset(large_data)
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Memory should not increase by more than 500MB
    assert memory_increase < 500 * 1024 * 1024
```

## Error Testing

### Exception Testing

```python
def test_invalid_geocode_handling():
    """Test handling of invalid geocode values."""
    invalid_data = pd.DataFrame({
        'geocode': ['999', None, 'invalid'],
        'km': [10.0, 15.0, 20.0]
    })
    
    transformer = TransformerGeocodeToCoordinates('geocode', 'km', 'EPSG:28992')
    
    with pytest.raises(ValueError, match="Invalid geocode"):
        transformer.transform(invalid_data)

def test_network_timeout_handling():
    """Test handling of network timeouts."""
    with patch('requests.get', side_effect=requests.Timeout):
        query = MapServicesQuery('https://test.url')
        
        with pytest.raises(TimeoutError):
            query.load_data()
```

## Notebook Testing

### Testing Jupyter Notebooks

```bash
# Test all notebooks
uv run pytest --nbmake demo_notebook/

# Test specific notebook
uv run pytest --nbmake demo_notebook/openspoor_example.ipynb

# Test notebooks with specific kernel
uv run pytest --nbmake --nbmake-kernel=python3 demo_notebook/
```

### Notebook Test Configuration

```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
nbmake_cell_timeout = 300  # 5 minutes per cell
nbmake_kernel = "python3"
```

## Continuous Integration

### GitHub Actions Configuration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install uv
        uv sync
    
    - name: Run tests
      run: |
        uv run pytest --cov=openspoor --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Test Data Management

### Test Data Guidelines

- Use minimal datasets that still test functionality
- Avoid large files in the repository
- Use fixtures to generate test data programmatically
- Mock external API responses

### Example Test Data Creation

```python
def create_test_railway_network():
    """Create minimal test railway network."""
    tracks = gpd.GeoDataFrame({
        'GEOCODE': ['001', '002', '003'],
        'MAXSNELHEID': [120, 160, 80],
        'geometry': [
            LineString([(4.0, 52.0), (4.1, 52.1)]),
            LineString([(4.1, 52.1), (4.2, 52.2)]),
            LineString([(4.2, 52.2), (4.3, 52.3)])
        ]
    }, crs='EPSG:4326')
    
    return tracks
```

## Debugging Tests

### Running Tests in Debug Mode

```bash
# Run with verbose output
uv run pytest -v

# Drop into debugger on failure
uv run pytest --pdb

# Run specific test with debugging
uv run pytest tests/test_file.py::test_function --pdb
```

### Test Debugging in IDE

Configure your IDE to run pytest with debugging support:

```python
# Add this to enable debugging in tests
import pdb; pdb.set_trace()
```

## Quality Metrics

### Coverage Targets

- Overall coverage: >90%
- New code coverage: 100%
- Critical paths: 100%

### Test Quality Indicators

- Test execution time < 5 minutes for full suite
- No flaky tests (tests that fail intermittently)
- Clear, descriptive test names
- Proper error message validation

## Troubleshooting Common Issues

### Import Errors

```python
# Ensure proper PYTHONPATH setup
import sys
sys.path.insert(0, '/path/to/openspoor')
```

### Async Test Issues

```python
import asyncio
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test asynchronous functionality."""
    result = await async_function()
    assert result is not None
```

### Cleanup After Tests

```python
def test_with_cleanup():
    """Test with proper cleanup."""
    try:
        # Test operations
        pass
    finally:
        # Cleanup operations
        cleanup_resources()
```

This testing guide ensures comprehensive test coverage and reliable quality assurance for the OpenSpoor project.