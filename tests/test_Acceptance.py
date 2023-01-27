import os
import geopandas as gpd
import pandas as pd
from unittest import mock

import pytest
from shapely.geometry import LineString

from openspoor.transformers import TransformerCoordinatesToSpoor, TransformerGeocodeToCoordinates, \
    TransformerSpoortakToCoordinates
from openspoor.mapservices import PUICMapservices, MapServicesQuery
from openspoor.utils.common import read_config

config = read_config()

mock_spoordata_gdf = gpd.GeoDataFrame({
    'OBJECTID': ["3030", "4738", "6792", "8578", "9149", "10073", "10701"],
    'GUID': ["7be2c50d-7139-fb4e-f46a-9900f32e12f7", "cb4da2ca-2209-962f-06de-40df9c2f1367",
             "0b3bc0b5-4b93-45a9-9130-12a9907f5940", "ee48e124-70e6-89d2-9a4d-38c24339f4bd",
             "330c2647-a053-fd04-0e68-a7634cf52a6a", "8713869e-d33f-0db0-ece9-18510ed8530a",
             "4be16269-1d0f-d544-27f4-228fbf64eecf"],
    'NAAM_LANG': ["664_903V_43.0", "107_133AV_12.0", "133_1045BV_13.6", "540_393AL_101.9", "107_133AV_12.0",
                  "540_393AL_101.9", "540_393AL_101.9"],
    'REF_FYSIEKE_SPOORTAK_PUIC': ["45a78c62-a4d4-4491-8760-2aca4cc0304d", "7fbc4e02-027c-4830-83d8-e315d19ec74e",
                                  "670f5613-a851-4d5a-bd11-dc430b46c545", "93c6d213-dd23-47eb-a0f4-80a4a6b2fd06",
                                  "7fbc4e02-027c-4830-83d8-e315d19ec74e", "93c6d213-dd23-47eb-a0f4-80a4a6b2fd06",
                                  "93c6d213-dd23-47eb-a0f4-80a4a6b2fd06"],
    'REF_FYSIEKE_SPOORTAK_NAAM': ["903V", "133AV", "1045BV", "393AL", "133AV", "393AL", "393AL"],
    'LENGTE': ["29.784084", "9733.893558", "372.658005", "32306.020472", "370.517858", "86.638492", "764.243859"],
    'X_BEGIN': ["95672.873", "94460.172", "112734.527", "90621.94519891", "103437.91488193", "90604.62401433",
                "90451.424"],
    'Y_BEGIN': ["433472.681", "451056.625", "480849.498", "439205.86644986", "447295.18032591", "439120.97708446",
                "438372.246"],
    'Z_BEGIN': ["0.039", "-2.897", "-10.096", "-2.33774869", "-3.08572145", "-0.28949644", "4.156"],
    'X_EIND': ["95659.391", "103437.91488193", "112526.442", "101785.771", "103779.704", "90621.94519891",
               "90604.62401433"],
    'Y_EIND': ["433499.239", "447295.18032591", "480540.36", "467698.101", "447152.129", "439205.86644986",
               "439120.97708446"],
    'Z_EIND': ["0.054", "-3.08572145", "-10.096", "-0.31", "-3.032", "-2.33774869", "-0.28949644"],
    'GEOCODE': ["664", "107", "133", "166", "107", "114", "114"],
    'SUBCODE': ["b", "None", "a", "None", "None", "b", "b"],
    'GEOCODE_NR': [664, 107, 133, 166, 107, 114, 114],
    'GEOSUBCODE': ["664_b", "107__", "133_a", "166__", "107__", "114_b", "114_b"],
    'GEOCODE_NAAM': ["Rotterdam Lombardijen", "Moordrecht Aansl. - Den Haag Binckhorst",
                     "Amsterdam Riekerpolder - Warmond", "Rotterdam Westelijke Splitsing - Nieuw Vennep",
                     "Moordrecht Aansl. - Den Haag Binckhorst",
                     "Rotterdam Kleiweg - Rotterdam Westelijke Splitsing",
                     "Rotterdam Kleiweg - Rotterdam Westelijke Splitsing"],
    'KMLINT': ["Bd-Rtd", "Gd-Gvc", "Asra-Wmd", "Rtd-Hfd", "Gd-Gvc", "Rtd-Hfd", "Rtd-Hfd"],
    'KMLINT_OMSCHRIJVING': ["Breda - Rotterdam Centraal ", "Gouda - Den Haag Centraal ",
                            "Amsterdam Riekerpolder Aansl. - Warmond ", "Rotterdam Centraal - Hoofddorp ",
                            "Gouda - Den Haag Centraal ", "Rotterdam Centraal - Hoofddorp ",
                            "Rotterdam Centraal - Hoofddorp "],
    'KM_GEOCODE_VAN': [43.049589, 11.980743, 13.565115, 102.9, 2.265149, 102.801006, 101.957663],
    'KM_GEOCODE_VAN_T': ["43,049589", "11,980743", "13,565115", "102,900000", "2,265149", "102,801006",
                         "101,957663"],
    'KM_GEOCODE_TOT': [43.076084, 2.265149, 13.938248, 135.206033, 1.894618, 102.9, 102.801006],
    'KM_GEOCODE_TOT_T': ["43,076084", "2,265149", "13,938248", "135,206033", "1,894618", "102,900000",
                         "102,801006"],
    'BEHEERDER': ["ProRail", "ProRail", "ProRail", "ProRail", "ProRail", "ProRail", "ProRail"],
    'ONDERHOUDSREGIO_NAAM': ["Randstad Zuid", "Randstad Zuid", "Randstad Noord", "None", "Randstad Zuid", "None",
                             "Randstad Zuid"],
    'ONDERHOUDSREGIO_AFKORTING': ["RZ", "RZ", "RN", "None", "RZ", "None", "RZ"],
    'TECHNIEKVELD': ["Baan", "Baan", "Baan", "Baan", "Baan", "Baan", "Baan"],
    'PGO_GEBIED_NAAM': ["Dordrecht", "Den Haag", "Kennemerland", "None", "Rijn en Gouwe", "None", "Rotterdam"],
    'PGO_GEBIED_NR': [140.0, 110.0, 240.0, None, 100.0, None, 120.0],
    'OPC_GEBIED_NAAM': ["Dordrecht", "Den Haag", "Haarlem", "HSL", "Rijn en Gouwe", "HSL", "Rotterdam"],
    'OPC_GEBIED_NR': [5.0, 2.0, 8.0, 70.0, 81.0, 70.0, 3.0],
    'PCA': ["ASSET Rail", "VolkerRail", "Strukton Rail", "Infraspeed", "BAM Rail", "Infraspeed", "VolkerRail"],
    'PRORAIL_GEBIED': ["Zuid-Holland Zuid", "Zuid-Holland Noord", "Noord-West", "Zuid-Holland Zuid",
                       "Zuid-Holland Noord", "Zuid-Holland Zuid", "Zuid-Holland Zuid"]},
    # This list of geometries is heavily trimmed
    geometry=[LineString([(95672.8720, 433472.6810, 43.0496),
                          (95659.391, 433499.2390, 43.07610)]),
              LineString([(94460.172, 451056.625, 11.98070),
                          (103437.91490, 447295.18030, 2.26510)]),
              LineString([(112734.527, 480849.498, 13.56510),
                          (112679.485, 480767.1550, 13.6647),
                          (112526.4420, 480540.36, 13.93820)]),
              LineString([(90621.9452, 439205.8664, 102.9),
                          (96064.1310, 450373.485, 115.50430),
                          (96076.9, 450390.1058, 115.52520),
                          (101785.7710, 467698.101, 135.2060)]),
              LineString([(103437.91490, 447295.18030, 2.26510),
                          (103596.4690, 447228.819, 2.0928),
                          (103779.704, 447152.1290, 1.8946)]),
              LineString([(90604.6240, 439120.9771, 102.8010),
                          (90606.367, 439129.4860, 102.8109),
                          (90621.9310, 439205.797, 102.9),
                          (90621.9452, 439205.8664, 102.9)]),
              LineString([(90451.424, 438372.246, 101.9577),
                          (90604.6240, 439120.9771, 102.8010)])],
    crs="EPSG:28992")


@pytest.fixture
@mock.patch("openspoor.transformers.TransformerCoordinatesToSpoor._get_spoortak_met_geokm")
def coordinates_transformer(mocked_load):
    mocked_load.return_value = mock_spoordata_gdf
    return TransformerCoordinatesToSpoor()


class Test:
    spoortak_mock_output = mock_spoordata_gdf

    puic_mock_output = gpd.GeoDataFrame(
        {
            "SPOOR_ID": ["133_1045BV_13.6", "916Aa", "916Aa", "916Aa", "916Aa", "666_405L_27.2", "152_4121L_30.5", ],
            "SPOOR_PUIC": ["670f5613-a851-4d5a-bd11-dc430b46c545", "b26b158e-7f8d-44b6-8fe9-902b3cbd07f6",
                           "b26b158e-7f8d-44b6-8fe9-902b3cbd07f6", "b26b158e-7f8d-44b6-8fe9-902b3cbd07f6",
                           "b26b158e-7f8d-44b6-8fe9-902b3cbd07f6", "6336d8e5-b897-4ce0-b179-9ffd50de5d8e",
                           "1362141d-51ad-437a-a8ed-926721a522f4", ],
            "GEOCODE_NR": [133, 664, 664, 664, 664, 666, 666],
            "GEOSUBCODE": ["133_a", "664_b", "664_b", "664_b", "664_b", "666_a", "666_b", ],
            "KM_GEOCODE_TOT": [13.938248, 43.096931, 43.115844, 43.096931, 43.120308, 30.413654, 47.389363, ],
            "KM_GEOCODE_VAN": [13.565115, 43.076084, 43.096931, 43.076202, 43.096931, 27.262663, 46.499943, ],
            "Type": ["Spoortak", "Kruisingbeen", "Kruisingbeen", "Kruisingbeen", "Kruisingbeen", "Spoortak",
                     "Spoortak", ],
            "PRORAIL_GEBIED": ["Noord-West", "Zuid-Holland Zuid", "Zuid-Holland Zuid", "Zuid-Holland Zuid",
                               "Zuid-Holland Zuid", "Zuid-West", "Zee-Zevenaar", ],
            "X_BEGIN": [112734.527, 95659.391, 95648.723, 95657.027, 95648.723, 146991.272, 146368.150692, ],
            "Y_BEGIN": [480849.498, 433499.239, 433520.105, 433498.19, 433520.105, 431256.059, 430096.101978, ],
        },
        geometry=[
            LineString([(112734.52699999884, 480849.4979999997), (112679.4849999994, 480767.1550000012),
                        (112622.47399999946, 480681.72399999946), (112574.38300000131, 480609.63599999994),
                        (112556.42000000179, 480583.22199999914), (112541.87000000104, 480562.2470000014),
                        (112526.44200000167, 480540.3599999994), ]),
            LineString([(95659.3909999989, 433499.2390000001), (95648.72300000116, 433520.1050000004), ]),
            LineString([(95648.72300000116, 433520.1050000004), (95642.02400000021, 433537.8249999993), ]),
            LineString([(95657.02699999884, 433498.1900000013), (95648.72300000116, 433520.1050000004), ]),
            LineString([(95648.72300000116, 433520.1050000004), (95638.0540000014, 433540.9699999988), ]),
            LineString([(146991.27199999988, 431256.05900000036), (146983.57200000063, 431239.006000001),
                        (146974.40900000185, 431219.0219999999), (146233.02100000158, 429589.6649999991),
                        (146226.03400000185, 429574.84800000116), (146219.30700000003, 429560.2509999983),
                        (146212.9849999994, 429546.29100000113), (146206.54800000042, 429532.35599999875),
                        (146198.88800000027, 429515.3260000013), (146012.93200000003, 428385.9149999991),
                        (146020.75699999928, 428314.4140000008), ]),
            LineString([(146368.15069999918, 430096.1020000018), (146368.15100000054, 430096.1020000018),
                        (146418.10200000182, 430099.43200000003), (146454.68389999866, 430101.62640000135),
                        (146460.3333999999, 430101.9653000012), (146460.33370000124, 430101.9653000012),
                        (146468.01300000027, 430102.42599999905), (146476.92550000176, 430102.9008000009),
                        (146476.92639999837, 430102.90089999884), (146476.92689999938, 430102.90089999884),
                        (146481.45710000023, 430103.1422000006), (146517.94200000167, 430105.0859999992),
                        (146547.90700000152, 430106.5229999982), (146577.87799999863, 430107.83900000155),
                        (146627.84099999815, 430109.7670000009), (146677.81599999964, 430111.36199999973),
                        (146707.8049999997, 430112.15900000185), (146737.7969999984, 430112.8359999992),
                        (146787.7899999991, 430113.6979999989), (146807.3200000003, 430113.95800000057),
                        (146837.78700000048, 430114.2259999998), (146887.78599999845, 430114.4210000001),
                        (146917.56799999997, 430114.38899999857), (146954.33300000057, 430114.1770000011),
                        (146985.48299999908, 430113.8579999991), (147030.68100000173, 430113.1460000016),
                        (147257.83199999854, 430108.6009999998), ]), ],
        crs="epsg:28992",
    )

    @mock.patch("openspoor.mapservices.MapServicesQuery._load_all_features_to_gdf")
    def test_caching_singlequery(self, mocked_load, tmp_path):
        mocked_load.return_value = self.spoortak_mock_output
        cache_path = tmp_path / "spoortak.p"

        assert ~os.path.exists(cache_path)
        spoortak_mapservices = MapServicesQuery(url=config['spoor_url'], cache_location=cache_path)

        spoortak_mapservices.load_data()
        assert os.path.exists(cache_path)

        # Load a second time to actually use cached file
        output = spoortak_mapservices.load_data()

        expected_output = self.spoortak_mock_output

        pd.testing.assert_frame_equal(
            pd.DataFrame(output.drop(columns="geometry")),
            pd.DataFrame(expected_output.drop(columns="geometry")),
        )
        assert all(output.geometry.geom_almost_equals(expected_output.geometry, 6))

    @mock.patch("openspoor.mapservices.MapServicesQuery._load_all_features_to_gdf")
    def test_caching_puicmapservices(self, mocked_load, tmp_path):
        mocked_load.return_value = self.puic_mock_output
        cache_path = tmp_path / "puic.p"

        assert ~os.path.exists(cache_path)
        puic_mapservices = PUICMapservices(spoor_cache_location=cache_path,
                                           wisselkruisingbeen_cache_location=cache_path)
        puic_mapservices.spoor_query.load_data()
        assert os.path.exists(cache_path)

        # Load a second time to actually use cached file
        output = puic_mapservices.spoor_query.load_data()

        expected_output = self.puic_mock_output

        pd.testing.assert_frame_equal(
            pd.DataFrame(output.drop(columns="geometry")),
            pd.DataFrame(expected_output.drop(columns="geometry")),
        )
        assert all(output.geometry.geom_almost_equals(expected_output.geometry, 6))

    def test_acceptance_TransformerCoordinatesToSpoor(self, coordinates_transformer):
        xy_test_df = pd.DataFrame(
            {
                "x": [
                    112734.526,
                    112734.526,
                    112732.526,
                    112679.485,
                    95659.5,
                    0,
                    95648.723,
                ],
                "y": [
                    480849.498,
                    480849.498,
                    480846.498,
                    480767.155,
                    433499.0,
                    0,
                    433520.105,
                ],
            }
        )
        xy_test_gdf = gpd.GeoDataFrame(
            xy_test_df,
            geometry=gpd.points_from_xy(xy_test_df["x"], xy_test_df["y"]),
            crs="epsg:28992",
        )
        output_gdf = coordinates_transformer.transform(xy_test_gdf)
        output_df = pd.DataFrame(
            output_gdf[
                [
                    "x",
                    "y",
                    "NAAM_LANG",
                    "REF_FYSIEKE_SPOORTAK_PUIC",
                    "GEOCODE_NR",
                    "GEOSUBCODE",
                    "PRORAIL_GEBIED",
                    "geocode_kilometrering",
                ]
            ]
        )
        expected_output_df = pd.DataFrame(
            {
                "x": [
                    112734.526,
                    112734.526,
                    112732.526,
                    112679.485,
                    95659.5,
                    0,
                    95648.723,
                ],
                "y": [
                    480849.498,
                    480849.498,
                    480846.498,
                    480767.155,
                    433499.0,
                    0,
                    433520.105,
                ],
                "NAAM_LANG": [
                    "133_1045BV_13.6",
                    "133_1045BV_13.6",
                    "133_1045BV_13.6",
                    "133_1045BV_13.6",
                    "664_903V_43.0",
                    None,
                    None
                ],
                "REF_FYSIEKE_SPOORTAK_PUIC": [
                    "670f5613-a851-4d5a-bd11-dc430b46c545",
                    "670f5613-a851-4d5a-bd11-dc430b46c545",
                    "670f5613-a851-4d5a-bd11-dc430b46c545",
                    "670f5613-a851-4d5a-bd11-dc430b46c545",
                    "45a78c62-a4d4-4491-8760-2aca4cc0304d",
                    None,
                    None
                ],
                "GEOCODE_NR": [133, 133, 133, 133, 664, None, None],
                "GEOSUBCODE": [
                    "133_a",
                    "133_a",
                    "133_a",
                    "133_a",
                    "664_b",
                    None,
                    None
                ],
                "PRORAIL_GEBIED": [
                    "Noord-West",
                    "Noord-West",
                    "Noord-West",
                    "Noord-West",
                    "Zuid-Holland Zuid",
                    None,
                    None
                ],
                "geocode_kilometrering": [
                    13.5651,
                    13.5651,
                    13.5687,
                    13.6647,
                    43.07566511830464,
                    None,
                    None
                ]
            }
        )

        pd.testing.assert_frame_equal(output_df, expected_output_df)

        # Check the same for GPS coordinate input
        gps_test_df = pd.DataFrame(
            {
                "x": [
                    4.767384394447763,
                    4.767384394447763,
                    4.767355509869135,
                    4.766587672621954,
                    4.525359,
                    3.3135577051498633,
                    4.5250881382855095,
                ],
                "y": [
                    52.31397654888525,
                    52.31397654888525,
                    52.31394943442051,
                    52.31323228145257,
                    51.886729,
                    47.974765849805166,
                    51.887041167508,
                ],
            }
        )
        gps_test_gdf = gpd.GeoDataFrame(
            gps_test_df,
            geometry=gpd.points_from_xy(gps_test_df["x"], gps_test_df["y"]),
            crs="epsg:4326",
        )
        output_gdf = coordinates_transformer.transform(gps_test_gdf)
        output_df = pd.DataFrame(
            output_gdf[
                [
                    "x",
                    "y",
                    "NAAM_LANG",
                    "REF_FYSIEKE_SPOORTAK_PUIC",
                    "GEOCODE_NR",
                    "GEOSUBCODE",
                    "PRORAIL_GEBIED",
                    "geocode_kilometrering",
                ]
            ]
        )

        expected_output_df["x"] = gps_test_gdf["x"]
        expected_output_df["y"] = gps_test_gdf["y"]
        pd.testing.assert_frame_equal(
            output_df, expected_output_df, check_less_precise=3
        )

    def test_acceptance_TransformerCoordinatesToSpoor_intersecting_tracks(self, coordinates_transformer):
        x_coord, y_coord = 96070, 450383
        points_df = pd.DataFrame({"x": [x_coord], "y": [y_coord]})
        points_gdf = gpd.GeoDataFrame(
            points_df,
            geometry=gpd.points_from_xy(points_df["x"], points_df["y"]),
            crs="epsg:28992",
        )
        output_gdf = coordinates_transformer.transform(points_gdf)
        output_df = pd.DataFrame(
            output_gdf[
                [
                    "x",
                    "y",
                    "NAAM_LANG",
                    "REF_FYSIEKE_SPOORTAK_PUIC",
                    "GEOCODE_NR",
                    "GEOSUBCODE",
                    "PRORAIL_GEBIED",
                    "geocode_kilometrering",
                ]
            ]
        )
        expected_output = pd.DataFrame(index=[0, 0],
                                       data={
                                           "x": [x_coord, x_coord],
                                           "y": [y_coord, y_coord],
                                           "NAAM_LANG": ["107_133AV_12.0", "540_393AL_101.9"],
                                           "REF_FYSIEKE_SPOORTAK_PUIC": [
                                               "7fbc4e02-027c-4830-83d8-e315d19ec74e",
                                               "93c6d213-dd23-47eb-a0f4-80a4a6b2fd06",
                                           ],
                                           "GEOCODE_NR": [107, 166],
                                           "GEOSUBCODE": ["107__", "166__"],
                                           "PRORAIL_GEBIED": ["Zuid-Holland Noord", "Zuid-Holland Zuid"],
                                           "geocode_kilometrering": [10.239600, 115.515389],
                                       }
                                       )

        pd.testing.assert_frame_equal(output_df.sort_values(['NAAM_LANG']),
                                      expected_output.sort_values(['NAAM_LANG']), check_less_precise=3)

    def test_acceptance_TransformerGeocodeToCoordinates(self):
        geocode_transformer = TransformerGeocodeToCoordinates(
            geocode_column="Geocode",
            geocode_km_column="geocode_km",
            coordinate_system="Rijksdriehoek",
        )
        df_locaties = pd.DataFrame(
            data={
                "Geocode": ["112", "112", "112", "009", "009", "009"],
                "geocode_km": [77, 76, 77, 115.208, 115.183, 115.208],
                "some_data": ["a", "b", "c", "d", "e", "f"],
            },
            index=pd.Series([66, 11, 55, 44, 33, 22], name="Indexname"),
        )

        output = geocode_transformer.transform(df_locaties)

        output_expected = pd.DataFrame(
            {
                "Geocode": ["112", "112", "112", "009", "009", "009"],
                "geocode_km": [77, 76, 77, 115.208, 115.183, 115.208],
                "some_data": ["a", "b", "c", "d", "e", "f"],
                "x": [
                    86494.936,
                    86193.091,
                    86494.936,
                    203621.562,
                    203642.514,
                    203621.562,
                ],
                "y": [
                    439781.070,
                    440735.689,
                    439781.070,
                    534204.614,
                    534190.950,
                    534204.614,
                ],
            },
            index=pd.Series([66, 11, 55, 44, 33, 22], name="Indexname"),
        )

        pd.testing.assert_frame_equal(output, output_expected, check_less_precise=2)

    def test_acceptance_TransformerSpoortakToCoordinates(self):
        spoortak_transformer = TransformerSpoortakToCoordinates(
            "SPOOR_ID", "lokale_kilometrering", coordinate_system="Rijksdriehoek"
        )
        spoortak_transformer = spoortak_transformer.fit(self.spoortak_mock_output)
        input_df = pd.DataFrame(
            {
                "SPOOR_ID": ["133_1045BV_13.6", "133_1045BV_13.6"],
                "lokale_kilometrering": [0.002280929575529405, 0.10132577461919272],
            }
        )

        output = spoortak_transformer.transform(input_df)

        expected_output = pd.DataFrame(
            {
                "SPOOR_ID": ["133_1045BV_13.6", "133_1045BV_13.6"],
                "lokale_kilometrering": [0.002280929575529405, 0.10132577461919272],
                "x": [112733.25943053346, 112678.21920015597],
                "y": [480849.498, 480767.155],
            }
        )
        pd.testing.assert_frame_equal(output, expected_output)

    def test_acceptance_query_functionality(self):
        data = MapServicesQuery(url="http://mapservices.prorail.nl/arcgis/rest/services/Kadastraal_004/MapServer/5")
        query_dict = {'KADSLEUTEL': ['ANM00G3774', 'ANM00G3775', 'ANM00H483'], 'KADGEM': ['ANM00']}

        output = data._load_all_features_to_gdf(dict_query=query_dict)

        assert (
                (output['KADSLEUTEL'][0] in ['ANM00G3774', 'ANM00G3775', 'ANM00H483'])
                & (output['GEMEENTE'][0] == 'Arnemuiden')
        )
