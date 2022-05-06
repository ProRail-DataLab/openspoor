from openspoor.mapservices import FeatureServerOverview
import pytest


@pytest.fixture(scope='session')
def all_featureserver_layers():
    return FeatureServerOverview()


def test_get_all_featureserver_layers(all_featureserver_layers):
    out = all_featureserver_layers.df
    assert out.shape[0] > 0, 'No featureservices found'
    assert out.shape[1] == 2, 'Unexpected number of columns'


def test_get_layers_in_featureservers(all_featureserver_layers):
    url = 'https://mapservices.prorail.nl/arcgis/rest/services/Bodemkwaliteit_001/FeatureServer'
    out = all_featureserver_layers._get_layers_in_featureservers(url)
    assert out.shape[0] > 0, 'No featureservices found'
    assert out.shape[1] == 2, 'Unexpected number of columns'


def test_search_for(all_featureserver_layers):
    out_hek = all_featureserver_layers.search_for('hek')
    out_spoor = all_featureserver_layers.search_for('spoor')
    assert out_spoor.shape[0] > out_hek.shape[0], 'Spoor does not occur more often than hek'
    assert out_hek.shape[1] == 2, 'Invalid number of columns'
    assert out_spoor.shape[1] == 2, 'Invalid number of columns'
