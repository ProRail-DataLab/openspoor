import os
import geopandas as gpd
import pandas as pd
from unittest import mock

from openspoor.transformers import TransformerCoordinatesToSpoor, TransformerGeocodeToCoordinates, TransformerSpoortakToCoordinates
from openspoor.mapservices import PUICMapservices, SpoortakMapservices, MapservicesData

from shapely.geometry import LineString, Point

class Test:
    spoortak_mock_output = gpd.GeoDataFrame(
        {
            "OBJECTID": [7632, 814, 3666],
            "LEVENSCYCLUS_STATUS": [None, None, None],
            "BEHEERDER": ["ProRail", "ProRail", "ProRail"],
            "GEOCODE": ["133", "666", "666"],
            "SUBCODE": ["a", "a", "b"],
            "GEOCODE_NR": [133, 666, 666],
            "GEOSUBCODE": ["133_a", "666_a", "666_b"],
            "GEOCODE_NAAM": [
                "Amsterdam Riekerpolder - Warmond",
                "Intersectie_Betuwe",
                "Intersectie_Betuwe2",
            ],
            "KMLINT": ["Asra-Wmd", "Ut-Btl", "x"],
            "KMLINT_OMSCHRIJVING": [
                "Amsterdam Riekerpolder Aansl. - Warmond",
                "Utrecht Centraal - Boxtel",
                "Betuweroute Giessendam - Betuweroute Echteld",
            ],
            "KM_GEOCODE_VAN": [13.565115, 27.2627, 30.611],
            "KM_GEOCODE_VAN_T": ["13,565115", "27,262663", "30,610967"],
            "KM_GEOCODE_TOT": [13.938248, 30.4137, 47.3894],
            "KM_GEOCODE_TOT_T": ["13,938248", "30,413654", "47,389363"],
            "ONDERHOUDSREGIO_NAAM": ["Randstad Noord", "x", "x"],
            "ONDERHOUDSREGIO_AFKORTING": ["RN", "x", "x"],
            "TECHNIEKVELD": ["BAAN", "BAAN", "BAAN"],
            "OPC_GEBIED_NAAM": ["Haarlem", "x", "x"],
            "OPC_GEBIED_NR": [8, 42, 42],
            "PGO_GEBIED_NR": [240, 42, 42],
            "PGO_GEBIED_NAAM": ["Kennemerland", "x", "x"],
            "PCA": ["Strukton Rail", "x", "x"],
            "X_BEGIN": [112734.527, 146991.272, 130926.326],
            "Y_BEGIN": [480849.498, 431256.059, 428074.85],
            "Z_BEGIN": [-10.096, 3.681, 0.805],
            "X_EIND": [112526.442, 146020.757, 147257.832],
            "Y_EIND": [480540.36, 428314.414, 430108.601],
            "Z_EIND": [-10.096, 5.529, 4.7],
            "LENGTE": [372.658005, 3148.7552, 16777.9781],
            "NAAM_LANG": ["133_1045BV_13.6", "666_405L_27.2", "152_4121L_30.5"],
            "PUIC": [
                "b21ee052-709e-419c-8bab-f6526c4d155b",
                "6336d8e5-b897-4ce0-b179-9ffd50de5d8e",
                "1362141d-51ad-437a-a8ed-926721a522f4",
            ],
            "REF_FYS_SPOORTAK_PUIC": ["670f5613-a851-4d5a-bd11-dc430b46c545", "x", "x"],
            "REF_FYS_SPOORTAK_NAAM": ["1045BV", "405L", "4121L"],
            "POSITIONELE_NAUWKEURIGHEID_MM": [None, None, None],
            "PUBLICATIEDATUM": [None, None, None],
            "GELDIG_VANAF": [None, None, None],
            "PRORAIL_GEBIED": ["Noord-West", "Zuid-West", "Zee-Zevenaar"],
        },
        geometry=[
            LineString(
                [
                    (112734.52699999884, 480849.4979999997),
                    (112679.4849999994, 480767.1550000012),
                    (112622.47399999946, 480681.72399999946),
                    (112574.38300000131, 480609.63599999994),
                    (112556.42000000179, 480583.22199999914),
                    (112541.87000000104, 480562.2470000014),
                    (112526.44200000167, 480540.3599999994),
                ]
            ),
            LineString(
                [
                    (146991.27199999988, 431256.05900000036),
                    (146983.57200000063, 431239.006000001),
                    (146974.40900000185, 431219.0219999999),
                    (146233.02100000158, 429589.6649999991),
                    (146226.03400000185, 429574.84800000116),
                    (146219.30700000003, 429560.2509999983),
                    (146212.9849999994, 429546.29100000113),
                    (146206.54800000042, 429532.35599999875),
                    (146198.88800000027, 429515.3260000013),
                    (146012.93200000003, 428385.9149999991),
                    (146020.75699999928, 428314.4140000008),
                ]
            ),
            LineString(
                [
                    (146368.15069999918, 430096.1020000018),
                    (146368.15100000054, 430096.1020000018),
                    (146418.10200000182, 430099.43200000003),
                    (146454.68389999866, 430101.62640000135),
                    (146460.3333999999, 430101.9653000012),
                    (146460.33370000124, 430101.9653000012),
                    (146468.01300000027, 430102.42599999905),
                    (146476.92550000176, 430102.9008000009),
                    (146476.92639999837, 430102.90089999884),
                    (146476.92689999938, 430102.90089999884),
                    (146481.45710000023, 430103.1422000006),
                    (146517.94200000167, 430105.0859999992),
                    (146547.90700000152, 430106.5229999982),
                    (146577.87799999863, 430107.83900000155),
                    (146627.84099999815, 430109.7670000009),
                    (146677.81599999964, 430111.36199999973),
                    (146707.8049999997, 430112.15900000185),
                    (146737.7969999984, 430112.8359999992),
                    (146787.7899999991, 430113.6979999989),
                    (146807.3200000003, 430113.95800000057),
                    (146837.78700000048, 430114.2259999998),
                    (146887.78599999845, 430114.4210000001),
                    (146917.56799999997, 430114.38899999857),
                    (146954.33300000057, 430114.1770000011),
                    (146985.48299999908, 430113.8579999991),
                    (147030.68100000173, 430113.1460000016),
                    (147257.83199999854, 430108.6009999998),
                ]
            ),
        ],
        crs="epsg:28992",
    )

    puic_mock_output = gpd.GeoDataFrame(
        {
            "SPOOR_ID": [
                "133_1045BV_13.6",
                "916Aa",
                "916Aa",
                "916Aa",
                "916Aa",
                "666_405L_27.2",
                "152_4121L_30.5",
            ],
            "SPOOR_PUIC": [
                "670f5613-a851-4d5a-bd11-dc430b46c545",
                "b26b158e-7f8d-44b6-8fe9-902b3cbd07f6",
                "b26b158e-7f8d-44b6-8fe9-902b3cbd07f6",
                "b26b158e-7f8d-44b6-8fe9-902b3cbd07f6",
                "b26b158e-7f8d-44b6-8fe9-902b3cbd07f6",
                "6336d8e5-b897-4ce0-b179-9ffd50de5d8e",
                "1362141d-51ad-437a-a8ed-926721a522f4",
            ],
            "GEOCODE_NR": [133, 664, 664, 664, 664, 666, 666],
            "GEOSUBCODE": [
                "133_a",
                "664_b",
                "664_b",
                "664_b",
                "664_b",
                "666_a",
                "666_b",
            ],
            "KM_GEOCODE_TOT": [
                13.938248,
                43.096931,
                43.115844,
                43.096931,
                43.120308,
                30.413654,
                47.389363,
            ],
            "KM_GEOCODE_VAN": [
                13.565115,
                43.076084,
                43.096931,
                43.076202,
                43.096931,
                27.262663,
                46.499943,
            ],
            "Type": [
                "Spoortak",
                "Kruisingbeen",
                "Kruisingbeen",
                "Kruisingbeen",
                "Kruisingbeen",
                "Spoortak",
                "Spoortak",
            ],
            "PRORAIL_GEBIED": [
                "Noord-West",
                "Zuid-Holland Zuid",
                "Zuid-Holland Zuid",
                "Zuid-Holland Zuid",
                "Zuid-Holland Zuid",
                "Zuid-West",
                "Zee-Zevenaar",
            ],
            "X_BEGIN": [
                112734.527,
                95659.391,
                95648.723,
                95657.027,
                95648.723,
                146991.272,
                146368.150692,
            ],
            "Y_BEGIN": [
                480849.498,
                433499.239,
                433520.105,
                433498.19,
                433520.105,
                431256.059,
                430096.101978,
            ],
        },
        geometry=[
            LineString(
                [
                    (112734.52699999884, 480849.4979999997),
                    (112679.4849999994, 480767.1550000012),
                    (112622.47399999946, 480681.72399999946),
                    (112574.38300000131, 480609.63599999994),
                    (112556.42000000179, 480583.22199999914),
                    (112541.87000000104, 480562.2470000014),
                    (112526.44200000167, 480540.3599999994),
                ]
            ),
            LineString(
                [
                    (95659.3909999989, 433499.2390000001),
                    (95648.72300000116, 433520.1050000004),
                ]
            ),
            LineString(
                [
                    (95648.72300000116, 433520.1050000004),
                    (95642.02400000021, 433537.8249999993),
                ]
            ),
            LineString(
                [
                    (95657.02699999884, 433498.1900000013),
                    (95648.72300000116, 433520.1050000004),
                ]
            ),
            LineString(
                [
                    (95648.72300000116, 433520.1050000004),
                    (95638.0540000014, 433540.9699999988),
                ]
            ),
            LineString(
                [
                    (146991.27199999988, 431256.05900000036),
                    (146983.57200000063, 431239.006000001),
                    (146974.40900000185, 431219.0219999999),
                    (146233.02100000158, 429589.6649999991),
                    (146226.03400000185, 429574.84800000116),
                    (146219.30700000003, 429560.2509999983),
                    (146212.9849999994, 429546.29100000113),
                    (146206.54800000042, 429532.35599999875),
                    (146198.88800000027, 429515.3260000013),
                    (146012.93200000003, 428385.9149999991),
                    (146020.75699999928, 428314.4140000008),
                ]
            ),
            LineString(
                [
                    (146368.15069999918, 430096.1020000018),
                    (146368.15100000054, 430096.1020000018),
                    (146418.10200000182, 430099.43200000003),
                    (146454.68389999866, 430101.62640000135),
                    (146460.3333999999, 430101.9653000012),
                    (146460.33370000124, 430101.9653000012),
                    (146468.01300000027, 430102.42599999905),
                    (146476.92550000176, 430102.9008000009),
                    (146476.92639999837, 430102.90089999884),
                    (146476.92689999938, 430102.90089999884),
                    (146481.45710000023, 430103.1422000006),
                    (146517.94200000167, 430105.0859999992),
                    (146547.90700000152, 430106.5229999982),
                    (146577.87799999863, 430107.83900000155),
                    (146627.84099999815, 430109.7670000009),
                    (146677.81599999964, 430111.36199999973),
                    (146707.8049999997, 430112.15900000185),
                    (146737.7969999984, 430112.8359999992),
                    (146787.7899999991, 430113.6979999989),
                    (146807.3200000003, 430113.95800000057),
                    (146837.78700000048, 430114.2259999998),
                    (146887.78599999845, 430114.4210000001),
                    (146917.56799999997, 430114.38899999857),
                    (146954.33300000057, 430114.1770000011),
                    (146985.48299999908, 430113.8579999991),
                    (147030.68100000173, 430113.1460000016),
                    (147257.83199999854, 430108.6009999998),
                ]
            ),
        ],
        crs="epsg:28992",
    )

    @mock.patch("openspoor.mapservices.SpoortakMapservices._download_data")
    def test_caching_spoortakmapservices(self, mocked_load, tmp_path):
        mocked_load.return_value = self.spoortak_mock_output
        cache_path = tmp_path / "spoortak.p"

        assert ~os.path.exists(cache_path)
        spoortak_mapservices = SpoortakMapservices(cache_location=cache_path)

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

    @mock.patch("openspoor.mapservices.PUICMapservices._download_data")
    def test_caching_puicmapservices(self, mocked_load, tmp_path):
        mocked_load.return_value = self.puic_mock_output
        cache_path = tmp_path / "puic.p"

        assert ~os.path.exists(cache_path)
        puic_mapservices = PUICMapservices(cache_location=cache_path)
        puic_mapservices.load_data()
        assert os.path.exists(cache_path)

        # Load a second time to actually use cached file
        output = puic_mapservices.load_data()

        expected_output = self.puic_mock_output

        pd.testing.assert_frame_equal(
            pd.DataFrame(output.drop(columns="geometry")),
            pd.DataFrame(expected_output.drop(columns="geometry")),
        )
        assert all(output.geometry.geom_almost_equals(expected_output.geometry, 6))

    def test_acceptance_TransformerCoordinatesToSpoor(self):
        xy_test_df = pd.DataFrame(
            {
                "x": [
                    112734.526,
                    112734.526,
                    112732.526,
                    112679.485,
                    95659.390,
                    0,
                    95648.723,
                ],
                "y": [
                    480849.498,
                    480849.498,
                    480846.498,
                    480767.155,
                    433499.239,
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
        coordinates_transformer = TransformerCoordinatesToSpoor()
        coordinates_transformer = coordinates_transformer.fit(
            self.puic_mock_output, self.spoortak_mock_output
        )
        output_gdf = coordinates_transformer.transform(xy_test_gdf)
        output_df = pd.DataFrame(
            output_gdf[
                [
                    "x",
                    "y",
                    "SPOOR_ID",
                    "SPOOR_PUIC",
                    "GEOCODE_NR",
                    "GEOSUBCODE",
                    "Type",
                    "PRORAIL_GEBIED",
                    "geocode_kilometrering",
                    "lokale_kilometrering",
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
                    95659.390,
                    0,
                    95648.723,
                ],
                "y": [
                    480849.498,
                    480849.498,
                    480846.498,
                    480767.155,
                    433499.239,
                    0,
                    433520.105,
                ],
                "SPOOR_ID": [
                    "133_1045BV_13.6",
                    "133_1045BV_13.6",
                    "133_1045BV_13.6",
                    "133_1045BV_13.6",
                    "916Aa",
                    None,
                    "916Aa",
                ],
                "SPOOR_PUIC": [
                    "670f5613-a851-4d5a-bd11-dc430b46c545",
                    "670f5613-a851-4d5a-bd11-dc430b46c545",
                    "670f5613-a851-4d5a-bd11-dc430b46c545",
                    "670f5613-a851-4d5a-bd11-dc430b46c545",
                    "b26b158e-7f8d-44b6-8fe9-902b3cbd07f6",
                    None,
                    "b26b158e-7f8d-44b6-8fe9-902b3cbd07f6",
                ],
                "GEOCODE_NR": [133, 133, 133, 133, 664, None, 664],
                "GEOSUBCODE": [
                    "133_a",
                    "133_a",
                    "133_a",
                    "133_a",
                    "664_b",
                    None,
                    "664_b",
                ],
                "Type": [
                    "Spoortak",
                    "Spoortak",
                    "Spoortak",
                    "Spoortak",
                    "Kruisingbeen",
                    None,
                    "Kruisingbeen",
                ],
                "PRORAIL_GEBIED": [
                    "Noord-West",
                    "Noord-West",
                    "Noord-West",
                    "Noord-West",
                    "Zuid-Holland Zuid",
                    None,
                    "Zuid-Holland Zuid",
                ],
                "geocode_kilometrering": [
                    13.565,
                    13.565,
                    13.569,
                    13.665,
                    43.076,
                    None,
                    43.097,
                ],
                "lokale_kilometrering": [
                    5.557240109132988e-07,
                    5.557240109132988e-07,
                    0.003606104262724306,
                    0.09904540076557604,
                    None,
                    None,
                    None,
                ],
            }
        )

        pd.testing.assert_frame_equal(output_df, expected_output_df)

        # Check the same for GPS coordinate input
        gps_test_df = pd.DataFrame(
            {
                "x": [
                    4.7673844619138706,
                    4.7673844619138706,
                    4.767355509869135,
                    4.766587672621954,
                    4.525246659701094,
                    3.3135577051498633,
                    4.5250881382855095,
                ],
                "y": [
                    52.313976549824126,
                    52.313976549824126,
                    52.31394943442051,
                    52.31323228145257,
                    51.88685477188099,
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
                    "SPOOR_ID",
                    "SPOOR_PUIC",
                    "GEOCODE_NR",
                    "GEOSUBCODE",
                    "Type",
                    "PRORAIL_GEBIED",
                    "geocode_kilometrering",
                    "lokale_kilometrering",
                ]
            ]
        )

        expected_output_df["x"] = gps_test_gdf["x"]
        expected_output_df["y"] = gps_test_gdf["y"]
        pd.testing.assert_frame_equal(
            output_df, expected_output_df, check_less_precise=3
        )

    def test_acceptance_TransformerCoordinatesToSpoor_intersecting_tracks(self):
        x_coord = 146465.975
        y_coord = 430102.306
        points_df = pd.DataFrame(
            {
                "x": [x_coord],
                "y": [y_coord],
            }
        )
        points_gdf = gpd.GeoDataFrame(
            points_df,
            geometry=gpd.points_from_xy(points_df["x"], points_df["y"]),
            crs="epsg:28992",
        )

        coordinates_transformer = TransformerCoordinatesToSpoor()
        coordinates_transformer = coordinates_transformer.fit(
            self.puic_mock_output, self.spoortak_mock_output
        )
        output_gdf = coordinates_transformer.transform(points_gdf)
        output_df = pd.DataFrame(
            output_gdf[
                [
                    "x",
                    "y",
                    "SPOOR_ID",
                    "SPOOR_PUIC",
                    "GEOCODE_NR",
                    "GEOSUBCODE",
                    "Type",
                    "PRORAIL_GEBIED",
                    "geocode_kilometrering",
                    "lokale_kilometrering",
                ]
            ]
        )
        expected_output = pd.DataFrame(
            {
                "x": [x_coord, x_coord],
                "y": [y_coord, y_coord],
                "SPOOR_ID": ["666_405L_27.2", "152_4121L_30.5"],
                "SPOOR_PUIC": [
                    "6336d8e5-b897-4ce0-b179-9ffd50de5d8e",
                    "1362141d-51ad-437a-a8ed-926721a522f4",
                ],
                "GEOCODE_NR": [666, 666],
                "GEOSUBCODE": ["666_a", "666_b"],
                "Type": ["Spoortak", "Spoortak"],
                "PRORAIL_GEBIED": ["Zuid-West", "Zee-Zevenaar"],
                "geocode_kilometrering": [28.533, 46.598],
                "lokale_kilometrering": [1.267710, 0.098021],
            }
        )
        pd.testing.assert_frame_equal(output_df, expected_output, check_less_precise=3)

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
        data = MapservicesData()
        input_base_url = "http://mapservices.prorail.nl/arcgis/rest/services/Kadastraal_004/MapServer/5"
        query_dict = {'KADSLEUTEL': ['ANM00G3774','ANM00G3775', 'ANM00H483'], 'KADGEM': ['ANM00']}

        output = data._load_all_features_to_gdf(input_base_url, dict_query=query_dict)

        assert (
                (output['KADSLEUTEL'][0] in ['ANM00G3774','ANM00G3775', 'ANM00H483']) \
               & (output['GEMEENTE'][0]=='Arnemuiden')
        )
