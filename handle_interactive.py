import numpy as np
from child import Waveform_window
from utils import get_clicked_station, remove_nearby_points
from PyQt5.QtCore import Qt

def show_waveforms_on_dblclick(main_map_widget,stations_common,gcarc_list,data_asdf,sync_asdf,parent_self):
    # since only after clicked update, this function is called with right data_asdf,sync_asdf
    canvas = main_map_widget.canvas
    figure = canvas.fig
    ax = figure.axes[0]

    stations_obs = data_asdf.ds.waveforms.list()
    stations_syn = sync_asdf.ds.waveforms.list()
    obs_tag = data_asdf.ds.waveforms[stations_obs[0]].get_waveform_tags()[0]
    syn_tag = sync_asdf.ds.waveforms[stations_syn[0]].get_waveform_tags()[0]
    def pressed_connect(event):
        if(parent_self.checkBox_windows_normalize.isChecked()):
            # not implement yet
            return
        if(event.dblclick):
            gcarc=event.ydata
            gcarc_dists=(gcarc_list-gcarc)**2
            gcarc_dists_min_index=np.argmin(gcarc_dists)
            id=stations_common[gcarc_dists_min_index]
            head_id = id.replace(".", "_")
            obs_stream = data_asdf.ds.waveforms[id][obs_tag]
            syn_stream = sync_asdf.ds.waveforms[id][syn_tag]
            head_info = data_asdf.ds.auxiliary_data.Traveltimes[head_id].parameters
            waveform_window = Waveform_window(
                    id, obs_stream, syn_stream, head_info, parent=parent_self)
            waveform_window.show()

    parent_self.binder["dbclick"]=canvas.mpl_connect('button_press_event', pressed_connect)

def remove_trace_on_press_s(main_map_widget,length, stations_common,gcarc_list,not_used_traces,not_used_traces_marker,parent_self):
    # label on discarded traces and log it in not_used_traces
    canvas = main_map_widget.canvas
    figure = canvas.fig
    ax = figure.axes[0]

    def key_connect(event):
        if(parent_self.checkBox_windows_normalize.isChecked()):
            # not implement yet
            return
        gcarc=event.ydata
        gcarc_dists=(gcarc_list-gcarc)**2
        gcarc_dists_min_index=np.argmin(gcarc_dists)
        id=stations_common[gcarc_dists_min_index]
        if(event.key=="r"):
            # * remove traces
            # if id is already in not_used_traces
            if(id in not_used_traces):
                return
            # label 
            not_used_traces_marker.append(ax.plot(length, gcarc_list[gcarc_dists_min_index], color="blue", alpha=0.5, marker="x", markersize=10)[0])
            # add to not_used_traces
            not_used_traces.append(id)
            canvas.draw()
        elif(event.key=="b"):
            # * find the pos of id in the two lists
            pos=None
            for index,item in enumerate(not_used_traces):
                if(item==id):
                    pos=index
                    break
            print(pos,not_used_traces,id)
            if(pos==None):
                return
            else:
                not_used_traces.remove(not_used_traces[pos])
                # del Line2D
                theline=not_used_traces_marker[pos]
                theline.set_xdata([])
                theline.set_ydata([])
                canvas.draw()
                not_used_traces_marker.remove(not_used_traces_marker[pos])

    figure.canvas.mpl_connect('key_press_event', key_connect)
    return not_used_traces,not_used_traces_marker

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


def pick_window_by_drawing_lines(main_map_widget, status, binder, windows_to_pick, window_lines, parent_self):
    canvas = main_map_widget.canvas
    figure = canvas.fig
    ax = figure.axes[0]
    firsttime_run = False
    # if status is False, remove the binder
    if(not status):
        figure.canvas.mpl_disconnect(binder)
        # set binder as None
        binder = None
        # disable animation
        theline = None
        window_lines_start, window_lines_end = window_lines
        # print(windows_to_pick, window_lines_start)
        if(windows_to_pick[0] == "start"):
            theline = window_lines_start[windows_to_pick[1]]
        elif(windows_to_pick[0] == "end"):
            theline = window_lines_end[windows_to_pick[1]]
        theline.set_animated(False)
        canvas.draw()

        return None, window_lines

    # if window_lines is None, we should create them
    if(window_lines == None):
        firsttime_run = True
        window_lines_start = {
            "p": ax.plot([], [], color="blue", alpha=0.5, marker="o", markersize=5)[0],
            "s": ax.plot([], [], color="green", alpha=0.5, marker="o", markersize=5)[0],
            "pp": ax.plot([], [], color="y", alpha=0.5, marker="o", markersize=5)[0],
            "ss": ax.plot([], [], color="k", alpha=0.5, marker="o", markersize=5)[0],
            "sp": ax.plot([], [], color="r", alpha=0.5, marker="o", markersize=5)[0],
            "scs": ax.plot([], [], color="magenta", alpha=0.5, marker="o", markersize=5)[0],
            "rayleigh": ax.plot([], [], color="m", alpha=0.5, marker="o", markersize=5)[0],
            "love": ax.plot([], [], color="teal", alpha=0.5, marker="o", markersize=5)[0],
        }
        window_lines_end = {
            "p": ax.plot([], [], color="blue", alpha=0.5, marker="o", markersize=5)[0],
            "s": ax.plot([], [], color="green", alpha=0.5, marker="o", markersize=5)[0],
            "pp": ax.plot([], [], color="y", alpha=0.5, marker="o", markersize=5)[0],
            "ss": ax.plot([], [], color="k", alpha=0.5, marker="o", markersize=5)[0],
            "sp": ax.plot([], [], color="r", alpha=0.5, marker="o", markersize=5)[0],
            "scs": ax.plot([], [], color="magenta", alpha=0.5, marker="o", markersize=5)[0],
            "rayleigh": ax.plot([], [], color="m", alpha=0.5, marker="o", markersize=5)[0],
            "love": ax.plot([], [], color="teal", alpha=0.5, marker="o", markersize=5)[0],
        }
        window_lines = (window_lines_start, window_lines_end)
        # ax add lines
    else:
        window_lines_start, window_lines_end = window_lines

    # get the Line2D to be modified
    theline = None
    if(windows_to_pick[0] == "start"):
        theline = window_lines_start[windows_to_pick[1]]
    elif(windows_to_pick[0] == "end"):
        theline = window_lines_end[windows_to_pick[1]]

    # some functions
    def on_left_click(event):
        theline.set_animated(True)

        raw_xdata = theline.get_xdata()
        raw_ydata = theline.get_ydata()
        # raw_xdata.append(event.xdata)
        # raw_ydata.append(event.ydata)
        raw_xdata = np.append(raw_xdata, event.xdata)
        raw_ydata = np.append(raw_ydata, event.ydata)
        # when update the array, we should sort them
        raw_ydata_index = raw_ydata.argsort()
        raw_xdata = raw_xdata[raw_ydata_index]
        raw_ydata = raw_ydata[raw_ydata_index]

        theline.set_xdata(raw_xdata)
        theline.set_ydata(raw_ydata)

        canvas.draw()
        ax.draw_artist(theline)
        canvas.blit(ax.bbox)

    # bind event
    def pressed_connect(event):
        if(event.button == 1):
            if(event.inaxes != ax):
                return
            # add (event.xdata,event.ydata) to the list
            on_left_click(event)
        elif(event.button == 3):
            if(event.inaxes != ax):
                return
            # remove points in the list
            theline.set_animated(True)

            raw_xdata = theline.get_xdata()
            raw_ydata = theline.get_ydata()
            remove_result = remove_nearby_points(
                event.xdata, event.ydata, raw_xdata, raw_ydata)
            if(remove_result != None):
                raw_xdata, raw_ydata = remove_result
                # when update the array, we should sort them
                raw_ydata_index = raw_ydata.argsort()
                raw_xdata = raw_xdata[raw_ydata_index]
                raw_ydata = raw_ydata[raw_ydata_index]
                theline.set_xdata(raw_xdata)
                theline.set_ydata(raw_ydata)

            canvas.draw()
            ax.draw_artist(theline)
            canvas.blit(ax.bbox)

    binder = canvas.mpl_connect(
        'button_press_event', pressed_connect)

    if(firsttime_run):
        # for the first time, we should build a callback function to handle the issue about the zoom
        # when we are zooming, we should disable the picking (similar to click "select")
        def handle_lim_changed(axes):
            # only work when parent_self.pushButton_windows_select_isdefault==True
            if(not parent_self.pushButton_windows_select_isdefault):
                return
            # then do some hack
            parent_self.pushButton_windows_select_isdefault = False
            parent_self.pushButton_windows_select.setDefault(
                parent_self.pushButton_windows_select_isdefault)
            figure.canvas.mpl_disconnect(
                parent_self.pushButton_windows_select_bind)
            parent_self.pushButton_windows_select_bind = None
            parent_self._windows_ratiobuttons_not_change(True)

            theline.set_animated(False)
            canvas.draw()

        # if double click
        # def dbclick(event):
        #     if(event.dblclick):
        #         print(event.xdata,event.ydata)

        ax.callbacks.connect('xlim_changed', handle_lim_changed)
        ax.callbacks.connect('ylim_changed', handle_lim_changed)
        # parent_self.binder["dbclick"]=canvas.mpl_connect('button_press_event', dbclick)

    return binder, (window_lines_start, window_lines_end)

