import pandas as pd
import folium
from shapely.geometry import point
import geopandas as gpd
from shapely import wkt
from typing import List, Optional, Dict, Tuple
from pathlib import Path
from urllib.parse import quote
from ..utils.common import read_config
from abc import ABC, abstractmethod

config = read_config()


class PlotObject(ABC):
    """
    A parent class for every object that can be plotted on a SpoorKaart
    """

    @abstractmethod
    def add_to(self, m) -> None:
        """
        A base function that should be overwritten with logic for every plottable object.
        :param m: A SpoorKaart object, to which this element should be added.
        :return: None
        """
        raise NotImplementedError('This needs to be set in implementation classes')

    def _convert_pandas_to_geopandas(self, df):
        # If this is a pandas dataframe with Rijksdriehoek in it, convert it to GPS
        first_coord = df.geometry.values[0].split('(')[1].split(' ')[0]
        if float(first_coord) > 180:
            expected_crs = 'EPSG:28992'
        else:
            expected_crs = 'EPSG:4326'
        return (
            df
                .assign(geometry=lambda d: d.geometry.apply(wkt.loads))
                .pipe(gpd.GeoDataFrame, geometry='geometry', crs=expected_crs)
                .assign(geometry=lambda d: d.geometry.to_crs('EPSG:4326'))
        )


class SpoorKaart(folium.Map):
    """
    Plotting functionality based on folium maps, designed for plotting objects on the Dutch railways.
    This object is designed to work as a context manager, where every element can be added to the SpoorKaart while it
    is opened.
    """

    def __init__(self, objects: List[PlotObject] = [],
                 save_name: Optional[Path] = None,
                 makesmaller: bool = False, **kwargs):
        """
        Set up a SpoorKaart object

        :param objects: A list of plottable objects that can be pre-defined outside the context manager of the
        spoorkaart
        :param save_name: An Optional Path where the final .html file could be written to
        :param makesmaller: A boolean for decreasing the size of the final plot. Designed for Databricks Notebooks
        :return: A SpoorKaart object
        """
        self.makesmaller = makesmaller
        super().__init__(location=[52, 5], zoom_start=8, max_zoom=30, max_native_zoom=30, tiles=None, **kwargs)
        self.save_name = save_name
        self._add_luchtfoto()

        for obj in objects:
            assert issubclass(type(obj), PlotObject), f'Unable to plot {obj}, not defined as plottable object'
            obj.add_to(self)

    def _add_luchtfoto(self) -> None:
        """
        Add the most recent ProRail luchtfoto to the map.

        :return: None
        """
        fg = folium.FeatureGroup(name=f"luchtfoto", max_zoom=30, max_native_zoom=30)
        folium.WmsTileLayer(url='https://luchtfoto.prorail.nl/erdas-iws/ogc/wms/Luchtfoto', layers='meest_recent',
                            transparent=True, overlay=False,
                            maxZoom=30, maxNativeZoom=30).add_to(fg)
        folium.TileLayer('openstreetmap', transparent=True, opacity=0.2).add_to(fg)
        self.add_child(fg)

    def __enter__(self):
        return self

    def _fix_zoom(self) -> None:
        """
        Set the zoom level so all of the plotted objects fit neatly within the default shown window.

        :return: None
        """
        bboxes = []

        for _, item in self._children.items():
            for _, subitem in item._children.items():
                # This is for plotted linestrings
                if isinstance(subitem.__dict__['_parent'], folium.features.Choropleth):
                    chloropleth = subitem.__dict__['_parent']
                    chloropleth_features = chloropleth.__dict__['geojson'].__dict__['data']['features']
                    for feature in chloropleth_features:
                        bboxes.append(
                            feature['bbox'][::-1])  # Reverse lat and long ordering here
                try:
                    # This is for plotted markers
                    bboxes.append(
                        subitem.__dict__['data']['features'][0]['bbox'][::-1])  # Reverse lat and long ordering here
                except:
                    pass
            try:
                bboxes.append(item.location * 2)  # Change order
            except:
                pass

        if bboxes:  # Fit only if there are some items to show
            bounds = [min(map(lambda x: x[i], bboxes)) if i < 2 else max(map(lambda x: x[i], bboxes)) for i in range(4)]
            self.fit_bounds([bounds[:2], bounds[2:]])

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        End the context manager, keeping track of any exceptions that may have occurred.
        :return: A SpoorKaart object
        """
        if exc_type is not None:
            raise exc_type(exc_val)
        self._fix_zoom()
        if self.save_name is not None:
            print(f'Saving as {self.save_name}')
            self.save(self.save_name)
        if self.makesmaller:
            self.superfigure = folium.Figure(1000, 400)
            self.add_to(self.superfigure)
            return self.superfigure
        else:
            return self


class PlottingDataFrame(pd.DataFrame, PlotObject):
    """
    Add functionalities to a Pandas DataFrame so it can be plotted in a nice manner.

    """

    def __init__(self, df, lat_column: str = 'lat', lon_column: str = 'lon', popup: List[str] = None,
                 colors: Dict[str, Dict[Tuple[float, float], str]] = None,
                 markertype: Optional[str] = None, marker_column: str = None, color_column: str = None,
                 rotation_column: str = None, radius_column: str = None, url_column: str=None):
        """
        Initialize a PlottingDataFrame.

        :param df: The Pandas DataFrame that should be plotted. GeoPandas dataframes are also partially supported
        :param lat_column: A column including latitudes
        :param lon_column: A column name including longitudes
        :param popup: A list of columns whose values should be mentioned when an object is clicked on
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

        # TODO: Make this a helper function? Also required for linestring dataframe parsing
        if 'geometry' in df.columns and isinstance(df, pd.DataFrame):
            df = self._convert_pandas_to_geopandas(df)
        super().__init__(df)
        self.attrs['lat'] = lat_column
        self.attrs['lon'] = lon_column
        if isinstance(df, gpd.GeoDataFrame):
            if isinstance(self.geometry.iloc[0], point.Point):
                self[self.attrs['lat']] = self.geometry.apply(lambda d: d.y)
                self[self.attrs['lon']] = self.geometry.apply(lambda d: d.x)
            else:
                NotImplementedError(f"Unimplemented geometry: {self.geometry.iloc[0]}")

        self.color_column = color_column
        if self.color_column is not None:
            self[self.color_column+"_factorized"] = pd.factorize(self[self.color_column])[0]

        # TODO: Automatically do this by looping through args?
        self.attrs['popup'] = popup
        self.attrs['markertype'] = markertype
        self.attrs['colors'] = colors
        self.attrs['marker'] = marker_column
        self.attrs['rotation'] = rotation_column
        self.attrs['radius'] = radius_column
        self.attrs['url_column'] = url_column

    def add_to(self, folium_map):
        for i, row in self.iterrows():
            location = list(row[[self.attrs['lat'], self.attrs['lon']]].values)
            if self.attrs['popup']:
                popup_text = ''
                for col in self.attrs['popup']:
                    if col == self.attrs['url_column']:
                        url = quote(row[col], safe='/:?=&') # Replaces characters unsuitable for URL's
                        popup_text = popup_text + f"{col}: <a href={url}>Hyperlink</a><br>",
                    else:
                        popup_text = popup_text + f'{col}: {row[col]}<br>'
            else:
                popup_text = None

            if self.attrs['rotation'] is not None:
                rotation = int(row[self.attrs['rotation']])
                marker = 'arrow-up'
            else:
                rotation = 0
                if self.attrs['marker'] is not None:
                    marker = row[self.attrs['marker']]
                elif self.attrs['markertype'] is not None:
                    marker = self.attrs['markertype']
                else:
                    marker = config['default_marker']

            if self.color_column is not None:
                colorset = ['purple', 'lightblue', 'darkgreen', 'blue', 'darkred', 'black',
                            'pink', 'cadetblue', 'lightgray', 'lightred', 'green',
                            'beige', 'darkblue', 'darkpurple', 'orange', 'lightgreen', 'red']
                marker_color = colorset[int(row[self.color_column+"_factorized"]) % len(colorset)]
            elif self.attrs['colors'] is not None:
                if isinstance(self.attrs['colors'], str):
                    marker_color = self.attrs['colors']
                else:
                    for column, colormap in self.attrs['colors'].items():
                        for bounds, color in colormap.items():
                            if min(bounds) <= row[column] <= max(bounds):
                                marker_color = color
            else:
                marker_color = config['default_color']

            if self.attrs['markertype'] == 'circle':
                if self.attrs['radius'] is not None:
                    radius = row[self.attrs['radius']]
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
    def _get_all_linestrings(self, file):
        # TODO Use the pandas to geopandas functionality?
        return (
            pd.read_csv(file, index_col=0)
            .assign(geometry=lambda d: d.geometry.apply(wkt.loads))
            .set_index(self.name_column)
            .pipe(gpd.GeoDataFrame, geometry='geometry', crs='EPSG:28992')
        )

    def __init__(self, file, name_column, subset=None, color='blue', topn=None, buffersize=3):
        self.subset = subset
        self.topn = topn
        self.color = color
        self.name_column = name_column
        self.buffersize = buffersize # In meters
        self.all_linestrings = self._get_all_linestrings(file)

    def add_sectie_to_map(self, geometry_data, folium_map):
        # Add lines
        folium.Choropleth(
            geometry_data['geometry'],
            line_weight=3,
            line_color=self.color,
        ).add_to(folium_map)

        # Add hover functionality.
        style_function = lambda x: {'fillColor': '#ffffff', 'color': '#000000', 'fillOpacity': 0.1, 'weight': 0.1}
        highlight_function = lambda x: {'fillColor': '#000000', 'color': '#000000', 'fillOpacity': 0.50, 'weight': 0.1}
        sectie_hover = folium.features.GeoJson(
            data=geometry_data.assign(geometry=lambda x: x.geometry.to_crs('EPSG:28992').buffer(self.buffersize)).reset_index(),
            style_function=style_function,
            control=False,
            highlight_function=highlight_function,
            tooltip=folium.features.GeoJsonTooltip(
                fields=[self.name_column],
                aliases=[self.name_column],
                style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
            )
        )
        folium_map.add_child(sectie_hover)
        folium_map.keep_in_front(sectie_hover)
        return folium_map

    def add_to(self, folium_map):
        if not self.subset:
            if self.topn:
                to_plot = self.all_linestrings.head(self.topn)
            else:
                to_plot = self.all_linestrings
            folium_map = self.add_sectie_to_map(to_plot, folium_map)
        else:
            for name in self.subset:
                try:
                    folium_map = self.add_sectie_to_map(self.all_linestrings.loc[[name], :], folium_map)
                except KeyError:
                    print(f'Failed to plot {name}')

        return folium_map
