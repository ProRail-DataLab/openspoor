import os
import pytest
from openspoor.visualisations.trackmap import TrackMap, PlottingDataFrame


@pytest.fixture(scope='session')
def emptytrackmap():
    return TrackMap()


@pytest.fixture(scope='session')
def example_plottingdataframe():
    return PlottingDataFrame({'lat': [52.45, 52.5], 'lon': [5.15, 5.2], 'name': ['ABC', 'DEF']})


@pytest.fixture()
def prefilled_trackmap(example_plottingdataframe):
    return TrackMap(objects=[example_plottingdataframe])


def test_TrackMap(emptytrackmap, prefilled_trackmap, example_plottingdataframe):
    objects_in_empty = len(emptytrackmap.__dict__['_children'])
    objects_in_nonempty = len(prefilled_trackmap.__dict__['_children'])
    assert objects_in_empty == 1, 'Should contain only the aerial photo'
    assert objects_in_nonempty == 1 + len(example_plottingdataframe), 'Should contain the aerial photo and some markers'


def test_fix_zoom(prefilled_trackmap):
    children_before = prefilled_trackmap.__dict__['_children'].copy()
    prefilled_trackmap._fix_zoom()
    children_after = prefilled_trackmap.__dict__['_children'].copy()
    for child in children_before:
        try:
            if children_before[child]['_name'] == 'FitBounds':
                assert False
        except TypeError:
            pass

    fitbounds_found = False
    for child in children_after:
        try:
            if children_after[child].__dict__['_name'] == 'FitBounds':
                fitbounds_found = True
        except TypeError:
            pass
    assert fitbounds_found


def test_makesmaller(prefilled_trackmap):
    assert type(prefilled_trackmap.show(makesmaller=False)) is not type(prefilled_trackmap.show(makesmaller=True))


def test_save_trackmap(prefilled_trackmap, tmpdir):
    prefilled_trackmap.save(os.path.join(tmpdir, 'output.html'))
    assert os.listdir(tmpdir) == ['output.html']

