import heapq
from functools import cached_property
from pathlib import Path
from typing import cast

import geopandas as gpd
import pandas as pd
from loguru import logger
from shapely.geometry import Point

from openspoor.mapservices import FeatureServerOverview
from openspoor.visualisations import Route


class TrackNetherlands:
    """
    Class to handle the track topology of the Netherlands.
    This class is used to create a graph of the track topology
    and to find the shortest path between two points.
    """

    def __init__(self, overwrite: bool = False, local_cache=True):
        self.local_cache = local_cache
        self.cache_location = Path("output")
        self.functionele_spoortak_path = (
            self.cache_location / "functionele_spoortak.gpkg"
        )
        self.allconnections_path = self.cache_location / "tracknetherlands.csv"
        self.overwrite = overwrite

    @cached_property
    def functionele_spoortak(self) -> gpd.GeoDataFrame:
        """
        Returns the GeoDataFrame with the functionele spoortakken.

        Returns
        -------
        gpd.GeoDataFrame
            A GeoDataFrame containing the functionele spoortakken.
        """
        if self.functionele_spoortak_path.exists() or self.overwrite:
            functionele_spoortak = gpd.read_file(
                self.functionele_spoortak_path
            )
        else:
            functionele_spoortak = (
                FeatureServerOverview()
                .search_for("functionele spoortak")
                .load_data()
            )
            functionele_spoortak["expected_connections"] = (
                functionele_spoortak.apply(self.expected_connections, axis=1)
            )
            if self.local_cache:
                functionele_spoortak.to_file(
                    self.functionele_spoortak_path, driver="GPKG"
                )  # [relevant_columns]
                logger.info(
                    "Saved functionele spoortak to "
                    f"{self.functionele_spoortak_path}"
                )
        return functionele_spoortak

    def _process_functionele_spoortak(
        self,
    ) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """
        Process the functionele spoortakken to find the connections
        between different spoortakken.

        Returns
        -------
        tuple of (gpd.GeoDataFrame, gpd.GeoDataFrame)
            A tuple containing:
            - valid_connections : gpd.GeoDataFrame
                A GeoDataFrame with valid connections between spoortakken.
            - all_connections : gpd.GeoDataFrame
                A GeoDataFrame with all identified connections between
                spoortakken.
        """
        touching_spoortakken = self.functionele_spoortak.sjoin(
            cast(
                gpd.GeoDataFrame,
                (
                    self.functionele_spoortak.assign(
                        geometry_right=lambda d: d.geometry
                    )
                ),
            ),
            how="inner",
            predicate="touches",
        )

        small_overlaps = self.get_small_overlaps(
            touching_spoortakken
        )  # Filter on spoortakken that are roughly consecutive
        small_overlaps_cleaned = KruisingResolver(
            small_overlaps
        ).take_best_at_kruising()  # At kruisingen, take the best match
        return (
            self._recheck_connections(small_overlaps_cleaned),
            touching_spoortakken,
        )  # Recheck if the connections are correct after the filtering

    def get_small_overlaps(self, joined: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Filters the connections between different spoortakken to retain only
        those that are roughly consecutive. This is determined by checking
        the intersection area between the two spoortakken.

        Parameters
        ----------
        joined : gpd.GeoDataFrame
            The GeoDataFrame containing the connections between
            different spoortakken.

        Returns
        -------
        gpd.GeoDataFrame
            The GeoDataFrame with the filtered connections.
        """
        joined["geometry_capped_left"] = joined.geometry.apply(
            lambda x: x.buffer(1, cap_style="flat")
        )
        joined["geometry_capped_right"] = joined.geometry_right.apply(
            lambda x: x.buffer(1, cap_style="flat")
        )
        joined["intersection_area"] = joined.apply(
            lambda d: d.geometry_capped_left.intersection(
                d.geometry_capped_right
            ).area,
            axis=1,
        )
        return cast(
            gpd.GeoDataFrame,
            joined[lambda d: d.intersection_area < 0.2].drop(
                columns=["geometry_capped_left", "geometry_capped_right"]
            ),
        )

    def _recheck_connections(
        self, gdf_cleaned: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
        """
        Rechecks the connections between different spoortakken to verify
        if they match the expected number of connections.

        Parameters
        ----------
        gdf_cleaned : gpd.GeoDataFrame
            The GeoDataFrame containing the cleaned connections.

        Returns
        -------
        gpd.GeoDataFrame
            The GeoDataFrame with the rechecked connections.
        """
        gdf_cleaned_res = gdf_cleaned.assign(
            found_connections_2=lambda d: d.groupby(
                "PUIC_left"
            ).PUIC_right.transform("count")
        )
        gdf_cleaned_res.loc[
            lambda d: d.found_connections_2 != d.expected_connections_left
        ].sort_values("PUIC_left")
        gdf_cleaned_res["mismatch"] = gdf_cleaned_res.apply(
            lambda x: x["found_connections_2"]
            != x["expected_connections_left"],
            axis=1,
        )
        return cast(gpd.GeoDataFrame, gdf_cleaned_res)

    def _mark_connections(
        self,
        all_connections: gpd.GeoDataFrame,
        valid_connections: gpd.GeoDataFrame,
    ) -> gpd.GeoDataFrame:
        """
        Tags each connection as illegal, valid, or neither based on the
        expected and actual connections.

        Parameters
        ----------
        all_connections : gpd.GeoDataFrame
            The GeoDataFrame containing all connections.
        valid_connections : gpd.GeoDataFrame
            The GeoDataFrame containing the valid connections.

        Returns
        -------
        gpd.GeoDataFrame
            The GeoDataFrame with all connections marked as illegal, valid,
            or neither.
        """
        all_connections_res = all_connections.set_index(
            ["PUIC_left", "PUIC_right"]
        )
        all_connections_res["valid"] = all_connections_res.index.isin(
            valid_connections.set_index(["PUIC_left", "PUIC_right"]).index
        )
        return cast(gpd.GeoDataFrame, all_connections_res)

    @cached_property
    def mismatches(self) -> gpd.GeoDataFrame:
        """
        Returns a GeoDataFrame containing all mismatches in the track topology.

        These mismatches represent connections that are not as expected and
        might indicate a problem in the underlying track topology.

        Returns
        -------
        gpd.GeoDataFrame
            A GeoDataFrame with all detected mismatches in the track topology.
        """
        valid_connections, _ = (
            self._process_functionele_spoortak()
        )  # TODO: This is a bit of a hack, but it works for now
        return cast(
            gpd.GeoDataFrame,
            valid_connections.loc[lambda d: d.mismatch is True],
        )

    @cached_property
    def all_connections(self) -> pd.DataFrame:
        """
        Creates a DataFrame with all connections between different spoortakken.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing all connections between spoortakken.
        """
        if not self.allconnections_path.exists() or self.overwrite:
            valid_connections, all_connections = (
                self._process_functionele_spoortak()
            )
            all_connections = self._mark_connections(
                all_connections, valid_connections
            )
            all_connections["length"] = all_connections.geometry.length

            self.cache_location.mkdir(exist_ok=True)
            if self.local_cache:
                all_connections.to_csv(self.allconnections_path)
            else:
                return all_connections
            logger.info(f"Saved all connections to {self.allconnections_path}")
        return pd.read_csv(self.allconnections_path, index_col=0)

    @cached_property
    def graphentries(self) -> dict[str, list[tuple[str, float]]]:
        """
        Creates a dictionary representing the connections between
        different spoortakken.

        The dictionary is structured as follows:
        {PUIC_left: [(PUIC_right, length), ...], ...}

        Returns
        -------
        dict[str, list[tuple[str, float]]]
            A dictionary where each key is a PUIC representing a track segment,
            and the value is a list of tuples containing the connected PUIC and
            the length of the connection.
        """
        valid_locations = self.all_connections.loc[
            lambda d: d.valid
        ].reset_index()
        graphentries = valid_locations[["PUIC_left", "PUIC_right", "length"]]

        return (
            graphentries.groupby("PUIC_left")
            .apply(lambda x: list(zip(x.PUIC_right, x.length)))
            .to_dict()
        )

    @cached_property
    def illegal_pairs_list(self) -> list[tuple[str, str]]:
        """
        Returns a list of illegal pairs of PUICs that should not be connected.

        These pairs represent track segments where the topology does not allow
        a train to travel from one to the other.

        Returns
        -------
        list of tuple[str, str]
            A list of illegal PUIC pairs structured as:
            [(PUIC_left, PUIC_right), ...]
        """
        return (
            self.all_connections.loc[lambda d: ~d.valid]
            .reset_index()
            .apply(lambda x: (x.PUIC_left, x.PUIC_right), axis=1)
            .tolist()
        )

    @staticmethod
    def expected_connections(row: pd.Series) -> int:
        """
        Calculates the expected number of connections for a
        given track segment.

        Parameters
        ----------
        row : pandas.Series
            A row representing a track segment.

        Returns
        -------
        int
            The expected number of connections.
        """
        connections = 0
        for begineind in ["_BEGIN", "_EIND"]:
            begrenzer = row[f"REF_BEGRENZER_TYPE{begineind}"]
            kantcode = row[f"KANTCODE_SPOORTAK{begineind}"]
            if begrenzer in [
                "EINDESPOOR",
                "STOOTJUK",
                "TERRA-INCOGNITA",
            ]:  # No significant connections
                connections += 0
            elif begrenzer == "KRUISING":  # Kruising, always connect to 1
                connections += 1
            elif begrenzer in [
                "WISSEL_EW",
                "WISSEL_HEW",
            ]:  # Engelse wissels, always connect to 2
                connections += 2
            elif begrenzer in [
                "WISSEL_GW"
            ]:  # Regular wissel, check at which side it connects
                if kantcode in ["L", "R"]:
                    connections += 1
                elif kantcode == "V":
                    connections += 2
                else:
                    logger.warning(
                        f"Unknown kantcode {kantcode} "
                        f"for begrenzer {begrenzer}"
                    )
            else:
                logger.warning(f"Unknown connection type {begrenzer}")
        return connections

    def _project_point(self, point: Point) -> str:
        """
        Projects a point to the nearest track and returns its PUIC.

        Parameters
        ----------
        point : Point
            The point to project onto the nearest track.

        Returns
        -------
        str
            The PUIC of the nearest track.
        """
        if point.x < 100:
            crs = "EPSG:4326"
        else:
            crs = "EPSG:28992"
        return (
            self.functionele_spoortak.to_crs(crs)
            .loc[
                lambda d: d.geometry.apply(
                    lambda x: x.distance(point)
                ).idxmin()
            ]
            .PUIC
        )

    def dijkstra(
        self, start: Point, end: Point, keringen_allowed: bool = False
    ) -> Route:
        """
        Finds the shortest path between two points using Dijkstra's algorithm.

        Parameters
        ----------
        start : shapely.geometry.Point
            The starting point.
        end : shapely.geometry.Point
            The destination point.
        keringen_allowed : bool, optional
            Whether or not to allow keringen (turnarounds) in the route,
            by default False.

        Returns
        -------
        Route
            A Route object representing the shortest path.

        Raises
        ------
        ValueError
            If no route is found between start and end.
        """
        if isinstance(start, Point):
            start_spoortak = self._project_point(start)
        else:
            start_spoortak = start
        if isinstance(end, Point):
            end_spoortak = self._project_point(end)
        else:
            end_spoortak = end

        # Priority queue to store (cost, current_node, path)
        pq: list[tuple[float, str, list[str]]] = [(0, start_spoortak, [])]
        visited = set()
        illegal_set = set(self.illegal_pairs_list)

        while pq:
            cost, node, path = heapq.heappop(pq)

            if node in visited:
                continue

            visited.add(node)
            path = path + [node]

            if node == end_spoortak:
                return Route(self.functionele_spoortak, path, start, end)

            if node not in self.graphentries:
                logger.debug(f"Node {node} not in graphentries")
                continue
            if keringen_allowed:
                for neighbor, weight in self.graphentries[node]:
                    if neighbor not in visited:
                        heapq.heappush(pq, (cost + weight, neighbor, path))
            else:
                # This greedy approach does not work if the best solution
                # would be revisiting a location
                # after making a circle and revisiting a previous location
                # at the exact same track.
                # This should not happen in the Netherlands due to the track
                # topology.
                for neighbor, weight in self.graphentries[node]:
                    if (node, neighbor) in illegal_set or (
                        neighbor,
                        node,
                    ) in illegal_set:
                        continue
                    if neighbor not in visited:
                        allowed = True
                        for p in path:
                            if (p, neighbor) in illegal_set or (
                                neighbor,
                                p,
                            ) in illegal_set:
                                allowed = False
                        if allowed:
                            heapq.heappush(pq, (cost + weight, neighbor, path))
        raise ValueError(
            f"No route found between {start_spoortak} and {end_spoortak}"
        )


class KruisingResolver:
    """
    This class filters the connections between the different
    spoortakken to only include the best match at kruisingen.
    At a kruising, two spoortakken will touch, but only one of them
    can actually be used.
    """

    def __init__(self, data: gpd.GeoDataFrame):
        self.data = data.assign(
            found_connections=lambda d: d.groupby(
                "PUIC_left"
            ).PUIC_right.transform("count")
        ).reset_index()

    def take_best_at_kruising(self) -> gpd.GeoDataFrame:
        """
        Filters the connections between different spoortakken to retain only
        the best match at kruisingen.

        Returns
        -------
        gpd.GeoDataFrame
            The filtered connections.
        """
        corrects = self._get_corrects()
        non_kruising_problem = self._get_non_kruising_problem()
        fixed_end = self._get_fixed_end()
        fixed_begin = self._get_fixed_begin()
        return cast(
            gpd.GeoDataFrame,
            pd.concat(
                [corrects, non_kruising_problem, fixed_end, fixed_begin]
            ).drop_duplicates(["PUIC_left", "PUIC_right"]),
        )

    def _get_corrects(self) -> gpd.GeoDataFrame:
        """
        Retrieves the connections that are correct, meaning the number of
        expected connections matches the number of found connections.

        Returns
        -------
        gpd.GeoDataFrame
            The connections that are correct.
        """
        return cast(
            gpd.GeoDataFrame,
            self.data.loc[
                lambda d: (d.expected_connections_left == d.found_connections)
            ].assign(source="correct"),
        )

    def _get_non_kruising_problem(self) -> gpd.GeoDataFrame:
        """
        Retrieves the connections that are incorrect and not at a kruising.
        These connections should still be reviewed later.

        Returns
        -------
        gpd.GeoDataFrame
            A GeoDataFrame containing the incorrect connections that are
            not at a kruising.
        """
        return cast(
            gpd.GeoDataFrame,
            (
                self.data.loc[
                    lambda d: (
                        d.expected_connections_left != d.found_connections
                    )
                ]
                .loc[
                    lambda d: (d.REF_BEGRENZER_TYPE_EIND_left != "KRUISING")
                    & (d.REF_BEGRENZER_TYPE_BEGIN_left != "KRUISING")
                ]
                .assign(source="non_kruising_problem")
            ),
        )

    def _get_fixed_begin(self) -> gpd.GeoDataFrame:
        """
        Retrieves the connections that are incorrect and occur at a kruising.

        Returns
        -------
        gpd.GeoDataFrame
            The connections that are incorrect and at a kruising.
        """
        connections = cast(
            gpd.GeoDataFrame,
            self.data.loc[
                lambda d: ((d.REF_BEGRENZER_TYPE_BEGIN_left == "KRUISING"))
            ],
        )
        best_match = cast(gpd.GeoDataFrame, self._get_best_match(connections))
        return cast(gpd.GeoDataFrame, best_match.assign(source="fixed_begin"))

    def _get_fixed_end(self) -> gpd.GeoDataFrame:
        """
        Retrieves the connections that are incorrect and occur at a kruising.

        Returns
        -------
        gpd.GeoDataFrame
            A GeoDataFrame containing the incorrect connections located
            at a kruising.
        """
        connections = cast(
            gpd.GeoDataFrame,
            self.data.loc[
                lambda d: ((d.REF_BEGRENZER_TYPE_EIND_left == "KRUISING"))
            ],
        )
        best_match = cast(gpd.GeoDataFrame, self._get_best_match(connections))
        return cast(gpd.GeoDataFrame, best_match.assign(source="fixed_end"))

    @staticmethod
    def _get_best_match(
        overlap_dataframe: gpd.GeoDataFrame,
    ) -> gpd.GeoDataFrame:
        """
        Finds the best connection for kruisingen by selecting the one with
        the smallest overlap area.
        This determines the correct spoortak connection.

        Parameters
        ----------
        overlap_dataframe : gpd.GeoDataFrame
            A DataFrame containing unfiltered kruisingen.

        Returns
        -------
        gpd.GeoDataFrame
            A DataFrame with the best match for each `PUIC_left`.
        """

        return cast(
            gpd.GeoDataFrame,
            overlap_dataframe.loc[
                lambda d: d.groupby("PUIC_left").intersection_area.transform(
                    "min"
                )
                == d.intersection_area
            ],
        )
