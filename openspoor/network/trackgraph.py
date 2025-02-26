import pandas as pd
from loguru import logger
from shapely.geometry import Point
import geopandas as gpd
from pathlib import Path
import heapq
from functools import cached_property

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
        self.cache_location = Path('output')
        self.functionele_spoortak_path = self.cache_location / 'functionele_spoortak.gpkg'
        self.allconnections_path = self.cache_location / 'tracknetherlands.csv'
        self.overwrite = overwrite

    @cached_property
    def functionele_spoortak(self) -> gpd.GeoDataFrame:
        """
        :return: The GeoDataFrame with the functionele spoortakken
        """
        relevant_columns = [['PUIC', 'NAAM', 'geometry', 'NAAM_LANG', 'REF_BEGRENZER_TYPE_EIND', 'REF_BEGRENZER_TYPE_BEGIN', 
                             'KANTCODE_SPOORTAK_EIND', 'KANTCODE_SPOORTAK_BEGIN', 'REF_BEGRENZER_PUIC_BEGIN','REF_BEGRENZER_PUIC_EIND']]
        if self.functionele_spoortak_path.exists() or self.overwrite:
            functionele_spoortak = gpd.read_file(self.functionele_spoortak_path)
        else:
            functionele_spoortak = FeatureServerOverview().search_for('functionele spoortak').load_data()
            functionele_spoortak['expected_connections'] = functionele_spoortak.apply(self.expected_connections, axis=1)   
            if self.local_cache:  
                functionele_spoortak.to_file(self.functionele_spoortak_path, driver='GPKG')[relevant_columns]
                logger.info(f"Saved functionele spoortak to {self.functionele_spoortak_path}")   
        return functionele_spoortak

    def _process_functionele_spoortak(self) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """
        Process the functionele spoortakken to find the connections between the different spoortakken.

        :return: A tuple with the valid connections and all connections        
        """
        touching_spoortakken = (
            self.functionele_spoortak
            .sjoin(
                (self.functionele_spoortak
                    .assign(geometry_right=lambda d: d.geometry)
                )
                , how='inner', predicate='touches')
        )

        small_overlaps = self.get_small_overlaps(touching_spoortakken)  # Filter on spoortakken that are roughly consecutive
        small_overlaps_cleaned = KruisingResolver(small_overlaps).take_best_at_kruising()  # At kruisingen, take the best match
        return self._recheck_connections(small_overlaps_cleaned), touching_spoortakken  # Recheck if the connections are correct after the filtering
    
    def get_small_overlaps(self, joined: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Filter the connections between the different spoortakken to only include the connections that are roughly consecutive. This is done by checking the area of the intersection between the two spoortakken.

        :param joined: The GeoDataFrame with the connections between the different spoortakken
        :return: The GeoDataFrame with the filtered connections        
        """
        joined['geometry_capped_left'] = joined.geometry.apply(lambda x: x.buffer(1, cap_style='flat'))
        joined['geometry_capped_right'] = joined.geometry_right.apply(lambda x: x.buffer(1, cap_style='flat'))
        joined['intersection_area'] = joined.apply(lambda d: d.geometry_capped_left.intersection(d.geometry_capped_right).area, axis=1)
        return joined[lambda d: d.intersection_area < 0.2].drop(columns=['geometry_capped_left', 'geometry_capped_right'])
    
    def _recheck_connections(self, gdf_cleaned: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Recheck the connections between the different spoortakken to see if the connections
        are as expected. This is done by checking if the number of connections is as expected.

        :param gdf_cleaned: The GeoDataFrame with the cleaned connections
        :return: The GeoDataFrame with the rechecked connections        
        """
        gdf_cleaned = gdf_cleaned.assign(found_connections_2=lambda d: d.groupby('PUIC_left').PUIC_right.transform('count'))
        gdf_cleaned.loc[lambda d: d.found_connections_2 != d.expected_connections_left].sort_values('PUIC_left')
        gdf_cleaned['mismatch'] = gdf_cleaned.apply(lambda x: x['found_connections_2'] != x['expected_connections_left'], axis=1)
        return gdf_cleaned

    def _mark_connections(self, all_connections: gpd.GeoDataFrame, valid_connections: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Tag every connection as illegal, valid or neither. This is based on the expected connections and the actual connections.

        :param all_connections: The GeoDataFrame with all connections
        :param joined_valid_filtered: The GeoDataFrame with the valid connections
        :return: The GeoDataFrame with all connections marked as illegal or valid
        """

        all_connections = all_connections.set_index(['PUIC_left', 'PUIC_right'])
        all_connections['valid'] = all_connections.index.isin(valid_connections.set_index(['PUIC_left', 'PUIC_right']).index)
        return all_connections
    
    @cached_property
    def mismatches(self)->gpd.GeoDataFrame:
        """
        Return a GeoDataFrame with all the mismatches in the track topology. These are the connections that are not as expected.
        This might indicate a problem in the underlying topology of the track.

        :return: The GeoDataFrame with all the mismatches        
        """
        valid_connections, _ = self._process_functionele_spoortak()  #TODO: This is a bit of a hack, but it works for now
        return valid_connections.loc[lambda d: d.mismatch==True]
    
    @cached_property    
    def all_connections(self)-> pd.DataFrame:
        """
        Create a GeoDataFrame with all connections between the different spoortakken. 

        :return: The GeoDataFrame with all connections        
        """
        if not self.allconnections_path.exists() or self.overwrite:
            valid_connections, all_connections = self._process_functionele_spoortak()
            all_connections = self._mark_connections(all_connections, valid_connections)
            all_connections['length'] = all_connections.geometry.length

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
        Create a dictionary with the connections between the different spoortakken. The dictionary is structured as follows:
        {PUIC_left: [(PUIC_right, length), ...], ...}

        :return: The dictionary with the connections        
        """
        valid_locations = self.all_connections.loc[lambda d: d.valid].reset_index()
        graphentries = valid_locations[['PUIC_left', 'PUIC_right', 'length']]

        return graphentries.groupby('PUIC_left').apply(lambda x: list(zip(x.PUIC_right, x.length))).to_dict()
    
    @cached_property    
    def illegal_pairs_list(self) -> list[tuple[str, str]]:
        """
        Return a list of illegal pairs of PUICs. These are the pairs that should not be connected due to the track topology not allowing a train to drive from one to the other.
        The list is structured as follows:
        [(PUIC_left, PUIC_right), ...]        
        """
        return self.all_connections.loc[lambda d: ~d.valid].reset_index().apply(lambda x: (x.PUIC_left, x.PUIC_right), axis=1).tolist()

    @staticmethod
    def expected_connections(row: pd.Series) -> int:
        """
        For a given spoortak, calculate the expected number of connections (on both sides combined).

        :param row: The row of the spoortak

        :return: The expected number of connections
        """
        connections = 0
        for begineind in ['_BEGIN', '_EIND']:
            begrenzer = row[f'REF_BEGRENZER_TYPE{begineind}']
            kantcode = row[f'KANTCODE_SPOORTAK{begineind}']
            if begrenzer in ['EINDESPOOR',"STOOTJUK", "TERRA-INCOGNITA"]:  # No significant connections
                connections += 0
            elif begrenzer =='KRUISING':  # Kruising, always connect to 1
                connections +=1
            elif begrenzer in ['WISSEL_EW', 'WISSEL_HEW']:  # Engelse wissels, always connect to 2
                connections += 2
            elif begrenzer in ['WISSEL_GW']:  # Regular wissel, check at which side it connects
                if kantcode  in ['L', "R"]:
                    connections += 1
                elif kantcode =='V':
                    connections += 2
                else:
                    logger.warning(f"Unknown kantcode {kantcode} for begrenzer {begrenzer}")
            else:
                logger.warning(f"Unknown connection type {begrenzer}")
        return connections


    def _project_point(self, point: Point) -> str:
        """
        Project a point to the nearest track

        :param point: The point to project
        :return: The PUIC of the nearest track
        """
        if point.x <100:
            crs = 'EPSG:4326'
        else:
            crs = 'EPSG:28992'
        return self.functionele_spoortak.to_crs(crs).loc[lambda d: d.geometry.apply(lambda x: x.distance(point)).idxmin()].PUIC
        
    def dijkstra(self, start: Point, end: Point, keringen_allowed: bool = False) -> Route:
        """
        Find the shortest path between two points on the track. This is done using Dijkstra's algorithm.

        :param start: The start point of the route
        :param end: The end point of the route
        :param keringen_allowed: Whether or not to allow keringen in the route

        :return: The Route object with the shortest path
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
                #This greedy approach does not work if the best solution would be revisiting a location
                #after making a circle and revisiting a previous location at the exact same track.
                #This should not happen in the Netherlands due to the track topology.
                for neighbor, weight in self.graphentries[node]:
                    if (node, neighbor) in illegal_set or (neighbor, node) in illegal_set:  
                        continue
                    if neighbor not in visited:
                        allowed =True
                        for p in path:
                            if (p, neighbor) in illegal_set or (neighbor, p) in illegal_set:
                                allowed = False
                        if allowed:                
                            heapq.heappush(pq, (cost + weight, neighbor, path))
        raise ValueError(f"No route found between {start_spoortak} and {end_spoortak}")
    

class KruisingResolver:
    """
    This class filters the connections between the different 
    spoortakken to only include the best match at kruisingen.
    At a kruising, two spoortakken will touch, but only one of them
    can actually be used.    
    """
    def __init__(self, data: gpd.GeoDataFrame):
        self.data = data.assign(found_connections=lambda d: d.groupby('PUIC_left').PUIC_right.transform('count')).reset_index()

    def take_best_at_kruising(self)->gpd.GeoDataFrame:
        """
        Filter the connections between the different spoortakken to only include the best match at kruisingen.

        :return: The filtered connections        
        """
        corrects = self._get_corrects()
        non_kruising_problem = self._get_non_kruising_problem()
        fixed_end = self._get_fixed_end()
        fixed_begin = self._get_fixed_begin()        
        return pd.concat([corrects, non_kruising_problem, fixed_end, fixed_begin]).drop_duplicates(['PUIC_left', 'PUIC_right'])
        

    def _get_corrects(self)->gpd.GeoDataFrame:
        """
        Get the connections that are correct. This means that the number of expected connections is equal to the number of found connections.

        :return: The connections that are correct        
        """
        return self.data.loc[lambda d: (d.expected_connections_left == d.found_connections)].assign(source='correct')

    def _get_non_kruising_problem(self)->gpd.GeoDataFrame:
        """
        Get the connections that are not correct and are not at a kruising.
        These should still be looked at later.

        :return: The connections that are not correct and are not at a kruising
        """
        return (
            self.data
            .loc[lambda d: (d.expected_connections_left != d.found_connections)]
            .loc[lambda d: (d.REF_BEGRENZER_TYPE_EIND_left != 'KRUISING') & (d.REF_BEGRENZER_TYPE_BEGIN_left != 'KRUISING')]
            .assign(source='non_kruising_problem')
        )

    def _get_fixed_begin(self)->gpd.GeoDataFrame:
        """
        Get the connections that are not correct and are at a kruising.

        :return: The connections that are not correct and are at a kruising        
        """
        return (
            self.data  
            .loc[lambda d: ((d.REF_BEGRENZER_TYPE_BEGIN_left=='KRUISING'))]
            .pipe(self._get_best_match)
            .assign(source='fixed_begin')
        )

    def _get_fixed_end(self)->gpd.GeoDataFrame:
        """
        Get the connections that are not correct and are at a kruising.

        :return: The connections that are not correct and are at a kruising
        """
        return (
            self.data
            .loc[lambda d: ((d.REF_BEGRENZER_TYPE_EIND_left=='KRUISING'))]
            .pipe(self._get_best_match)
            .assign(source='fixed_begin')
        )
    
    @staticmethod    
    def _get_best_match(overlap_dataframe: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        For kruisingen specifically, look for the connection with the smallest overlap area. This is the one to which the spoortak should connect.

        :param overlap_dataframe: A dataframe with unfiltered kruisingen.

        :return: A dataframe with the best match for each PUIC_left        
        """
        return overlap_dataframe.loc[lambda d: d.groupby('PUIC_left').intersection_area.transform('min') == d.intersection_area]
