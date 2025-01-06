from openspoor.mapservices import FeatureServerOverview
from openspoor.visualisations import Route
import pandas as pd
from loguru import logger
from shapely.geometry import Point
import geopandas as gpd
from pathlib import Path
import heapq

class TrackNetherlands:
    def __init__(self, overwrite=False):
        self.cache_location = Path('output')
        self.functionele_spoortak_path = self.cache_location / 'functionele_spoortak.gpkg'
        self.alltouches_path = self.cache_location / 'tracknetherlands.gpkg'

        if overwrite or not(self.alltouches_path.exists() and self.functionele_spoortak_path.exists()):
            functionele_spoortak = FeatureServerOverview().search_for('functionele spoortak').load_data()
            functionele_spoortak = functionele_spoortak[['PUIC', 'NAAM', 'geometry', 'NAAM_LANG', 'REF_BEGRENZER_TYPE_EIND', 'REF_BEGRENZER_TYPE_BEGIN', 'KANTCODE_SPOORTAK_EIND', 'KANTCODE_SPOORTAK_BEGIN', 'REF_BEGRENZER_PUIC_BEGIN','REF_BEGRENZER_PUIC_EIND']]

            functionele_spoortak['expected_connections'] = functionele_spoortak.apply(self.expected_connections, axis=1)
            functionele_spoortak = functionele_spoortak[['PUIC', 'geometry', 'REF_BEGRENZER_TYPE_EIND',
        'REF_BEGRENZER_TYPE_BEGIN', 'expected_connections']]
            joined = (
                functionele_spoortak
                .sjoin(
                    (functionele_spoortak
                        .assign(geometry_right=lambda d: d.geometry)
                    )
                    , how='inner',predicate='touches')
                .assign(geometry_left_begin = lambda d: d.geometry.apply(lambda x: x.interpolate(0, normalized=True)))
                .assign(geometry_left_end = lambda d: d.geometry.apply(lambda x: x.interpolate(1, normalized=True)))
                .assign(geometry_right_begin = lambda d: d.geometry_right.apply(lambda x: x.interpolate(0, normalized=True)))
                .assign(geometry_right_end = lambda d: d.geometry_right.apply(lambda x: x.interpolate(1, normalized=True)))
            )

            joined['geometry_left_capped'] = joined.geometry.apply(lambda x: x.buffer(1, cap_style='flat'))
            joined['geometry_right_capped'] = joined.geometry_right.apply(lambda x: x.buffer(1, cap_style='flat'))
            joined['intersection_area'] = joined.apply(lambda d: d.geometry_left_capped.intersection(d.geometry_right_capped).area, axis=1)
            joined_valid = joined[lambda d: d.intersection_area < 0.2]

            joined_valid = joined_valid.assign(found_connections=lambda d: d.groupby('PUIC_left').PUIC_right.transform('count'))

            joined_valid_filtered = self.take_best_at_kruising(joined_valid)

            joined_valid_filtered = joined_valid_filtered.assign(found_connections_2=lambda d: d.groupby('PUIC_left').PUIC_right.transform('count'))
            joined_valid_filtered.loc[lambda d: d.found_connections_2 != d.expected_connections_left].sort_values('PUIC_left')
            joined_valid_filtered['mismatch'] = joined_valid_filtered.apply(lambda x: x['found_connections_2'] != x['expected_connections_left'], axis=1)

            self.mismatches = joined_valid_filtered.loc[lambda d: d.mismatch==True]

            alltouches = functionele_spoortak.sjoin(functionele_spoortak, how='inner',predicate='touches')

            #TODO: Is this only unallowed keringen or does this contain more? Both parts of a kruising may be part of the best route. Create unit test for this
            #TODO: Merge these back in original dataframe, with an additional column. For caching the output
            illegal_touches = alltouches.set_index(['PUIC_left', 'PUIC_right']).loc[lambda d: d.index.isin(joined_valid_filtered.set_index(['PUIC_left', 'PUIC_right']).index)==False].assign(illegal=True)[['illegal']]

            illegal_index = illegal_touches.index
            valid_index = joined_valid_filtered.set_index(['PUIC_left', 'PUIC_right']).index

            alltouches = alltouches.set_index(['PUIC_left', 'PUIC_right'])
            alltouches['illegal'] = False
            alltouches.loc[illegal_index, ['illegal']] = True

            alltouches['valid'] = False
            alltouches.loc[valid_index, ['valid']] = True

            self.cache_location.mkdir(exist_ok=True)
            alltouches.to_file(self.alltouches_path, driver='GPKG')
            functionele_spoortak.to_file(self.functionele_spoortak_path, driver='GPKG')
            logger.success("TrackNetherlands created and cached")

        logger.info("Loading cached TrackNetherlands")        
        alltouches = gpd.read_file(self.alltouches_path)
        functionele_spoortak = gpd.read_file(self.functionele_spoortak_path)

        valid_locations = alltouches.loc[lambda d: d.valid].reset_index()
        illegal_pairs = alltouches.loc[lambda d: d.illegal]
        graphentries = valid_locations.assign(length=lambda d: d.geometry.length)[['PUIC_left', 'PUIC_right', 'length']]

        self.graphentries = graphentries.groupby('PUIC_left').apply(lambda x: list(zip(x.PUIC_right, x.length))).to_dict()
        self.illegal_pairs_list = illegal_pairs.reset_index().apply(lambda x: (x.PUIC_left, x.PUIC_right), axis=1).tolist()
        self.functionele_spoortak = functionele_spoortak

        logger.success("TrackNetherlands created")

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
    

    def take_best_at_kruising(self, joined_valid):
        corrects = joined_valid.loc[lambda d: (d.expected_connections_left == d.found_connections)].assign(source='correct')

        nonproblem = (
            joined_valid
            .loc[lambda d: (d.REF_BEGRENZER_TYPE_BEGIN_left!='KRUISING') & (d.REF_BEGRENZER_TYPE_EIND_left!='KRUISING')]
            .assign(source='nonproblem')
        )

        nonproblem_end = (
            joined_valid
            .loc[lambda d: d.REF_BEGRENZER_TYPE_EIND_left=='KRUISING']
            .loc[lambda d: d.REF_BEGRENZER_TYPE_BEGIN_left!='KRUISING']
            .loc[lambda d: (d.geometry_left_end!=d.geometry_right_end) & (d.geometry_left_end!=d.geometry_right_begin)]
            .assign(source='nonproblem_end')
        )

        nonproblem_begin = (
            joined_valid
            .loc[lambda d: d.REF_BEGRENZER_TYPE_BEGIN_left=='KRUISING']
            .loc[lambda d: d.REF_BEGRENZER_TYPE_EIND_left!='KRUISING']
            .loc[lambda d: (d.geometry_left_begin!=d.geometry_right_begin) & (d.geometry_left_begin!=d.geometry_right_end)]
            .assign(source='nonproblem_begin')
        )
        fixed_begin = (
            joined_valid
            .loc[lambda d: ((d.REF_BEGRENZER_TYPE_BEGIN_left=='KRUISING') | (d.REF_BEGRENZER_TYPE_BEGIN_right=='KRUISING')) & \
                ((d.geometry_left_begin==d.geometry_right_end) | (d.geometry_left_begin==d.geometry_right_begin))]
            .loc[lambda d: d.groupby('PUIC_left').intersection_area.transform('min') == d.intersection_area]
            .assign(source='fixed_begin')
        )

        fixed_end = (
            joined_valid
            .loc[lambda d: ((d.REF_BEGRENZER_TYPE_EIND_left=='KRUISING') | (d.REF_BEGRENZER_TYPE_EIND_right=='KRUISING')) & \
                ((d.geometry_left_end==d.geometry_right_end) | (d.geometry_left_end==d.geometry_right_begin))]
            .loc[lambda d: d.groupby('PUIC_left').intersection_area.transform('min') == d.intersection_area]
            .assign(source='fixed_end')
        )

        return pd.concat([corrects, nonproblem, nonproblem_begin, nonproblem_end, fixed_end, fixed_begin]).drop_duplicates(['PUIC_left', 'PUIC_right'])    

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

