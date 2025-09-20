import geopandas as gpd
import pytest
from shapely.geometry import LineString

from openspoor.visualisations.route import Route


@pytest.fixture
def sample_functionele_spoortak():
    """Create sample track data for testing."""
    data = {
        "PUIC": ["001_12345_1", "002_12346_1", "003_12347_1"],
        "geometry": [
            LineString([(100000, 400000), (101000, 400000)]),  # 1000m horizontal line
            LineString([(101000, 400000), (101000, 401000)]),  # 1000m vertical line
            LineString([(101000, 401000), (102000, 401000)]),  # 1000m horizontal line
        ],
    }
    return gpd.GeoDataFrame(data, crs="EPSG:28992")


@pytest.fixture
def sample_route(sample_functionele_spoortak):
    """Create a sample Route object."""
    spoortakken = ["001_12345_1", "002_12346_1", "003_12347_1"]
    return Route(sample_functionele_spoortak, spoortakken)


def test_route_basic_properties(sample_route):
    """Test basic route properties."""
    assert sample_route.length == 3000.0  # 3 segments of 1000m each
    assert sample_route.distance == 3000.0  # Same as length
    assert sample_route.distance_km == 3.0
    assert sample_route.segment_count == 3


def test_route_travel_time(sample_route):
    """Test travel time estimation."""
    expected_time = (3.0 / 80.0) * 60.0  # 3km at 80km/h in minutes
    assert abs(sample_route.total_travel_time - expected_time) < 0.01


def test_route_segments(sample_route, sample_functionele_spoortak):
    """Test detailed route segments information."""
    segments = sample_route.route_segments
    
    assert len(segments) == 3
    
    # Check first segment
    first_segment = segments[0]
    assert first_segment['puic'] == "001_12345_1"
    assert first_segment['length_m'] == 1000.0
    assert first_segment['length_km'] == 1.0
    assert abs(first_segment['estimated_time_minutes'] - (1.0/80.0)*60.0) < 0.01
    
    # Check that all segments have required fields
    for segment in segments:
        assert 'puic' in segment
        assert 'length_m' in segment
        assert 'length_km' in segment
        assert 'estimated_time_minutes' in segment
        assert 'geometry' in segment


def test_route_summary(sample_route):
    """Test comprehensive route summary."""
    summary = sample_route.summary
    
    # Check all required fields are present
    required_fields = [
        'total_distance_m',
        'total_distance_km', 
        'estimated_travel_time_minutes',
        'estimated_travel_time_hours',
        'segment_count',
        'start_point',
        'end_point',
        'track_segments',
        'has_start_end_coordinates'
    ]
    
    for field in required_fields:
        assert field in summary
    
    # Check values
    assert summary['total_distance_m'] == 3000.0
    assert summary['total_distance_km'] == 3.0
    assert summary['segment_count'] == 3
    assert summary['track_segments'] == ["001_12345_1", "002_12346_1", "003_12347_1"]
    assert summary['has_start_end_coordinates'] == False  # No start/end set in fixture
    
    # Check time calculations
    expected_minutes = (3.0 / 80.0) * 60.0
    expected_hours = expected_minutes / 60.0
    assert abs(summary['estimated_travel_time_minutes'] - expected_minutes) < 0.01
    assert abs(summary['estimated_travel_time_hours'] - expected_hours) < 0.01


def test_route_with_start_end_points(sample_functionele_spoortak):
    """Test route with start and end points."""
    from shapely.geometry import Point
    
    spoortakken = ["001_12345_1", "002_12346_1"]
    start = Point(100000, 400000)
    end = Point(101000, 401000)
    
    route = Route(sample_functionele_spoortak, spoortakken, start=start, end=end)
    
    assert route.start == start
    assert route.end == end
    assert route.summary['has_start_end_coordinates'] == True
    assert route.summary['start_point'] == start
    assert route.summary['end_point'] == end


def test_route_backward_compatibility(sample_route):
    """Test that existing functionality still works."""
    # Test that set_color method still works
    colored_route = sample_route.set_color('red')
    assert colored_route == sample_route  # Should return self
    assert hasattr(sample_route, 'color')
    
    # Test that length property still works as before
    assert sample_route.length == 3000.0
    
    # Test that the route has data attribute
    assert hasattr(sample_route, 'data')
    assert len(sample_route.data) == 3


def test_empty_route():
    """Test route with no segments."""
    empty_gdf = gpd.GeoDataFrame({'PUIC': [], 'geometry': []}, crs="EPSG:28992")
    empty_route = Route(empty_gdf, [])
    
    assert empty_route.length == 0.0
    assert empty_route.distance == 0.0
    assert empty_route.distance_km == 0.0
    assert empty_route.segment_count == 0
    assert empty_route.total_travel_time == 0.0
    assert empty_route.route_segments == []