import numpy as np
import obspy

AMP_RATIO = 3


def plot_window_selector(obs_ds, syn_ds, canvas, azimuth_range, travel_times, length, normalize, show_sync, show_data, component, amp_ratio):
    # get plt elements
    canvas.fig.clf()
    ax = canvas.fig.add_subplot(111)
    # line_p_start = connect_DraggableLine(canvas.fig, ax, "p")
    stations_obs = obs_ds.waveforms.list()
    stations_syn = syn_ds.waveforms.list()
    stations_common = set(stations_obs) & set(stations_syn)
    stations_common = sorted(stations_common)
    stations_common = [stname for stname in stations_common if (
        azimuth_range[0] <= obs_ds.auxiliary_data.Traveltimes[stname.replace(".", "_")].parameters["azimuth"] <= azimuth_range[1])]

    # for the cases if there are only one trace
    if(len(stations_common) <= 1):
        return

    obs_tag = obs_ds.waveforms[stations_common[0]].get_waveform_tags()[0]
    syn_tag = syn_ds.waveforms[stations_common[0]].get_waveform_tags()[0]

    # discard traces where the difference of amplitude between obs and syn are not so large
    stations_common = discard_according_to_amplitude(
        stations_common, obs_ds, syn_ds, obs_tag, syn_tag)

    # get traces to plot
    if(component == "vertical"):
        obs_all = [obs_ds.waveforms[stname][obs_tag][2]
                   for stname in stations_common]
        syn_all = [syn_ds.waveforms[stname][syn_tag][2]
                   for stname in stations_common]
    elif(component == "radial"):
        obs_all = [obs_ds.waveforms[stname][obs_tag][0]
                   for stname in stations_common]
        syn_all = [syn_ds.waveforms[stname][syn_tag][0]
                   for stname in stations_common]
    elif(component == "tangential"):
        obs_all = [obs_ds.waveforms[stname][obs_tag][1]
                   for stname in stations_common]
        syn_all = [syn_ds.waveforms[stname][syn_tag][1]
                   for stname in stations_common]

    obs = obs_all
    syn = syn_all
    start_index = 0
    if(normalize == False):
        # collect gcarc information
        gcarc_list = [obs_ds.auxiliary_data.Traveltimes[stname.replace(".", "_")].parameters["gcarc"]
                      for stname in stations_common]
        gcarc_list = sorted(gcarc_list)
        standard_distance = np.mean(np.diff(gcarc_list))
        norm_obs = obspy.Stream()
        norm_syn = obspy.Stream()
        for index in range(len(obs)):
            obs_trace = obs[index].copy()
            syn_trace = syn[index].copy()
            # print(obs_trace, obs, index, splited_obs_all, figure_index)
            obs_trace.trim(obs_trace.stats.starttime,
                           obs_trace.stats.starttime+length)
            syn_trace.trim(syn_trace.stats.starttime,
                           syn_trace.stats.starttime+length)
            norm_all = obspy.Stream()+obs_trace+syn_trace
            norm_all.normalize(global_max=True)
            norm_obs += obs_trace
            norm_syn += syn_trace
        # norm_all = norm_obs+norm_syn
        # norm_all.normalize(global_max=True)

        # plot
        for index in range(len(obs)):
            obs_trace = list(norm_obs)[index]
            syn_trace = list(norm_syn)[index]
            x_obs = np.linspace(0, obs_trace.stats.endtime -
                                obs_trace.stats.starttime, obs_trace.stats.npts)
            x_syn = np.linspace(0, syn_trace.stats.endtime -
                                syn_trace.stats.starttime, syn_trace.stats.npts)
            stname = stations_common[index]
            gcarc = obs_ds.auxiliary_data.Traveltimes[stname.replace(
                ".", "_")].parameters["gcarc"]
            y_obs = 0.5*obs_trace.data*standard_distance*amp_ratio+gcarc
            y_syn = 0.5*syn_trace.data*standard_distance*amp_ratio+gcarc
            # print(index, np.max(y_obs), np.max(y_syn),
            #       standard_distance, np.max(obs_trace.data), np.max(syn_trace.data))
            if(show_data):
                ax.plot(x_obs, y_obs, color="k")
            if(show_sync):
                ax.plot(x_syn, y_syn, color="r")

            # if show_legend
            if(index == 0):
                show_legend = True
            else:
                show_legend = False

            if(component == "vertical" or component == "radial"):
                plot_travel_times("p", ax, travel_times, obs_ds,
                                  length, gcarc, stname, "blue", show_legend)
                plot_travel_times("pp", ax, travel_times, obs_ds,
                                  length, gcarc, stname, "y", show_legend)
                plot_travel_times("sp", ax, travel_times, obs_ds,
                                  length, gcarc, stname, "r", show_legend)
                plot_travel_times("rayleigh", ax, travel_times, obs_ds,
                                  length, gcarc, stname, "m", show_legend)
            if(component == "tangential"):
                plot_travel_times("scs", ax, travel_times, obs_ds,
                                  length, gcarc, stname, "magenta", show_legend)
                plot_travel_times("love", ax, travel_times, obs_ds,
                                  length, gcarc, stname, "teal", show_legend)
            plot_travel_times("s", ax, travel_times, obs_ds,
                              length, gcarc, stname, "green", show_legend)
            plot_travel_times("ss", ax, travel_times, obs_ds,
                              length, gcarc, stname, "black", show_legend)
        ax.legend()
    else:
        # we have to sort obs_all and syn_all
        syn_all_norm, obs_all_norm, stations_common = sort_stream(
            syn_all, obs_all, stations_common, obs_ds)
        # stations_common has been sorted in the first step
        obs = obs_all_norm
        syn = syn_all_norm
        # plot
        for index in range(len(obs)):
            obs_trace = obs[index].copy()
            syn_trace = syn[index].copy()
            obs_trace.trim(obs_trace.stats.starttime,
                           obs_trace.stats.starttime+length)
            syn_trace.trim(syn_trace.stats.starttime,
                           syn_trace.stats.starttime+length)
            # norm
            norm_stream = obspy.Stream()+obs_trace+syn_trace
            norm_stream.normalize(global_max=True)

            x_obs = np.linspace(0, obs_trace.stats.endtime -
                                obs_trace.stats.starttime, obs_trace.stats.npts)
            x_syn = np.linspace(0, syn_trace.stats.endtime -
                                syn_trace.stats.starttime, syn_trace.stats.npts)
            stname = stations_common[index]

            y_obs = 0.5*obs_trace.data*amp_ratio+start_index+index
            y_syn = 0.5*syn_trace.data*amp_ratio+start_index+index
            # plot lines
            if(show_data):
                ax.plot(x_obs, y_obs, color="k")
            if(show_sync):
                ax.plot(x_syn, y_syn, color="r")

            # if show_legend
            if(index == 0):
                show_legend = True
            else:
                show_legend = False
            gcarc = index  # the y coordinate
            if(component == "vertical" or component == "radial"):
                plot_travel_times("p", ax, travel_times, obs_ds,
                                  length, gcarc, stname, "blue", show_legend)
                plot_travel_times("pp", ax, travel_times, obs_ds,
                                  length, gcarc, stname, "y", show_legend)
                plot_travel_times("sp", ax, travel_times, obs_ds,
                                  length, gcarc, stname, "r", show_legend)
                plot_travel_times("rayleigh", ax, travel_times, obs_ds,
                                  length, gcarc, stname, "c", show_legend)
            if(component == "tangential"):
                plot_travel_times("scs", ax, travel_times, obs_ds,
                                  length, gcarc, stname, "magenta", show_legend)
                plot_travel_times("love", ax, travel_times, obs_ds,
                                  length, gcarc, stname, "teal", show_legend)
            plot_travel_times("s", ax, travel_times, obs_ds,
                              length, gcarc, stname, "green", show_legend)
            plot_travel_times("ss", ax, travel_times, obs_ds,
                              length, gcarc, stname, "black", show_legend)
        ax.legend()
    canvas.draw()

    # get returned info
    gcarc_list = [obs_ds.auxiliary_data.Traveltimes[stname.replace(".", "_")].parameters["gcarc"]
                  for stname in stations_common]

    return True, stations_common, gcarc_list


def plot_travel_times(phase_name, ax, travel_times, obs_ds, length, gcarc,  stname, thecolor, show_legend):
    # don't plot when the travel time is 0 (the None case)
    if(travel_times[phase_name]):
        t_phase = obs_ds.auxiliary_data.Traveltimes[stname.replace(
            ".", "_")].parameters[phase_name]
        if(t_phase <= 1e-6):
            return
        if(t_phase <= length):
            if(show_legend):
                ax.scatter(t_phase, gcarc, color=thecolor,
                           s=18, label=phase_name)
            else:
                ax.scatter(t_phase, gcarc, color=thecolor,
                           s=18, label='_nolegend_')


def array_split_same_size(thelist, thesize):
    thelist = list(thelist)
    result = []
    number_list = len(thelist)
    N_chunks = number_list//thesize+1
    if(number_list % thesize == 0):
        N_chunks -= 1
    for i in range(N_chunks):
        result.append(thelist[i*thesize:(i+1)*thesize])
    # print("@@", result)
    return result


def discard_according_to_amplitude(stations_common, obs_ds, syn_ds, obs_tag, syn_tag):
    result = []
    for stname in stations_common:
        obs = obs_ds.waveforms[stname][obs_tag]
        syn = syn_ds.waveforms[stname][syn_tag]
        status_r = (
            1/AMP_RATIO <= (np.abs(np.max(obs[0].data)))/(np.abs(np.max(syn[0].data))) <= AMP_RATIO)
        status_t = (
            1/AMP_RATIO <= (np.abs(np.max(obs[1].data)))/(np.abs(np.max(syn[1].data))) <= AMP_RATIO)
        status_z = (
            1/AMP_RATIO <= (np.abs(np.max(obs[2].data)))/(np.abs(np.max(syn[2].data))) <= AMP_RATIO)
        if(status_r and status_t and status_z):
            result.append(stname)
    return result


def sort_stream(syn_all, obs_all, stations_common, obs_ds):
    gcarc_list = [obs_ds.auxiliary_data.Traveltimes[stname.replace(".", "_")].parameters["gcarc"]
                  for stname in stations_common]
    result_syn = [trace for _, trace in sorted(zip(gcarc_list, syn_all))]
    result_obs = [trace for _, trace in sorted(zip(gcarc_list, obs_all))]
    result_names = [stname for _, stname in sorted(
        zip(gcarc_list, stations_common))]
    return result_syn, result_obs, result_names
