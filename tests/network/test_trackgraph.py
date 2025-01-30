import pytest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
from openspoor.network.trackgraph import TrackNetherlands, KruisingResolver

@pytest.fixture
def sample_functionele_spoortak():
    data = {
        'PUIC': [1, 2],
        'geometry': [LineString([(0, 0), (1, 1)]), LineString([(1, 1), (2, 2)])],
        'REF_BEGRENZER_TYPE_BEGIN': ['KRUISING', 'WISSEL_GW'],
        'REF_BEGRENZER_TYPE_EIND': ['WISSEL_GW', 'KRUISING'],
        'KANTCODE_SPOORTAK_BEGIN': ['L', 'V'],
        'KANTCODE_SPOORTAK_EIND': ['R', 'L'],
    }
    return gpd.GeoDataFrame(data, crs="EPSG:4326")

def test_expected_connections(sample_functionele_spoortak):
    track_nl = TrackNetherlands()
    row = sample_functionele_spoortak.iloc[0]
    assert track_nl.expected_connections(row) == 2
    row2 = sample_functionele_spoortak.iloc[1]
    assert track_nl.expected_connections(row2) == 3

def test_project_point(sample_functionele_spoortak):
    track_nl = TrackNetherlands()
    track_nl.functionele_spoortak = sample_functionele_spoortak
    point = Point(0.5, 0.5)
    assert track_nl._project_point(point) == 1

def test_dijkstra(sample_functionele_spoortak):
    track_nl = TrackNetherlands()
    track_nl.functionele_spoortak = sample_functionele_spoortak
    track_nl.illegal_pairs_list = []
    track_nl.graphentries = {1: [(2, 1.414)], 2: []}
    start = Point(0, 0)
    end = Point(2, 2)
    route = track_nl.dijkstra(start, end)
    assert (route.data.index.values == [1, 2]).all()

def test_kruising_resolver():
    data = {
        'PUIC_left': [1, 1, 2],
        'PUIC_right': [2, 3, 3],
        'REF_BEGRENZER_TYPE_BEGIN_left': ['KRUISING', 'KRUISING', 'WISSEL_EW'],
        'REF_BEGRENZER_TYPE_EIND_left': ['WISSEL_EW', 'WISSEL_EW', 'KRUISING'],
        'intersection_area': [0.1, 0.3, 0.2],
        'expected_connections_left': [1, 1, 2],
        'found_connections': [1, 1, 2]
    }
    df = pd.DataFrame(data)
    resolver = KruisingResolver(df)
    best_matches = resolver.take_best_at_kruising()
    assert len(best_matches) == 2
    assert best_matches.loc[best_matches.PUIC_left == 1, 'PUIC_right'].values[0] == 2
