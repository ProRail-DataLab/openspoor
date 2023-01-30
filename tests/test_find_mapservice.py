import pytest
from unittest import mock
import pandas as pd
import geopandas as gpd
from glob import glob

from shapely.geometry import Point
from pathlib import Path

from openspoor.mapservices import FeatureServerOverview, FeatureSearchResults


@pytest.fixture(scope='session')
def all_featureserver_layers():
    featureserver = FeatureServerOverview()
    featureserver.df = featureserver.get_all_featureserver_layers()
    return featureserver


def test_get_all_featureserver_layers(all_featureserver_layers):
    out = all_featureserver_layers.df
    assert out.shape[0] > 0, 'No featureservices found'
    assert out.shape[1] == 4, 'Unexpected number of columns'


def test_get_layers_in_featureservers(all_featureserver_layers):
    url = 'https://mapservices.prorail.nl/arcgis/rest/services/Afscherming_002/FeatureServer'
    out = all_featureserver_layers._get_layers_in_featureservers(url)
    assert out.shape[0] > 0, 'No featureservices found'
    assert out.shape[1] == 2, 'Unexpected number of columns'


def test_exact_match(all_featureserver_layers):
    # This should find many hits, as 'spo' is part of 'spoor'
    general_search_hits = all_featureserver_layers.search_for('spo').shape[0]
    exact_search_hits = all_featureserver_layers.search_for('spo', exact=True).shape[0]

    exact_search_hits_haag = all_featureserver_layers.search_for('haag', exact=True).shape[0]  # Hedges

    assert general_search_hits > 0, 'Did not find hits for a very general search'
    assert exact_search_hits == 0, 'Found hits for exact search where none where expected'
    assert exact_search_hits_haag == 1, 'Found no hit for haag when one was expected'



def test_search_for(all_featureserver_layers):
    out_hek = all_featureserver_layers.search_for('hek')
    out_spoor = all_featureserver_layers.search_for('spoor')
    assert out_spoor.shape[0] > out_hek.shape[0], 'Spoor does not occur more often than hek'
    assert out_hek.shape[1] == 4, 'Invalid number of columns'
    assert out_spoor.shape[1] == 4, 'Invalid number of columns'


@pytest.fixture()
def search_results():
    return pd.DataFrame({'layer_url': ['a', 'b', 'c'],
                         'description': ['d', 'e', 'f']})


class TestFeatureSearchResults:
    spoortak_mock_output = gpd.GeoDataFrame({'example_col': [1, 2, 3],
                                             },
                                            geometry=[Point(112734.52699999884, 480849.4979999997),
                                                      Point(112679.4849999994, 480767.1550000012),
                                                      Point(112622.47399999946, 480681.72399999946)],
                                            crs="epsg:28992")

    @mock.patch("openspoor.mapservices.MapServicesQuery._load_all_features_to_gdf")
    def test_FeatureSearchResults(self, mocked_load, search_results, tmpdir):
        out_gdf = FeatureSearchResults(search_results).load_data(0)
        gpd.testing.assert_geodataframe_equal(out_gdf, mocked_load), 'Incorrecting loading of data'

    @mock.patch("openspoor.mapservices.MapServicesQuery._load_all_features_to_gdf")
    def test_FeatureSearchResults(self, mocked_load, search_results, tmpdir):
        mocked_load.return_value = self.spoortak_mock_output

        output_dir = Path(tmpdir) / 'outputs'
        FeatureSearchResults(search_results).write_gpkg(output_dir, 0)

        files = glob(str(output_dir) + "/**")
        assert len(files) == 1, 'A file was written'
        assert gpd.read_file(files[0]).shape == (3, 2), 'Incorrect shape'

        FeatureSearchResults(search_results).write_gpkg(output_dir, 1)
        files = glob(str(output_dir) + "/**")
        assert len(files) == 2, 'A file was written'

        with pytest.raises(IndexError):
            FeatureSearchResults(search_results).write_gpkg(output_dir, 4)
