import pytest
import pandas as pd
import geopandas as gpd
from openspoor.mapservices import FeatureServerOverview


@pytest.fixture(scope="session")
def featureserveroverview():
    return FeatureServerOverview()


def test_get_feature_wi_geometry(featureserveroverview):
    station = featureserveroverview.search_for(
        "Station", exact=True
    ).load_data()
    assert isinstance(station, gpd.GeoDataFrame)


def test_get_features_wo_geometry(featureserveroverview):
    relaties = featureserveroverview.search_for(
        "Relatie perronwand spoortak", exact=True
    ).load_data()
    assert isinstance(relaties, pd.DataFrame)
