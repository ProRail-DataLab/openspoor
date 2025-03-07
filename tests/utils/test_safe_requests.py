import pytest

from openspoor.utils import safe_requests


@pytest.fixture
def invalid_url():
    return "nonexistant://prorail.nl"


@pytest.fixture
def count_url():
    base_url = (
        "http://mapservices.prorail.nl/"
        "arcgis/rest/services/Kadastraal_004/MapServer/5/query"
    )
    params = (
        "?where=(KADSLEUTEL='ANM00G3774') and (KADGEM='ANM00')"
        "&f=json&returnGeometry=true&spatialRel=esriSpatialRelIntersects"
        "&geometry="
        "{"
        '"xmin":0,"ymin":0,"xmax":500000,"ymax":800000,'
        '"spatialReference":{"wkid":28992}'
        "}"
        "&geometryType=esriGeometryEnvelope&inSR=28992"
        "&outFields=*&outSR=28992&returnCountOnly=True"
    )
    return base_url + params


@pytest.fixture
def input_json():
    return {
        "features": [
            {
                "geometry": {
                    "coordinates": [112734.526, 480849.498],
                    "type": "Point",
                },
                "properties": {"FID": "0"},
                "type": "Feature",
            }
        ],
        "name": "RD_Coordinaten",
        "type": "FeatureCollection",
    }


@pytest.fixture
def geocode_to_xy_url():
    return (
        "https://mapservices.prorail.nl/"
        + "geocoderen/api_v2.ashx/GEO_PuntXY_naar_GEOCODE_en_KM_RD"
    )


@pytest.fixture
def base_safe_requests():
    return safe_requests.SafeRequest(max_retry=3, time_between=0.5)


def test_get_string_failure(invalid_url):
    with pytest.raises(Exception):  # This is a bit generic
        # as the exception raised varies on where you run this
        safe_requests.SafeRequest(max_retry=2, time_between=0.01).get_string(
            "GET", invalid_url
        )


def test_get_string_success(base_safe_requests, count_url):
    assert isinstance(base_safe_requests.get_string("GET", count_url), str)


def test_get_json_success(base_safe_requests, count_url):
    assert isinstance(base_safe_requests.get_json("GET", count_url), dict)


def test_post_json_success(base_safe_requests, geocode_to_xy_url, input_json):
    assert isinstance(
        base_safe_requests.get_json("POST", geocode_to_xy_url, input_json),
        dict,
    )
