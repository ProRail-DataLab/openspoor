from __future__ import annotations
import pandas as pd
import folium
from loguru import logger

from shapely.geometry import point, polygon, linestring
import geopandas as gpd
from typing import List, Optional, Dict, Tuple, Union
from pathlib import Path
from urllib.parse import quote
from ..utils.common import read_config
from abc import ABC, abstractmethod

config = read_config()


class PlotObject(ABC):
    """
    A parent class for every object that can be plotted on a TrackMap
    """

    def __init__(self, data, popup):
        if popup is None or isinstance(popup, list):
            self.popup = popup
        elif isinstance(popup, str):
            self.popup = [popup]
        else:
            TypeError('Unknown type for popup in linestrings')

        if isinstance(data, gpd.GeoDataFrame):
            self.data = data
        elif isinstance(data, str):
            self.data = gpd.read_file(data)
        else:
            raise TypeError('Provide either a geopandas dataframe or a file location of a csv to show')
        self.data = self.data.to_crs('EPSG:4326')
        if self.popup is not None:
            self.data = self.data.set_index(self.popup)

    @abstractmethod
    def add_to(self, m) -> None:
        """
        A base function that should be overwritten with logic for every plottable object.

        :param m: A TrackMap object, to which this element should be added.
        :return: None
        """
        raise NotImplementedError('This needs to be set in implementation classes')

    def show(self):
        return TrackMap([self]).show()


class TrackMap(folium.Map):
    """
    Plotting functionality based on folium maps, designed for plotting objects on the Dutch railways.
    Plottable objects are based on geopandas GeoDataFrames; with the function plottable they can be converted to
    a PlotObject that can be used for this class.
    Outputs are automatically zoomed in on what data is requested and include an aerial photograph of the Netherlands.
    Maps can be shown directly, or saved as .html files.
    """

    def __init__(self, objects: List[PlotObject] = [], add_aerial=True, **kwargs):
        """
        Set up a TrackMap object.

        :param objects: A list of plottable objects that can be pre-defined outside the context manager of the
        TrackMap
        :param add_aerial: Whether you want to include the ProRail aerial photograph or not
        :return: A TrackMap object
        """

        super().__init__(location=[52, 5], zoom_start=8, max_zoom=30, max_native_zoom=30, tiles=None, **kwargs)
        if add_aerial:
            self._add_aerial_photograph()

        # TODO: Remove this altogether?
        for obj in objects:
            assert issubclass(type(obj), PlotObject), f'Unable to plot {obj}, not defined as plottable object'
            self.add(obj)

    def _add_aerial_photograph(self) -> None:
        """
        Add the most recent ProRail aerial photograph to the map.

        :return: None
        """
        fg = folium.FeatureGroup(name=f"aerial_photograph", max_zoom=30, max_native_zoom=30)
        folium.WmsTileLayer(url='https://luchtfoto.prorail.nl/erdas-iws/ogc/wms/Luchtfoto', layers='meest_recent',
                            transparent=True, overlay=False,
                            maxZoom=30, maxNativeZoom=30).add_to(fg)
        folium.TileLayer('openstreetmap', transparent=True, opacity=0.2).add_to(fg)
        self.add_child(fg)

    def _fix_zoom(self) -> None:
        """
        Set the zoom level so all the plotted objects fit neatly within the initial view of the output.

        :return: None
        """
        # Bboxes are stored as a List of [min_lat, min_lon, max_lat, max_lon]
        bboxes = []

        for _, item in self._children.items():
            if isinstance(item, folium.features.Choropleth):  # For linestrings
                bboxes.extend(feature['bbox'][::-1] for feature in item.geojson.data['features'])
            if isinstance(item, folium.features.GeoJson):  # For linestrings and areas
                bboxes.append([i for coords in item.get_bounds() for i in coords])
            if isinstance(item, folium.map.Marker):  # For markers
                bboxes.append(item.location * 2)  # Min and max bound are equal for points, hence the repeat

        if bboxes:  # Fit only if there are some items to show
            bounds = [min(map(lambda x: x[i], bboxes)) if i < 2 else max(map(lambda x: x[i], bboxes)) for i in range(4)]
            # Convert into [[min_lat, min_lon], [max_lat, max_lon]]
            self.fit_bounds([bounds[:2], bounds[2:]])

    def add(self, plotobject) -> TrackMap:
        plotobject.add_to(self)
        return self

    def show(self, notebook: bool = False) -> Union[TrackMap, folium.Figure]:
        """
        Show the map zoomed to a nice level and displayed at a suitable size.

        :param notebook: A boolean for decreasing the size of the final plot. Designed for use in Notebooks
        :return:
        """
        self._fix_zoom()
        if notebook:
            # Add a folium map inside a folium figure. This is the easiest way to change the figure size
            figure = folium.Figure(1000, 400)
            self.add_to(figure)
            return figure
        else:
            return self

    def save(self, save_name: Path) -> None:
        """
        Save the map to a given directory
        :param save_name: A Path where the final .html file could be written to
        :return: Nothing, the map is saved
        """

        self.show()
        super(TrackMap, self).save(save_name)


class PlottingPoints(PlotObject):
    """
    Add functionalities to a Pandas DataFrame, so it can be plotted in a nice manner.
    """

    def __init__(self, data, popup: Optional[Union[str, List[str]]] = None,
                 lat_column: Optional[str] = 'lat', lon_column: Optional[str] = 'lon',
                 colors: Dict[str, Dict[Tuple[float, float], str]] = None,
                 markertype: Optional[str] = None, marker_column: str = None, color_column: str = None,
                 rotation_column: str = None, radius_column: str = None, url_column: str = None):
        """
        Initialize a PlottingPoints object, used for plotting a list of markers on a map of the Netherlands.

        :param data: The Pandas DataFrame that should be plotted. GeoPandas dataframes are also partially supported
        :param lat_column: A column including latitudes. Not required if data is a geopandas GeoDataFrame
        :param lon_column: A column name including longitudes. Not required if data is a geopandas GeoDataFrame
        :param popup: A column or list of columns whose values should be mentioned when an object is clicked on
        :param colors: A dictionary, noting on what column to base the colors on and what values they should take
        depending on the registered value.
        :param markertype: 'circle' if circles are required, or an icon name found in
        # https://fontawesome.com/v4/icons/
        :param marker_column: A column including the names of the markers to display
        :param color_column: A column that can be  used for the colors of the markers
        :param rotation_column: A column noting the degrees of rotation in the range (0,360)
        :param radius_column: A column noting the radius of the circles to plot (if markertype=='circle')
        :param url_column: A column including an url that is displayed in the popup
        """

        # Do some pre-processing for the cases the data is not a GeoDataFrame
        if isinstance(data, dict):
            data = pd.DataFrame(data)

        if isinstance(data, pd.DataFrame) and not isinstance(data, gpd.geodataframe.GeoDataFrame):
            data = (
                gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data[lon_column], data[lat_column]), crs='EPSG:4326')
            )
        if rotation_column:
            data[rotation_column + '_for_plotting'] = data[rotation_column]
        self.color_column = color_column
        if self.color_column is not None:
            data[self.color_column + "_factorized"] = pd.factorize(data[self.color_column])[0]

        super().__init__(data, popup)

        if isinstance(data, gpd.GeoDataFrame):
            if isinstance(data.geometry.iloc[0], point.Point):
                data = data.to_crs('EPSG:4326')
                self.data['lat'] = data.geometry.apply(lambda d: d.y)
                self.data['lon'] = data.geometry.apply(lambda d: d.x)
            else:
                NotImplementedError(f"Unimplemented geometry: {data.geometry.iloc[0]}")

        # TODO: Automatically do this by looping through args?
        self.markertype = markertype
        self.colors = colors
        self.marker = marker_column
        self.rotation = rotation_column
        self.radius = radius_column
        self.url_column = url_column

    def add_to(self, folium_map):
        for i, row in self.data.iterrows():
            if isinstance(i, tuple):
                indexnames = i
            else:
                indexnames = (i,)
            location = row.geometry.y, row.geometry.x
            if self.popup:
                popup_text = ''
                for indexvalue, col in zip(indexnames, self.popup):
                    if col == self.url_column:
                        url = quote(row[col], safe='/:?=&')  # Replaces characters unsuitable for URL's
                        popup_text = popup_text + f"{col}: <a href={url}>Hyperlink</a><br>",
                    else:
                        popup_text = popup_text + f'{col}: {indexvalue}<br>'
            else:
                popup_text = None

            if self.rotation is not None:
                rotation = int(row[self.rotation + '_for_plotting'])
                marker = 'arrow-up'
            else:
                rotation = 0

                if self.marker is not None:
                    marker = row[self.marker]
                elif self.markertype is not None:
                    marker = self.markertype
                else:
                    marker = config['default_marker']

            if self.color_column is not None:
                colorset = ['purple', 'lightblue', 'darkgreen', 'blue', 'darkred', 'black',
                            'pink', 'cadetblue', 'lightgray', 'lightred', 'green',
                            'beige', 'darkblue', 'darkpurple', 'orange', 'lightgreen', 'red']
                marker_color = colorset[int(row[self.color_column + "_factorized"]) % len(colorset)]

            elif self.colors is not None:
                if isinstance(self.colors, str):
                    marker_color = self.colors
                else:
                    for column, colormap in self.colors.items():
                        for bounds, color in colormap.items():
                            if min(bounds) <= row[column] <= max(bounds):
                                marker_color = color
            else:
                marker_color = config['default_color']
            if self.markertype == 'circle':
                if self.radius is not None:
                    radius = row[self.radius]
                else:
                    radius = config['default_radius']
                folium.Circle(
                    radius=radius,
                    location=location,
                    popup=popup_text,
                    color=marker_color,
                    fill=False,
                ).add_to(folium_map)
            else:
                folium.Marker(location,
                              popup=popup_text,
                              icon=folium.Icon(color=marker_color, prefix='fa', icon=marker, angle=rotation)).add_to(
                    folium_map)
        return folium_map


class PlottingLineStrings(PlotObject):
    """
    An object that can be plotted on a TrackMap. This is based on a geopandas dataframe or a file with every row
    indicating an item to show.

    """

    def __init__(self, data: Union[gpd.GeoDataFrame, str], popup: Optional[Union[str, List[str]]] = None,
                 color: str = 'blue', buffersize: int = 3):
        """
        Initialize a PlottingLineStrings object.

        :param data: A geopandas dataframe or a file location of a csv file
        :param popup: The column(s) whose values are shown when hovering over a linestring
        :param color: The color in which the linestrings should be shown on the map
        :param buffersize: The size of the buffer around the linestrings on the map.
        """

        super().__init__(data, popup)
        self.color = color

        self.buffersize = buffersize  # In meters

    def _make_tooltip(self):
        return folium.features.GeoJsonTooltip(
            fields=self.popup,
            aliases=self.popup,
            style="background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"
        )

    def add_to(self, folium_map: TrackMap) -> TrackMap:
        """
        Add Linestrings to a TrackMap object

        :param folium_map: The map to add the objects to
        :return: The updated map
        """
        # Add lines
        folium.Choropleth(
            self.data['geometry'],
            line_weight=3,
            line_color=self.color,
        ).add_to(folium_map)

        # Add hover functionality.
        style_function = lambda x: {'fillColor': '#ffffff', 'color': '#000000', 'fillOpacity': 0.1, 'weight': 0.1}
        highlight_function = lambda x: {'fillColor': '#000000', 'color': '#000000', 'fillOpacity': 0.50, 'weight': 0.1}

        if self.popup:
            tooltip = self._make_tooltip()
        else:
            tooltip = None

        sectie_hover = folium.features.GeoJson(
            data=self.data.assign(
                geometry=lambda x: x.geometry.to_crs('EPSG:28992').buffer(self.buffersize)).reset_index(),
            style_function=style_function,
            control=False,
            highlight_function=highlight_function,
            tooltip=tooltip
        )
        folium_map.add_child(sectie_hover)
        folium_map.keep_in_front(sectie_hover)
        return folium_map


class PlottingAreas(PlotObject):
    """
    An object that can be plotted on a TrackMap. This is based on a geopandas dataframe or a file with every row
    indicating an item to show.

    """

    def __init__(self, data: Union[gpd.GeoDataFrame, str],
                 popup: Optional[Union[str, List[str]]] = None,
                 color: str = 'orange',
                 stroke: bool = True):
        """
        Class which allows the plotting of areas on maps.

        :param data: A path to a geopandas geodataframe, or a geopandas GeoDataFrame. The geometry should contain polygons.
        :param popup: What columns to display in the popup (when clicking in the area)
        :param color: A background color for the areas
        :param stroke: Whether to include a border for each area or not
        """

        super().__init__(data, popup)
        self.color = color
        self.stroke = stroke

    def add_to(self, folium_map: TrackMap) -> TrackMap:
        """
        Add the areas to a TrackMap object

        :param folium_map: The map to add the objects to
        :return: The updated map
        """
        if self.popup:
            indexnames = self.data.index.names

        for index, r in self.data.iterrows():
            sim_geo = gpd.GeoSeries(r['geometry']).simplify(tolerance=0.00001)
            geo_j = sim_geo.to_json()
            geo_j = folium.GeoJson(data=geo_j,
                                   style_function=lambda x: {'fillColor': self.color,
                                                             'stroke': self.stroke})

            if self.popup:
                if not isinstance(index, tuple):
                    index = (index,)
                popupname = '<br>'.join([': '.join([str(i), str(j)]) for i, j in list(zip(indexnames, index))])

                folium.Popup(popupname).add_to(geo_j)
            folium_map.add_child(geo_j)
        return folium_map


def plottable(data: Union[gpd.GeoDataFrame, pd.DataFrame], popup=None, *args, **kwargs) -> PlotObject:
    """
    Infer the type of data to be plotted and make sure it can be added to a TrackMap

    :param data: The data that needs to be plotted
    :param popup: The columns that define the data
    :return: The data, transformed as a plottable object
    """
    if isinstance(data, gpd.GeoDataFrame):
        firstentry = data.geometry.values[0]
        if isinstance(firstentry, polygon.Polygon):
            return PlottingAreas(data, popup, *args, **kwargs)
        elif isinstance(firstentry, linestring.LineString):
            return PlottingLineStrings(data, popup, *args, **kwargs)
        elif isinstance(firstentry, point.Point):
            return PlottingPoints(data, popup, *args, **kwargs)
        else:
            NotImplementedError(f'GeoDataFrame with entries of type {type(firstentry)} not supported yet')
    elif isinstance(data, pd.DataFrame):  # Whenever data is a dataframe, it is probably points
        logger.info('Interpreting data as dataframe')
        return PlottingPoints(data, popup, *args, **kwargs)
