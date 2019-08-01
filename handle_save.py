from scipy.interpolate import interp1d
from collections import namedtuple
import numpy as np

# ! a bug in save console window


def save_result(save_file, stations_common, gcarc_list, window_lines, not_used_traces, component):
    phases = ["p", "s", "pp", "ss", "sp", "scs", "rayleigh", "love"]
    start_lines = window_lines[0]
    end_lines = window_lines[1]

    # get info for each line (start_y,end_y,interp_func)
    line_info = {}
    info = namedtuple('info', ['start_y', 'end_y', "interp_func"])
    for phase in phases:
        # start
        xdata = start_lines[phase].get_xdata()
        ydata = start_lines[phase].get_ydata()
        len_data = len(xdata)
        if(len_data <= 1):
            line_info[phase+"_start"] = info(0,
                                             0, lambda gcarc: None)
        else:
            interp_func = interp1d(ydata, xdata)
            line_info[phase +
                      "_start"] = info(np.min(ydata), np.max(ydata), interp_func)
        # end
        xdata = end_lines[phase].get_xdata()
        ydata = end_lines[phase].get_ydata()
        len_data = len(xdata)
        if(len_data <= 1):
            line_info[phase+"_end"] = info(0,
                                           0, lambda gcarc: None)
        else:
            interp_func = interp1d(ydata, xdata)
            line_info[phase +
                      "_end"] = info(np.min(ydata), np.max(ydata), interp_func)

    # the save format:
    # id gcarc p_start p_end s_start s_end ...
    save_file.write(
        "# id gcarc component p_start p_end s_start s_end pp_start pp_end ss_start ss_end sp_start sp_end scs_start scs_end rayleigh_start rayleigh_end love_start love_end\n")
    for index, stname in enumerate(stations_common):
        if(not (stname in not_used_traces)):
            to_write = f"{stname} {gcarc_list[index]} {component} "
            for phase in phases:
                for thetype in ["_start", "_end"]:
                    key = phase+thetype
                    gcarc = gcarc_list[index]
                    theinfo = line_info[key]
                    if(gcarc < theinfo.start_y or gcarc > theinfo.end_y):
                        to_write += "None "
                    else:
                        thetime = theinfo.interp_func(gcarc)
                        to_write += f"{thetime} "
            to_write += "\n"
            save_file.write(to_write)
