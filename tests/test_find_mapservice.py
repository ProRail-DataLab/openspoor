from openspoor import FeatureServerOverview
import pytest


@pytest.fixture(scope='session')
def all_featureserver_layers():
    return FeatureServerOverview()


# TODO: These tests can be a lot stricter
def test_get_all_featureserver_layers(all_featureserver_layers):
    out = all_featureserver_layers.df
    assert out.shape == (264, 2)


# TODO: These tests can be a lot stricter
def test_get_layers_in_featureservers(all_featureserver_layers):
    url = 'https://mapservices.prorail.nl/arcgis/rest/services/Bodemkwaliteit_001/FeatureServer'
    out = all_featureserver_layers._get_layers_in_featureservers(url)
    assert out.shape == (3, 2)


# TODO: These tests can be a lot stricter
def test_search_for(all_featureserver_layers):
    out = all_featureserver_layers.search_for('hek')
    assert out.shape == (3, 2)
