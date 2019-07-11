from PyQt5.QtWidgets import QDialog
from ui_waveform import Ui_waveforms
import numpy as np


class Waveform_window(QDialog, Ui_waveforms):
    def __init__(self, id, obs_stream, syn_stream, head_info, parent=None):
        super(Waveform_window, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(id)

        self.id = id
        self.obs_stream = obs_stream
        self.syn_stream = syn_stream
        self.head_info = head_info

        self.bind_vue()
        self.bind_buttons()

        # plot waveforms when entering
        self.plot_waveforms()

    # * ===========================================================
    # * bind vue
    def bind_vue(self):
        # update network and station
        network, station = self.id.split(".")
        self.label_network.setText(network)
        self.label_station.setText(station)
        # update labels for the sliders
        self.horizontalSlider_length.valueChanged.connect(
            self._horizontalSlider_length_valueChanged)
        self.horizontalSlider_per_lap.valueChanged.connect(
            self._horizontalSlider_per_lap_valueChanged)
        # update wlen
        sampling_rate = self.obs_stream[0].stats.sampling_rate
        # we set wlen as 100 times sampling_rate (maybe a bug in obspy)
        self.lineEdit_wlen.setText(f"{sampling_rate:.2f}")

        # if comobox_type is spectrogram, we will only data or syn
        self.checkBox_show_data.stateChanged.connect(
            self._checkBox_show_data_stateChanged)
        self.checkBox_show_sync.stateChanged.connect(
            self._checkBox_show_sync_stateChanged)
        self.comboBox_type.currentIndexChanged.connect(
            self._comboBox_type_currentIndexChanged)

    def _horizontalSlider_length_valueChanged(self):
        slider_value = self.horizontalSlider_length.value()
        if(slider_value % 100 != 0):
            slider_value = round(slider_value, -2)
            self.horizontalSlider_length.setValue(slider_value)
        self.label_length.setText(f"Length({slider_value}s)")

    def _horizontalSlider_per_lap_valueChanged(self):
        slider_value = self.horizontalSlider_per_lap.value()
        self.label_per_lap.setText(f"per_lap({slider_value/100:.2f})")

    def _checkBox_show_data_stateChanged(self):
        thetype = self.comboBox_type.currentText()
        if(thetype == "waveform"):
            pass
        else:
            if(self.checkBox_show_data.isChecked()):
                self.checkBox_show_sync.setChecked(False)
            else:
                self.checkBox_show_sync.setChecked(True)

    def _checkBox_show_sync_stateChanged(self):
        thetype = self.comboBox_type.currentText()
        if(thetype == "waveform"):
            pass
        else:
            if(self.checkBox_show_sync.isChecked()):
                self.checkBox_show_data.setChecked(False)
            else:
                self.checkBox_show_data.setChecked(True)

    def _comboBox_type_currentIndexChanged(self):
        if(self.comboBox_type.currentText() == "spectrogram"):
            if(self.checkBox_show_sync.isChecked() and self.checkBox_show_data.isChecked()):
                self.checkBox_show_data.setChecked(True)
                self.checkBox_show_sync.setChecked(False)
    # * ===========================================================

    # * ===========================================================
    # * bind buttons
    def bind_buttons(self):
        self.pushButton_update.clicked.connect(self._pushButton_update_clicked)
        self.pushButton_change_type.clicked.connect(
            self._pushButton_change_type_clicked)

    def _pushButton_update_clicked(self):
        if(self.comboBox_type.currentText() == "waveform"):
            self.plot_waveforms()
        elif(self.comboBox_type.currentText() == "spectrogram"):
            self.plot_spectrogram()

    def _pushButton_change_type_clicked(self):
        if(self.comboBox_type.currentText() == "waveform"):
            self.comboBox_type.setCurrentText("spectrogram")
        elif(self.comboBox_type.currentText() == "spectrogram"):
            self.comboBox_type.setCurrentText("waveform")
        self._pushButton_update_clicked()
    # * ===========================================================
    # * plot waveforms

    def plot_waveforms(self):
        canvas = self.widget_plot.canvas
        figure = canvas.fig
        figure.clf()
        ax_z = figure.add_subplot(311)
        ax_r = figure.add_subplot(312, sharex=ax_z)
        ax_t = figure.add_subplot(313, sharex=ax_z)

        # get some info from head_info and ui
        length = self.horizontalSlider_length.value()
        plot_sync = self.checkBox_show_sync.isChecked()
        plot_data = self.checkBox_show_data.isChecked()

        obs_stream = self.obs_stream.copy()
        syn_stream = self.syn_stream.copy()
        # * we don't need to normalize anything.
        # * each time we plot something, we should make an copy

        # * z component
        obs_z = obs_stream[2]
        syn_z = syn_stream[2]
        # trim
        obs_z.trim(obs_z.stats.starttime, obs_z.stats.starttime+length)
        syn_z.trim(syn_z.stats.starttime, syn_z.stats.starttime+length)
        x_obs_z = np.linspace(0, obs_z.stats.endtime -
                              obs_z.stats.starttime, obs_z.stats.npts)
        x_syn_z = np.linspace(0, syn_z.stats.endtime -
                              syn_z.stats.starttime, syn_z.stats.npts)
        y_obs_z = obs_z.data
        y_syn_z = syn_z.data
        if(plot_data):
            ax_z.plot(x_obs_z, y_obs_z, color="k")
        if(plot_sync):
            ax_z.plot(x_syn_z, y_syn_z, color="r")

        # * r component
        obs_r = obs_stream[0]
        syn_r = syn_stream[0]
        # trim
        obs_r.trim(obs_r.stats.starttime, obs_r.stats.starttime+length)
        syn_r.trim(syn_r.stats.starttime, syn_r.stats.starttime+length)
        x_obs_r = np.linspace(0, obs_r.stats.endtime -
                              obs_r.stats.starttime, obs_r.stats.npts)
        x_syn_r = np.linspace(0, syn_r.stats.endtime -
                              syn_r.stats.starttime, syn_r.stats.npts)
        y_obs_r = obs_r.data
        y_syn_r = syn_r.data
        if(plot_data):
            ax_r.plot(x_obs_r, y_obs_r, color="k")
        if(plot_sync):
            ax_r.plot(x_syn_r, y_syn_r, color="r")

        # * t component
        obs_t = obs_stream[1]
        syn_t = syn_stream[1]
        # trim
        obs_t.trim(obs_t.stats.starttime, obs_t.stats.starttime+length)
        syn_t.trim(syn_t.stats.starttime, syn_t.stats.starttime+length)
        x_obs_t = np.linspace(0, obs_t.stats.endtime -
                              obs_t.stats.starttime, obs_t.stats.npts)
        x_syn_t = np.linspace(0, syn_t.stats.endtime -
                              syn_t.stats.starttime, syn_t.stats.npts)
        y_obs_t = obs_t.data
        y_syn_t = syn_t.data
        if(plot_data):
            ax_t.plot(x_obs_t, y_obs_t, color="k")
        if(plot_sync):
            ax_t.plot(x_syn_t, y_syn_t, color="r")

        # * scatter arrival times
        self.scatter_travel_times("p", "blue", length, ax_z)
        self.scatter_travel_times("p", "blue", length, ax_r)
        self.scatter_travel_times("pp", "y", length, ax_z)
        self.scatter_travel_times("pp", "y", length, ax_r)
        self.scatter_travel_times("sp", "r", length, ax_z)
        self.scatter_travel_times("sp", "r", length, ax_r)
        self.scatter_travel_times("rayleigh", "c", length, ax_z)
        self.scatter_travel_times("rayleigh", "c", length, ax_r)
        self.scatter_travel_times("scs", "magenta", length, ax_t)
        self.scatter_travel_times("love", "teal", length, ax_t)
        self.scatter_travel_times("s", "green", length, ax_z)
        self.scatter_travel_times("s", "green", length, ax_r)
        self.scatter_travel_times("s", "green", length, ax_t)
        self.scatter_travel_times("ss", "k", length, ax_z)
        self.scatter_travel_times("ss", "k", length, ax_r)
        self.scatter_travel_times("ss", "k", length, ax_t)

        # show legend
        ax_z.legend(fontsize='xx-small')
        ax_r.legend(fontsize='xx-small')
        ax_t.legend(fontsize='xx-small')

        # * add some text
        ax_t.set_xlabel("time(s)")
        ax_z.set_ylabel("amplitude(m)")
        ax_r.set_ylabel("amplitude(m)")
        ax_t.set_ylabel("amplitude(m)")

        canvas.draw()

    def scatter_travel_times(self, phase_name, thecolor, length, ax):
        if(self.head_info[phase_name] and self.is_checked_phase(phase_name)):
            t_phase = self.head_info[phase_name]
            if(t_phase <= 1e-6):
                return
            if(t_phase <= length):
                ax.scatter(t_phase, 0, color=thecolor, label=phase_name, s=18)

    def is_checked_phase(self, phase_name):
        mapper = {
            "p": self.checkBox_p.isChecked(),
            "s": self.checkBox_s.isChecked(),
            "pp": self.checkBox_pp.isChecked(),
            "ss": self.checkBox_ss.isChecked(),
            "sp": self.checkBox_sp.isChecked(),
            "scs": self.checkBox_scs.isChecked(),
            "love": self.checkBox_love.isChecked(),
            "rayleigh": self.checkBox_rayleigh.isChecked(),
        }
        return mapper[phase_name]

    # * ===========================================================
    # * plot spectrogram
    def plot_spectrogram(self):
        canvas = self.widget_plot.canvas
        figure = canvas.fig
        figure.clf()
        ax_z = figure.add_subplot(311)
        ax_r = figure.add_subplot(312, sharex=ax_z)
        ax_t = figure.add_subplot(313, sharex=ax_z)
        # get some info from head_info and ui
        length = self.horizontalSlider_length.value()
        plot_sync = self.checkBox_show_sync.isChecked()
        plot_data = self.checkBox_show_data.isChecked()
        per_lap = float(self.horizontalSlider_per_lap.value()/100)
        wlen = float(self.lineEdit_wlen.text())
        log_scale = self.checkBox_log.isChecked()
        max_freq = 1.0/float(self.lineEdit_min_sec.text())
        min_freq = 1.0/float(self.lineEdit_max_sec.text())

        obs_stream = self.obs_stream.copy()
        syn_stream = self.syn_stream.copy()

        # * z component
        obs_z = obs_stream[2]
        syn_z = syn_stream[2]
        # trim
        obs_z.trim(obs_z.stats.starttime, obs_z.stats.starttime+length)
        syn_z.trim(syn_z.stats.starttime, syn_z.stats.starttime+length)
        if(plot_data):
            obs_z.spectrogram(axes=ax_z, per_lap=per_lap,
                              wlen=wlen, log=log_scale)
        if(plot_sync):
            syn_z.spectrogram(axes=ax_z, per_lap=per_lap,
                              wlen=wlen, log=log_scale)
        # scale
        ax_z.set_ylim(min_freq, max_freq)

        # * r component
        obs_r = obs_stream[0]
        syn_r = syn_stream[0]
        # trim
        obs_r.trim(obs_r.stats.starttime, obs_r.stats.starttime+length)
        syn_r.trim(syn_r.stats.starttime, syn_r.stats.starttime+length)
        if(plot_data):
            obs_r.spectrogram(axes=ax_r, per_lap=per_lap,
                              wlen=wlen, log=log_scale)
        if(plot_sync):
            syn_r.spectrogram(axes=ax_r, per_lap=per_lap,
                              wlen=wlen, log=log_scale)
        # scale
        ax_r.set_ylim(min_freq, max_freq)

        # * t component
        obs_t = obs_stream[1]
        syn_t = syn_stream[1]
        # trim
        obs_t.trim(obs_t.stats.starttime, obs_t.stats.starttime+length)
        syn_t.trim(syn_t.stats.starttime, syn_t.stats.starttime+length)
        if(plot_data):
            obs_t.spectrogram(axes=ax_t, per_lap=per_lap,
                              wlen=wlen, log=log_scale)
        if(plot_sync):
            syn_t.spectrogram(axes=ax_t, per_lap=per_lap,
                              wlen=wlen, log=log_scale)
        # scale
        ax_t.set_ylim(min_freq, max_freq)

        # * add some text
        ax_t.set_xlabel("time(s)")
        ax_z.set_ylabel("frequency(HZ)")
        ax_r.set_ylabel("frequency(HZ)")
        ax_t.set_ylabel("frequency(HZ)")

        canvas.draw()
