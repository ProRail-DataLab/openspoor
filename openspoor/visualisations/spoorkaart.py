import pandas as pd
import folium


class PlotObject:

    def add_to(self, m):
        raise NotImplementedError('This needs to be set in implementation classes')


class SpoorKaart(folium.Map):

    def __init__(self, objects=[], save_name=None, makesmaller=False, **kwargs):
        self.makesmaller = makesmaller
        super().__init__(location=[52, 5], zoom_start=8, max_zoom=30, max_native_zoom=30, tiles=None, **kwargs)
        self.save_name = save_name
        self._add_luchtfoto()

        for obj in objects:
            assert issubclass(type(obj), PlotObject), f'Unable to plot {obj}, not defined as plottable object'
            obj.add_to(self)

    def _add_luchtfoto(self):
        fg = folium.FeatureGroup(name=f"luchtfoto", max_zoom=30, max_native_zoom=30)
        folium.WmsTileLayer(url='https://luchtfoto.prorail.nl/erdas-iws/ogc/wms/Luchtfoto', layers='meest_recent',
                            transparent=True, overlay=False,
                            maxZoom=30, maxNativeZoom=30).add_to(fg)
        folium.TileLayer('openstreetmap', transparent=True, opacity=0.2).add_to(fg)
        self.add_child(fg)

    def __enter__(self):
        return self

    def add(self, obj):
        assert issubclass(type(obj), PlotObject), f'Unable to plot {obj}, not defined as plottable object'
        obj.add_to(self)

    def _fix_zoom(self):
        bboxes = []

        for _, item in self._children.items():
            for _, subitem in item._children.items():
                try:
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
        if exc_type is not None:
            raise exc_type(exc_val)
        self._fix_zoom()
        if self.save_name is not None:
            print(f'Saving as {self.save_name}')
            self.save(self.save_name)
        if not self.makesmaller:
            return self
        else:
            self.superfigure = folium.Figure(1000, 400)
            self.add_to(self.superfigure)
            return self.superfigure


# TODO: Support for hyperlinks?
class PlottingDataFrame(pd.DataFrame, PlotObject):
    def __init__(self, df, lat_column='lat', lon_column='lng', popup=None, markertype=None, colors=None,
                 marker_column=None, color_column=None, rotation_column=None, radius_column=None):
        super().__init__(df)
        # Set these to circumvent userwarnings
        self.popup = None
        self.markertype = None
        self.color_column = None
        self.colors = None
        self.marker_column = None
        self.rotation_column = None
        self.radius_column = None
        self._plot_settings(lat_column, lon_column, popup, markertype, colors, marker_column, color_column,
                            rotation_column, radius_column)

    def _plot_settings(self, lat_column='lat', lon_column='lng', popup=None, markertype=None, colors=None,
                       marker_column=None, color_column=None, rotation_column=None, radius_column=None):
        self.lat_column = lat_column
        self.lon_column = lon_column
        self.popup = popup
        # https://fontawesome.com/v4/icons/
        self.markertype = markertype
        if color_column is not None:
            self[color_column] = pd.factorize(self[color_column])[0]
        self.color_column = color_column
        self.colors = colors
        self.marker_column = marker_column
        self.rotation_column = rotation_column
        self.radius_column = radius_column

    def add_to(self, folium_map):
        for i, point in self.iterrows():
            location = list(point[[self.lat_column, self.lon_column]].values)
            if self.popup:
                popup_text = ''
                for col in self.popup:
                    if col == "batch_url":
                        url = point[col].replace(' ', '%20')
                        popup_text = popup_text + f"<a href={url}>Dashboard URL</a><br>",
                    else:
                        popup_text = popup_text + f'{col}: {point[col]}<br>'
            else:
                popup_text = None

            if self.rotation_column is not None:
                rotation = int(point[self.rotation_column])
                marker = 'arrow-up'
            else:
                rotation = 0
                if self.marker_column is not None:
                    marker = point[self.marker_column]
                elif self.markertype is not None:
                    marker = self.markertype
                else:
                    marker = 'info'

            if self.color_column is not None:
                colorset = ['purple', 'lightblue', 'darkgreen', 'blue', 'darkred', 'black',
                            'pink', 'cadetblue', 'lightgray', 'lightred', 'green',
                            'beige', 'darkblue', 'darkpurple', 'orange', 'lightgreen', 'red']
                marker_color = colorset[int(point[self.color_column]) % len(colorset)]
            elif self.colors is not None:
                if isinstance(self.colors, str):
                    marker_color = self.colors
                else:
                    for column, colormap in self.colors.items():
                        for bounds, color in colormap.items():
                            if min(bounds) <= point[column] <= max(bounds):
                                marker_color = color
            else:
                marker_color = 'blue'

            if self.markertype == 'circle':
                if self.radius_column is not None:
                    radius = point[self.radius_column]
                else:
                    radius = 2
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
