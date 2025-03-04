from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import quote

import folium
import geopandas as gpd
import pandas as pd
from loguru import logger
from shapely.geometry import linestring, multilinestring, point, polygon

from ..utils.common import read_config

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
            TypeError("Unknown type for popup in linestrings")

        if isinstance(data, gpd.GeoDataFrame):
            self.data = data
        elif isinstance(data, str):
            self.data = gpd.read_file(data)
        else:
            raise TypeError(
                "Provide either a geopandas dataframe or a file location "
                "of a csv to show"
            )
        self.data = self.data.to_crs("EPSG:4326")
        if self.popup is not None:
            self.data = self.data.set_index(self.popup)

    @abstractmethod
    def add_to(self, m) -> PlotObject:
        """
        Base function to be overridden with logic for each plottable object.

        Parameters
        ----------
        m : TrackMap
            A TrackMap object to which this element should be added.

        Returns
        -------
        None
        """
        raise NotImplementedError(
            "This needs to be set in implementation classes"
        )


class TrackMap(folium.Map):
    """
    Plotting functionality based on folium maps, designed for plotting objects
    on the Dutch railways.
    Plottable objects are based on geopandas GeoDataFrames; with the function
    plottable they can be converted to
    a PlotObject that can be used for this class.
    Outputs are automatically zoomed in on what data is requested and include
    an aerial photograph of the Netherlands.
    Maps can be shown directly, or saved as .html files.
    """

    def __init__(
        self,
        objects: Union[PlotObject, List[PlotObject]] = [],
        add_aerial=True,
        **kwargs,
    ):
        """
        Set up a TrackMap object.

        Parameters
        ----------
        objects : object or list of objects, optional
            A single plottable object or a list of plottable objects that can
            be pre-defined outside the context manager of the TrackMap.
        add_aerial : bool, optional
            Whether to include the ProRail aerial photograph or not.

        Returns
        -------
        TrackMap
            A TrackMap object.
        """

        super().__init__(
            location=[52, 5],
            zoom_start=8,
            max_zoom=30,
            max_native_zoom=30,
            tiles=None,
            **kwargs,
        )
        if add_aerial:
            self._add_aerial_photograph()

        if not isinstance(objects, list):
            self.add(objects)
            return

        for obj in objects:
            assert issubclass(
                type(obj), PlotObject
            ), f"Unable to plot {obj}, not defined as plottable object"
            self.add(obj)

    def _add_aerial_photograph(self) -> None:
        """
        Add the most recent ProRail aerial photograph to the map.

        Returns
        -------
        None
        """
        fg = folium.FeatureGroup(
            name="aerial_photograph", max_zoom=30, max_native_zoom=30
        )
        folium.WmsTileLayer(
            url="https://luchtfoto.prorail.nl/erdas-iws/ogc/wms/Luchtfoto",
            layers="meest_recent",
            transparent=True,
            overlay=False,
            maxZoom=30,
            maxNativeZoom=30,
        ).add_to(fg)
        folium.TileLayer(
            "openstreetmap", transparent=True, opacity=0.2
        ).add_to(fg)
        self.add_child(fg)

    def _fix_zoom(self) -> None:
        """
        Set the zoom level so all the plotted objects fit neatly within
        the initial view of the output.

        Returns
        -------
        None
        """
        # Bboxes are stored as a List of [min_lat, min_lon, max_lat, max_lon]
        bboxes = []

        for _, item in self._children.items():
            if isinstance(item, folium.features.Choropleth):  # For linestrings
                bboxes.extend(
                    feature["bbox"][::-1]
                    for feature in item.geojson.data["features"]
                )
            if isinstance(
                item, folium.features.GeoJson
            ):  # For linestrings and areas
                bboxes.append(
                    [i for coords in item.get_bounds() for i in coords]
                )
            if isinstance(item, folium.map.Marker) and item.location:
                bboxes.append(
                    item.location * 2
                )  # Min and max bound are equal for points, hence the repeat

        if bboxes:  # Fit only if there are some items to show
            bounds = [
                (
                    min(map(lambda x: x[i], bboxes))
                    if i < 2
                    else max(map(lambda x: x[i], bboxes))
                )
                for i in range(4)
            ]
            # Convert into [[min_lat, min_lon], [max_lat, max_lon]]
            self.fit_bounds([bounds[:2], bounds[2:]])

    def add(self, plotobject) -> TrackMap:
        plotobject.add_to(self)
        return self

    def show(self, notebook: bool = False) -> Union[TrackMap, folium.Figure]:
        """
        Display the map at an optimal zoom level and size.

        Parameters
        ----------
        notebook : bool, optional
            If True, decreases the size of the final plot for use in notebooks.

        Returns
        -------
        self or folium.Figure
            Returns `self` if `notebook` is False, otherwise returns a
            `folium.Figure`.
        """
        self._fix_zoom()
        if notebook:
            # Add a folium map inside a folium figure. This is the easiest way
            # to change the figure size
            figure = folium.Figure(1000, 400)
            self.add_to(figure)
            return figure
        else:
            return self

    def save(self, save_name: Path) -> None:
        """
        Save the map to a specified directory.

        Parameters
        ----------
        save_name : Path
            The file path where the final .html file should be saved.

        Returns
        -------
        None
            The map is saved to the specified location.
        """

        self.show()
        super(TrackMap, self).save(save_name)


class PlottingPoints(PlotObject):
    """
    Add functionalities to a Pandas DataFrame,
    so it can be plotted in a nice manner.
    """

    def __init__(
        self,
        data,
        popup: Optional[Union[str, List[str]]] = None,
        lat_column: Optional[str] = "lat",
        lon_column: Optional[str] = "lon",
        colors: Optional[Union[str, Tuple[str, Dict[float, float]]]] = None,
        markertype: Optional[str] = None,
        marker_column: Optional[str] = None,
        color_column: Optional[str] = None,
        rotation_column: Optional[str] = None,
        radius_column: Optional[str] = None,
        url_column: Optional[str] = None,
    ):
        """
        Initialize a PlottingPoints object for plotting markers on a
        map of the Netherlands.

        Parameters
        ----------
        data : pandas.DataFrame or geopandas.GeoDataFrame
            The DataFrame containing data to be plotted. GeoPandas
            DataFrames are partially supported.
        lat_column : str, optional
            Column name containing latitudes. Not required if `data`
            is a GeoDataFrame.
        lon_column : str, optional
            Column name containing longitudes. Not required if `data`
            is a GeoDataFrame.
        popup : str or list of str, optional
            Column(s) whose values should be displayed when an
            object is clicked.
        colors : str or tuple, optional
            Specifies the column to base colors on and the values they
            should take.
        markertype : str, optional
            'circle' for circular markers, or an icon name from
            https://fontawesome.com/v4/icons/.
        marker_column : str, optional
            Column containing marker names to display.
        color_column : str, optional
            Column specifying marker colors.
        rotation_column : str, optional
            Column specifying rotation degrees (0-360).
        radius_column : str, optional
            Column specifying circle radius (if `markertype='circle'`).
        url_column : str, optional
            Column containing URLs displayed in the popup.

        """

        # Do some pre-processing for the cases the data is not a GeoDataFrame
        if isinstance(data, dict):
            data = pd.DataFrame(data)

        if isinstance(data, pd.DataFrame) and not isinstance(
            data, gpd.geodataframe.GeoDataFrame
        ):
            data = gpd.GeoDataFrame(
                data,
                geometry=gpd.points_from_xy(
                    data[lon_column], data[lat_column]
                ),
                crs="EPSG:4326",
            )
        if rotation_column:
            data[rotation_column + "_for_plotting"] = data[rotation_column]
        self.color_column = color_column
        if self.color_column is not None:
            data[self.color_column + "_factorized"] = pd.factorize(
                data[self.color_column]
            )[0]

        super().__init__(data, popup)

        if isinstance(data, gpd.GeoDataFrame):
            if isinstance(data.geometry.iloc[0], point.Point):
                data = data.to_crs("EPSG:4326")
                self.data["lat"] = data.geometry.apply(lambda d: d.y)
                self.data["lon"] = data.geometry.apply(lambda d: d.x)
            else:
                raise NotImplementedError(
                    f"Unimplemented geometry: {data.geometry.iloc[0]}"
                )

        # TODO: Automatically do this by looping through args?
        self.markertype = markertype
        self.colors = colors
        self.marker = marker_column
        self.rotation = rotation_column
        self.radius = radius_column
        self.url_column = url_column

    def _get_marker_color(self, row):
        if self.color_column is not None:
            colorset = [
                "purple",
                "lightblue",
                "darkgreen",
                "blue",
                "darkred",
                "black",
                "pink",
                "cadetblue",
                "lightgray",
                "lightred",
                "green",
                "beige",
                "darkblue",
                "darkpurple",
                "orange",
                "lightgreen",
                "red",
            ]
            return colorset[
                int(row[self.color_column + "_factorized"]) % len(colorset)
            ]

        if self.colors is None:
            return config["default_color"]

        if isinstance(self.colors, str):
            return self.colors

        column, colormap = self.colors
        for bounds, color in colormap.items():
            if min(bounds) <= row[column] < max(bounds):
                return color

    def _get_popup_text(self, i, row):
        if isinstance(i, tuple):
            indexnames = i
        else:
            indexnames = (i,)
        if self.popup:
            popup_text = ""
            for indexvalue, col in zip(indexnames, self.popup):
                if col == self.url_column:
                    url = quote(
                        row[col], safe="/:?=&"
                    )  # Replaces characters unsuitable for URL's
                    popup_text = (
                        popup_text + f"{col}: <a href={url}>Hyperlink</a><br>",
                    )
                else:
                    popup_text = popup_text + f"{col}: {indexvalue}<br>"
            return popup_text
        else:
            return None

    def add_to(self, folium_map) -> folium.Map:
        for i, row in self.data.iterrows():

            location = row.geometry.y, row.geometry.x

            if self.rotation is not None:
                rotation = int(row[self.rotation + "_for_plotting"])
                marker = "arrow-up"
            else:
                rotation = 0

                if self.marker is not None:
                    marker = row[self.marker]
                elif self.markertype is not None:
                    marker = self.markertype
                else:
                    marker = config["default_marker"]

            if self.markertype == "circle":
                if self.radius is not None:
                    radius = row[self.radius]
                else:
                    radius = config["default_radius"]
                folium.Circle(
                    radius=radius,
                    location=location,
                    popup=self._get_popup_text(i, row),
                    color=self._get_marker_color(row),
                    fill=False,
                ).add_to(folium_map)
            else:
                folium.Marker(
                    location,
                    popup=self._get_popup_text(i, row),
                    icon=folium.Icon(
                        color=self._get_marker_color(row),
                        prefix="fa",
                        icon=marker,
                        angle=rotation,
                    ),
                ).add_to(folium_map)
        return folium_map


class PlottingLineStrings(PlotObject):
    """
    An object that can be plotted on a TrackMap.
    This is based on a geopandas dataframe or a file with every row
    indicating an item to show.

    """

    def __init__(
        self,
        data: Union[gpd.GeoDataFrame, str],
        popup: Optional[Union[str, List[str]]] = None,
        color: str = "blue",
        buffersize: int = 3,
    ):
        """
        Initialize a PlottingLineStrings object.

        Parameters
        ----------
        data : geopandas.GeoDataFrame or str
            A GeoPandas DataFrame or a file path to a CSV file.
        popup : str or list of str, optional
            Column(s) whose values are displayed when hovering over
            a LineString.
        color : str, optional
            Color in which the LineStrings should be displayed on the map.
        buffersize : float, optional
            Size of the buffer around the LineStrings on the map.
        """

        data = data.copy()
        if color not in data.columns:
            self.color = color
        else:
            self.color_by_column = "color_by_column"
            assert (
                self.color_by_column not in data.columns
            ), f"Column name {self.color_by_column} already exists in data;"
            "please rename"

            data[self.color_by_column] = data[color]
            popup = (
                [color] + popup if isinstance(popup, list) else [color, popup]
            )
        self.buffersize = buffersize  # In meters

        super().__init__(data, popup)

    def _make_tooltip(self):
        return folium.features.GeoJsonTooltip(
            fields=self.popup,
            aliases=self.popup,
            style="background-color: white; color: #333333; "
            "font-family: arial; font-size: 12px; padding: 10px;",
        )

    def add_to(self, folium_map: TrackMap) -> TrackMap:
        """
        Add LineStrings to a TrackMap object.

        Parameters
        ----------
        folium_map : folium.Map
            The map to which the LineStrings should be added.

        Returns
        -------
        folium.Map
            The updated map with the added LineStrings.
        """
        if "color_by_column" in self.data.columns:
            colors = [
                "black",
                "pink",
                "darkblue",
                "darkred",
                "gray",
                "green",
                "lightblue",
                "darkgreen",
                "lightgray",
                "lightgreen",
                "orange",
                "purple",
                "red",
                "beige",
            ]

            if self.data["color_by_column"].nunique() > len(colors):
                logger.warning(
                    "More groups than colors, some groups will "
                    "have the same color"
                )
                if self.data["color_by_column"].nunique() > len(colors) * 100:
                    raise ValueError(
                        f"Too many groups to color by; reduce the number of "
                        f"elements in the {self.color} column "
                        f"below {len(colors) * 100}"
                    )

            if len(
                self.data.loc[lambda d: d["color_by_column"].isin(colors)]
            ) < len(self.data):
                self.data["color_by_column"] = self.data[
                    "color_by_column"
                ].map(
                    dict(
                        zip(
                            self.data["color_by_column"].unique(), colors * 100
                        )
                    )
                )

            for color, group in self.data.reset_index().groupby(
                "color_by_column"
            ):
                to_plot = PlottingLineStrings(
                    group.drop(["color_by_column"], axis=1),
                    popup=self.popup,
                    color=color,
                    buffersize=self.buffersize,
                )
                to_plot.add_to(folium_map)
            return folium_map

        folium.Choropleth(
            self.data["geometry"],
            line_weight=3,
            line_color=self.color,
        ).add_to(folium_map)

        def style_function(_) -> Dict:
            return {
                "fillColor": "#000000",
                "color": "#000000",
                "fillOpacity": 0.50,
                "weight": 0.1,
            }

        def highlight_function(_) -> Dict:
            return {
                "fillColor": "#000000",
                "color": "#000000",
                "fillOpacity": 0.50,
                "weight": 0.1,
            }

        if self.popup:
            tooltip = self._make_tooltip()
        else:
            tooltip = None

        sectie_hover = folium.features.GeoJson(
            data=self.data.assign(
                geometry=lambda x: x.geometry.to_crs("EPSG:28992").buffer(
                    self.buffersize
                )
            ).reset_index(),
            style_function=style_function,
            control=False,
            highlight_function=highlight_function,
            tooltip=tooltip,
        )
        folium_map.add_child(sectie_hover)
        folium_map.keep_in_front(sectie_hover)
        return folium_map


class PlottingAreas(PlotObject):
    """
    An object that can be plotted on a TrackMap. This is based on a geopandas
    dataframe or a file with every row
    indicating an item to show.

    """

    def __init__(
        self,
        data: Union[gpd.GeoDataFrame, str],
        popup: Optional[Union[str, List[str]]] = None,
        color: str = "orange",
        stroke: bool = True,
    ):
        """
        Class for plotting areas on maps.

        Parameters
        ----------
        data : str or geopandas.GeoDataFrame
            A file path to a GeoPandas GeoDataFrame or a GeoDataFrame itself.
            The geometry should contain polygons.
        popup : str or list of str, optional
            Column(s) to display in the popup when clicking on an area.
        color : str, optional
            Background color for the areas.
        stroke : bool, optional
            Whether to include a border for each area.
        """

        super().__init__(data, popup)
        self.color = color
        self.stroke = stroke

    def add_to(self, folium_map: TrackMap) -> TrackMap:
        """
        Add areas to a TrackMap object.

        Parameters
        ----------
        folium_map : folium.Map
            The map to which the areas should be added.

        Returns
        -------
        folium.Map
            The updated map with the added areas.
        """

        if self.popup:
            indexnames = self.data.index.names

        for index, r in self.data.iterrows():
            sim_geo = gpd.GeoSeries(r["geometry"]).simplify(tolerance=0.00001)
            geo_j_str = sim_geo.to_json()
            geo_j = folium.GeoJson(
                data=geo_j_str,
                style_function=lambda x: {
                    "fillColor": self.color,
                    "stroke": self.stroke,
                },
            )

            if self.popup:
                if not isinstance(index, tuple):
                    index = (index,)
                popupname = "<br>".join(
                    [
                        ": ".join([str(i), str(j)])
                        for i, j in list(zip(indexnames, index))
                    ]
                )

                folium.Popup(popupname).add_to(geo_j)
            folium_map.add_child(geo_j)
        return folium_map


def plottable(
    data: Union[gpd.GeoDataFrame, pd.DataFrame, PlotObject],
    popup=None,
    *args,
    **kwargs,
) -> PlotObject:
    """
    Infer the type of data to be plotted and ensure it can be added
    to a TrackMap.

    This function is idempotent, meaning it can be used on objects that
    are already plottable.

    Parameters
    ----------
    data : object
        The data that needs to be plotted.
    popup : str or list of str, optional
        The columns that define the data.

    Returns
    -------
    object
        The data transformed into a plottable object.
    """

    if isinstance(data, PlotObject):  # Objects that are already plottable
        return data
    if isinstance(data, gpd.GeoDataFrame):
        firstentry = data.geometry.values[0]
        if isinstance(firstentry, polygon.Polygon):
            return PlottingAreas(data, popup, *args, **kwargs)
        elif isinstance(firstentry, linestring.LineString) or isinstance(
            firstentry, multilinestring.MultiLineString
        ):
            return PlottingLineStrings(data, popup, *args, **kwargs)
        elif isinstance(firstentry, point.Point):
            return PlottingPoints(data, popup, *args, **kwargs)
        else:
            raise NotImplementedError(
                f"GeoDataFrame with entries of type {type(firstentry)} "
                "not supported yet"
            )
    elif isinstance(
        data, pd.DataFrame
    ):  # Whenever data is a dataframe, it is probably points
        logger.info("Interpreting data as dataframe")
        return PlottingPoints(data, popup, *args, **kwargs)
    raise TypeError(
        f"Data of type {type(data)} not supported. "
        "Please provide a geodataframe or a dataframe"
    )


def quick_plot(
    *args, notebook=False, **kwargs
) -> Union[TrackMap | folium.Figure]:
    """
    Quickly plot a list of objects on a map.

    This function is a wrapper around the TrackMap class.

    Parameters
    ----------
    *args : list of PlotObjects
        A list of PlotObjects to be plotted on the map.

    Returns
    -------
    TrackMap
        A TrackMap object with the plotted objects.
    """

    objects = []
    for arg in args:
        try:
            objects.append(plottable(arg, **kwargs))
        except TypeError:
            logger.info(
                f"Unable to plot {arg} with these arguments, "
                "plot these without arguments."
            )
            objects.append(plottable(**kwargs))
    return TrackMap(objects).show(notebook=notebook)
