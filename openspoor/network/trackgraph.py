from openspoor.mapservices import FeatureServerOverview
from openspoor.visualisations import Route
import pandas as pd
from loguru import logger
from shapely.geometry import Point
import geopandas as gpd
from pathlib import Path
import heapq
from functools import cached_property


class TrackNetherlands:
    def __init__(self, overwrite=False):
        self.cache_location = Path('output')
        self.functionele_spoortak_path = self.cache_location / 'functionele_spoortak.gpkg'
        self.allconnections_path = self.cache_location / 'tracknetherlands.gpkg'
        self.overwrite = overwrite

    @cached_property
    def functionele_spoortak(self):
        if self.functionele_spoortak_path.exists() or self.overwrite:
            functionele_spoortak = gpd.read_file(self.functionele_spoortak_path)
        else:
            functionele_spoortak = FeatureServerOverview().search_for('functionele spoortak').load_data()            
            functionele_spoortak.to_file(self.functionele_spoortak_path, driver='GPKG')
            logger.info(f"Saved functionele spoortak to {self.functionele_spoortak_path}")
        
        functionele_spoortak = functionele_spoortak[['PUIC', 'NAAM', 'geometry', 'NAAM_LANG', 'REF_BEGRENZER_TYPE_EIND', 'REF_BEGRENZER_TYPE_BEGIN', 'KANTCODE_SPOORTAK_EIND', 'KANTCODE_SPOORTAK_BEGIN', 'REF_BEGRENZER_PUIC_BEGIN','REF_BEGRENZER_PUIC_EIND']]

        functionele_spoortak['expected_connections'] = functionele_spoortak.apply(self.expected_connections, axis=1)
        functionele_spoortak = functionele_spoortak[['PUIC', 'geometry', 'REF_BEGRENZER_TYPE_EIND', 'REF_BEGRENZER_TYPE_BEGIN', 'expected_connections']]
        
        return functionele_spoortak

    def _process_functionele_spoortak(self):
        joined = (
            self.functionele_spoortak
            .sjoin(
                (self.functionele_spoortak
                    .assign(geometry_right=lambda d: d.geometry)
                )
                , how='inner', predicate='touches')
            .assign(geometry_begin_left=lambda d: d.geometry.apply(lambda x: x.interpolate(0, normalized=True)))
            .assign(geometry_end_left=lambda d: d.geometry.apply(lambda x: x.interpolate(1, normalized=True)))
            .assign(geometry_begin_right=lambda d: d.geometry_right.apply(lambda x: x.interpolate(0, normalized=True)))
            .assign(geometry_end_right=lambda d: d.geometry_right.apply(lambda x: x.interpolate(1, normalized=True)))
        )

        joined['geometry_capped_left'] = joined.geometry.apply(lambda x: x.buffer(1, cap_style='flat'))
        joined['geometry_capped_right'] = joined.geometry_right.apply(lambda x: x.buffer(1, cap_style='flat'))
        joined['intersection_area'] = joined.apply(lambda d: d.geometry_capped_left.intersection(d.geometry_capped_right).area, axis=1)
        small_overlaps = joined[lambda d: d.intersection_area < 0.2]

        small_overlaps = small_overlaps.assign(found_connections=lambda d: d.groupby('PUIC_left').PUIC_right.transform('count')).reset_index()
        small_overlaps_filtered = KruisingResolver(small_overlaps).take_best_at_kruising()
        small_overlaps_filtered = small_overlaps_filtered.assign(found_connections_2=lambda d: d.groupby('PUIC_left').PUIC_right.transform('count'))
        small_overlaps_filtered.loc[lambda d: d.found_connections_2 != d.expected_connections_left].sort_values('PUIC_left')
        small_overlaps_filtered['mismatch'] = small_overlaps_filtered.apply(lambda x: x['found_connections_2'] != x['expected_connections_left'], axis=1)

        return small_overlaps_filtered

    def _identify_illegal_connections(self, all_connections, joined_valid_filtered):
        illegal_connections = all_connections.set_index(['PUIC_left', 'PUIC_right']).loc[lambda d: d.index.isin(joined_valid_filtered.set_index(['PUIC_left', 'PUIC_right']).index)==False].assign(illegal=True)[['illegal']]
        return illegal_connections

    def _mark_connections(self, all_connections, illegal_connections, joined_valid_filtered):
        all_connections = all_connections.set_index(['PUIC_left', 'PUIC_right'])
        all_connections['illegal'] = all_connections.index.isin(illegal_connections.index)
        all_connections['valid'] = all_connections.index.isin(joined_valid_filtered.set_index(['PUIC_left', 'PUIC_right']).index)
        return all_connections
    
    @cached_property
    def mismatches(self):
        joined_valid_filtered = self._process_functionele_spoortak()  #TODO: This is a bit of a hack, but it works for now
        return joined_valid_filtered.loc[lambda d: d.mismatch==True]
    
    @cached_property    
    def all_connections(self):
        if not self.allconnections_path.exists() or self.overwrite:
            joined_valid_filtered = self._process_functionele_spoortak()
            all_connections = self.functionele_spoortak.sjoin(self.functionele_spoortak, how='inner', predicate='touches')
            illegal_connections = self._identify_illegal_connections(all_connections, joined_valid_filtered)

            all_connections = self._mark_connections(all_connections, illegal_connections, joined_valid_filtered)

            self.cache_location.mkdir(exist_ok=True)
            all_connections.to_file(self.allconnections_path, driver='GPKG')
            logger.info(f"Saved all connections to {self.allconnections_path}")
        return gpd.read_file(self.allconnections_path)

    @cached_property
    def graphentries(self):
        valid_locations = self.all_connections.loc[lambda d: d.valid].reset_index()
        graphentries = valid_locations.assign(length=lambda d: d.geometry.length)[['PUIC_left', 'PUIC_right', 'length']]

        return graphentries.groupby('PUIC_left').apply(lambda x: list(zip(x.PUIC_right, x.length))).to_dict()
    
    @cached_property    
    def illegal_pairs_list(self):
        return self.all_connections.loc[lambda d: d.illegal].reset_index().apply(lambda x: (x.PUIC_left, x.PUIC_right), axis=1).tolist()

    @staticmethod
    def expected_connections(row):
        connections = 0
        for begineind in ['_BEGIN', '_EIND']:
            begrenzer = row[f'REF_BEGRENZER_TYPE{begineind}']
            kantcode = row[f'KANTCODE_SPOORTAK{begineind}']
            if begrenzer in ['EINDESPOOR',"STOOTJUK", "TERRA-INCOGNITA"]:
                connections += 0
            elif begrenzer =='KRUISING':
                connections +=1
            elif begrenzer in ['WISSEL_EW', 'WISSEL_HEW']:
                connections += 2
            elif begrenzer in ['WISSEL_GW']:
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
        
    def dijkstra(self, start, end, keringen_allowed=False):
        if isinstance(start, Point):
            start_spoortak = self._project_point(start)
        else:
            start_spoortak = start
        if isinstance(end, Point):
            end_spoortak = self._project_point(end)
        else:
            end_spoortak = end
            
        # Priority queue to store (cost, current_node, path)
        pq = [(0, start_spoortak, [])]
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

        return Route(self.functionele_spoortak, [], start, end)
    

class KruisingResolver:
    def __init__(self, small_overlaps):
        self.kruisingleft = {}
        self.small_overlaps = small_overlaps
        self.small_overlaps['kruising_begin_left'] = self.small_overlaps.REF_BEGRENZER_TYPE_BEGIN_left == 'KRUISING'
        self.small_overlaps['kruising_eind_left'] = self.small_overlaps.REF_BEGRENZER_TYPE_EIND_left == 'KRUISING'
        self.small_overlaps['kruising_begin_right'] = self.small_overlaps.REF_BEGRENZER_TYPE_BEGIN_right == 'KRUISING'
        self.small_overlaps['kruising_eind_right'] = self.small_overlaps.REF_BEGRENZER_TYPE_EIND_right == 'KRUISING'
        for (kruising_begin_left, kruising_eind_left), df_subset in (
            self.small_overlaps
            .loc[lambda d: (d.expected_connections_left == d.found_connections)]
            .groupby(['kruising_eind_left', 'kruising_begin_left'])):
            logger.debug(f"{kruising_begin_left} {kruising_eind_left}")
            self.kruisingleft[(kruising_begin_left, kruising_eind_left)] = df_subset.reset_index()

    def take_best_at_kruising(self):

        corrects = self._get_corrects()
        nonproblem = self._get_nonproblem()
        nonproblem_end = self._get_nonproblem_end()
        nonproblem_begin = self._get_nonproblem_begin()
        fixed_end = self._get_fixed_end()
        fixed_begin = self._get_fixed_begin()

        return pd.concat([corrects, nonproblem, nonproblem_begin, nonproblem_end, fixed_end, fixed_begin]).drop_duplicates(['PUIC_left', 'PUIC_right'])
        

    def _get_corrects(self):
        return self.small_overlaps.loc[lambda d: (d.expected_connections_left == d.found_connections)].assign(source='correct')

    def _get_nonproblem(self):
        return self.kruisingleft[(False, False)].assign(source='nonproblem')

    def _get_nonproblem_end(self):
        try:
            return (self.kruisingleft[(False, True)]
                .apply(self._no_relevant_kruising, axis=1)
                .assign(source='nonproblem_end'))
        except KeyError:
            return pd.DataFrame()

    def _get_nonproblem_begin(self):
        try:
            return (            
                self.kruisingleft[(True, False)]
                .apply(self._no_relevant_kruising, axis=1)
                .assign(source='nonproblem_begin')
            )
        except KeyError:
            return pd.DataFrame()

    def _get_fixed_begin(self):
        return (
            self.small_overlaps            
            .loc[lambda d: ((d.REF_BEGRENZER_TYPE_BEGIN_left=='KRUISING') | (d.REF_BEGRENZER_TYPE_BEGIN_right=='KRUISING')) & \
                ((d.kruising_begin_left==d.kruising_eind_right) | (d.kruising_begin_left==d.kruising_begin_right))]
            .pipe(self._get_best_match)
            .assign(source='fixed_begin')
        )

    def _get_fixed_end(self):
        return (
            self.small_overlaps
            .loc[lambda d: ((d.REF_BEGRENZER_TYPE_EIND_left=='KRUISING') | (d.REF_BEGRENZER_TYPE_EIND_right=='KRUISING')) & \
                ((d.kruising_eind_left==d.kruising_eind_right) | (d.kruising_eind_left==d.kruising_begin_right))]
            .pipe(self._get_best_match)
            .assign(source='fixed_begin')
        )
    
    @staticmethod    
    def _get_best_match(overlap_dataframe):
        return overlap_dataframe.loc[lambda d: d.groupby('PUIC_left').intersection_area.transform('min') == d.intersection_area]
    
    @staticmethod
    def _no_relevant_kruising(overlap_dataframe):
        return overlap_dataframe.loc[lambda d: (d.geometry_end_left != d.geometry_end_right) & (d.geometry_end_left != d.geometry_begin_right)]