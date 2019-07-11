from matplotlib.lines import Line2D
import numpy as np
from child import Waveform_window
from utils import get_clicked_station


def show_waveforms_on_right_click(main_map_widget, df, status, map_basemap, binder, data_asdf, sync_asdf, parent_self):
    canvas = main_map_widget.canvas
    figure = canvas.fig
    ax = figure.axes[0]
    # if status is False, remove the binder
    if(not status):
        figure.canvas.mpl_disconnect(binder)
        # set binder as None
        binder = None
        return None

    # info from ds
    lats = df.values[:, 1]
    lons = df.values[:, 2]
    ids = df.values[:, 0]

    # info from asdf
    stations_obs = data_asdf.ds.waveforms.list()
    stations_syn = sync_asdf.ds.waveforms.list()
    obs_tag = data_asdf.ds.waveforms[stations_obs[0]].get_waveform_tags()[0]
    syn_tag = sync_asdf.ds.waveforms[stations_syn[0]].get_waveform_tags()[0]

    # if status is True, set up a function to handle event
    def pressed_connect(event):
        if(event.button == 3):
            stlo, stla = map_basemap(event.xdata, event.ydata, inverse=True)
            nearest_point = get_clicked_station(stlo, stla, lons, lats, ids)
            if(nearest_point != None):
                # show up waveform_window
                id = nearest_point[0]
                head_id = id.replace(".", "_")
                obs_stream = data_asdf.ds.waveforms[id][obs_tag]
                syn_stream = sync_asdf.ds.waveforms[id][syn_tag]
                head_info = data_asdf.ds.auxiliary_data.Traveltimes[head_id].parameters

                waveform_window = Waveform_window(
                    id, obs_stream, syn_stream, head_info, parent=parent_self)
                waveform_window.show()

    # connect event
    binder = canvas.mpl_connect(
        'button_press_event', pressed_connect)
    return binder
