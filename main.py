import datetime
import io
import os

import pandas as pd
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QFileDialog, QMainWindow

import ui
from handle_asdf import ASDF_helper
from table_pandas import DataFrameModel
from waveform_plotter import plot_window_selector
from map_plotter import plot_map
from handle_interactive import show_waveforms_on_right_click, pick_window_by_drawing_lines,show_waveforms_on_dblclick,remove_trace_on_press_key
from handle_save import save_result


class MainApp(QMainWindow, ui.Ui_MainWindow):
    # TODO 
    # 2. finish the button remove
    def __init__(self):
        super(MainApp, self).__init__()
        # init all the widget from the ui file
        self.setupUi(self)
        self.initValues()
        self.bind_menu()
        self.bind_button_windows()
        self.bind_button_map()

        # set the focus policy to bind keyboard with matplotlib
        canvas = self.mplwidget_windows.canvas
        canvas.setFocusPolicy(Qt.ClickFocus)
        canvas.setFocus()
        # * vue like
        # update the label for adjusting the time length
        # self.horizontalSlider_windows_length.valueChanged.connect(
        #     lambda: self.label_windows_length.setText(f"Length({self.horizontalSlider_windows_length.value()}s)"))
        self.horizontalSlider_windows_length.valueChanged.connect(
            self._update_windows_slider)
        # azimuth width and the range
        self._update_azimuth_ranges()
        self.lineEdit_window_width.editingFinished.connect(
            self._update_azimuth_ranges)
        # beachball couldn't exist in Equidistant Cylindrical Projection
        self.comboBox_map_projection.currentIndexChanged.connect(self._comboBox_map_projection_currentIndexChanged)

    # * ===========================================================
    # * init values
    def initValues(self):
        # init values
        self.sync_filename = None
        self.data_filename = None
        self.dir_path = "~"
        self.azimuth_width = 15
        self.azimuth_ranges = []
        # table
        self.df=None
        df = pd.DataFrame(
            columns=["id", "stla", "stlo", "gcarc(°)", "azimuth"])
        model = DataFrameModel(df)
        self.tableView_welcome_content.setModel(model)
        self.tableView_welcome_content.horizontalHeader().setStretchLastSection(True)
        # asdf files
        self.sync_asdf = None
        self.data_asdf = None
        # map->select event button
        self.pushButton_map_select_stations_isdefault=False
        # bind map handler
        self.pushButton_map_select_stations_bind=None
        # map's Basemap
        self.map_basemap=None
        # select windows
        self.pushButton_windows_select_isdefault=False
        # if has plotted the window selector
        self.plotted_window_selector=False
        # bind window selector
        self.pushButton_windows_select_bind = None
        # window lines (a dict, its value is Line2D)
        self.window_lines=None
        # related to the saved windows
        self.saved_windows=None
        # last updated component
        self.last_updated_component=None
        # statins in the figure
        self.stations_common=None
        self.gcarc_list=None
        # binder
        self.binder={}
        # if the first time press update button
        self.first_time_update=True
        # store which trace is not used
        self.not_used_traces=[]
        self.not_used_traces_marker=[]
        # the filename to save the windows
        self.save_filename=None
        self.firsttime_save=True
    # * ===========================================================

    # * ===========================================================
    # * bind menus
    def bind_menu(self):
        self.actionWelcome.triggered.connect(self._actionWelcome_triggered)
        self.actionPick_Window.triggered.connect(
            self._actionPick_Window_triggered)
        self.actionMap.triggered.connect(self._actionMap_triggered)
        self.actionsync_asdf_file.triggered.connect(
            self._actionsync_asdf_file_triggered)
        self.actiondata_asdf_file.triggered.connect(
            self._actiondata_asdf_file_triggered)

    def _actionWelcome_triggered(self):
        self.stackedWidget.setCurrentIndex(0)

    def _actionPick_Window_triggered(self):
        self.stackedWidget.setCurrentIndex(1)

    def _actionMap_triggered(self):
        self.stackedWidget.setCurrentIndex(2)

    def _actionsync_asdf_file_triggered(self):
        self.sync_filename = QFileDialog.getOpenFileNames(
            None,
            "Select one file to open",
            self.dir_path,
            "ASDF file (*.h5)")[0]
        if(self.sync_filename == []):
            return
        self.sync_filename = self.sync_filename[0]
        self.dir_path = os.path.dirname(self.sync_filename)
        self.sync_asdf = ASDF_helper(self.sync_filename)
        if(not self.sync_asdf.has_asdf()):
            text_old = self.textBrowser_windows_log.toPlainText()
            self.textBrowser_windows_log.setText(text_old +
                                                 f"[ERROR] {str(datetime.datetime.now())} couldn't read {self.sync_filename}\n")
            self.textBrowser_welcome_log.setText(text_old +
                                                 f"[ERROR] {str(datetime.datetime.now())} couldn't read {self.sync_filename}\n")
            self.textBrowser_map_log.setText(text_old +
                                             f"[ERROR] {str(datetime.datetime.now())} couldn't read {self.sync_filename}\n")
        else:
            text_old = self.textBrowser_windows_log.toPlainText()
            self.textBrowser_windows_log.setText(text_old +
                                                 f"[INFO] {str(datetime.datetime.now())} having read sync file: {self.sync_filename}\n")
            self.textBrowser_welcome_log.setText(text_old +
                                                 f"[INFO] {str(datetime.datetime.now())} having read sync file: {self.sync_filename}\n")
            self.textBrowser_map_log.setText(text_old +
                                             f"[INFO] {str(datetime.datetime.now())} having read sync file: {self.sync_filename}\n")
            # if update table
            if(self.check_asdf_read_status()):
                self._update_table()
                self._update_event()

    def _actiondata_asdf_file_triggered(self):
        self.data_filename = QFileDialog.getOpenFileNames(
            None,
            "Select one file to open",
            self.dir_path,
            "ASDF file (*.h5)")[0]
        if(self.data_filename == []):
            return
        self.data_filename = self.data_filename[0]
        self.dir_path = os.path.dirname(self.data_filename)
        self.data_asdf = ASDF_helper(self.data_filename)
        if(not self.data_asdf.has_asdf()):
            text_old = self.textBrowser_windows_log.toPlainText()
            self.textBrowser_windows_log.setText(text_old +
                                                 f"[ERROR] {str(datetime.datetime.now())} couldn't read {self.data_filename}\n")
            self.textBrowser_welcome_log.setText(text_old +
                                                 f"[ERROR] {str(datetime.datetime.now())} couldn't read {self.data_filename}\n")
            self.textBrowser_map_log.setText(text_old +
                                             f"[ERROR] {str(datetime.datetime.now())} couldn't read {self.data_filename}\n")
        else:
            text_old = self.textBrowser_windows_log.toPlainText()
            self.textBrowser_windows_log.setText(text_old +
                                                 f"[INFO] {str(datetime.datetime.now())} having read data file: {self.data_filename}\n")
            self.textBrowser_welcome_log.setText(text_old +
                                                 f"[INFO] {str(datetime.datetime.now())} having read data file: {self.data_filename}\n")
            self.textBrowser_map_log.setText(text_old +
                                             f"[INFO] {str(datetime.datetime.now())} having read data file: {self.data_filename}\n")
            # if update table
            if(self.check_asdf_read_status()):
                self._update_table()
                self._update_event()
    # * ===========================================================

    # * ===========================================================
    # * bind button in the windows selection part
    def bind_button_windows(self):
        self.pushButton_windows_update.clicked.connect(
            self._pushButton_windows_update_clicked)
        self.pushButton_windows_select.clicked.connect(
            self._pushButton_windows_select_clicked)
        self.pushButton_windows_remove.clicked.connect(
            self._pushButton_windows_remove_clicked)
        self.pushButton_windows_save.clicked.connect(self._pushButton_windows_save_clicked)

    def _pushButton_windows_update_clicked(self):
        if(self.data_asdf == None or self.sync_asdf == None):
            return

        # if self.window_lines is not None, we should save lines and redraw them
        if(self.window_lines!=None):
            self.save_windows()

        obs_ds = self.data_asdf.ds
        syn_ds = self.sync_asdf.ds

        canvas = self.mplwidget_windows.canvas
        # canvas.setFocusPolicy( Qt.ClickFocus )
        # canvas.setFocus()
        azimuth_combobox = self.comboBox_windows_azimuth.currentText().split("-")
        azimuth_range = (
            float(azimuth_combobox[0]), float(azimuth_combobox[1]))
        travel_times = {
            "p": self.checkBox_p.isChecked(),
            "s": self.checkBox_s.isChecked(),
            "ss": self.checkBox_ss.isChecked(),
            "pp": self.checkBox_pp.isChecked(),
            "sp": self.checkBox_sp.isChecked(),
            "scs": self.checkBox_scs.isChecked(),
            "rayleigh": self.checkBox_rayleigh.isChecked(),
            "love": self.checkBox_love.isChecked()
        }
        length = self.horizontalSlider_windows_length.value()
        normalize = self.checkBox_windows_normalize.isChecked()
        show_sync = self.checkBox_windows_showsync.isChecked()
        show_data = self.checkBox_windows_showdata.isChecked()
        component = self.comboBox_windows_component.currentText()
        amp_ratio = float(self.comboBox_windows_amplitude.currentText())

        # plot the waveforms out
        plot_window_selector_result=plot_window_selector(obs_ds, syn_ds, canvas, azimuth_range, travel_times,
                             length, normalize, show_sync, show_data, component, amp_ratio)
        if(plot_window_selector_result!=None):
            self.plotted_window_selector, self.stations_common, self.gcarc_list=plot_window_selector_result

        # if self.window_lines is not None, we should save lines and redraw them
        if(self.window_lines!=None):
            self.load_windows(component,normalize,azimuth_range)

        self.last_updated_component=component
        self.last_updated_normalize=normalize
        self.last_updated_azimuth_range=azimuth_range

        # double click waveform plotter
        if(self.first_time_update):
            self.first_time_update=False
            self.handle_dbclick(canvas)
            self.handle_keyboard(canvas)

    def _pushButton_windows_select_clicked(self):
        if(self.data_asdf == None or self.sync_asdf == None):
            return
        if(not self.plotted_window_selector):
            return
        # check which ratiobutton has been selected
        windows_to_pick=self._get_windows_to_pick()
        # set default 
        self.pushButton_windows_select_isdefault = not self.pushButton_windows_select_isdefault
        self.pushButton_windows_select.setDefault(
            self.pushButton_windows_select_isdefault)
        # handle animation
        self.pushButton_windows_select_bind,self.window_lines = pick_window_by_drawing_lines(
                self.mplwidget_windows, self.pushButton_windows_select_isdefault, self.pushButton_windows_select_bind, windows_to_pick, self.window_lines,self)
        # if self.pushButton_windows_select_isdefault, we should not change the ratio buttons
        if(self.pushButton_windows_select_isdefault):
            self._windows_ratiobuttons_not_change(False)
        else:
            self._windows_ratiobuttons_not_change(True)

    def _pushButton_windows_remove_clicked(self):
        if(self.window_lines==None):
            return
        # clean self.window_lines[key] and update the figure
        start_or_end,phase=self._get_windows_to_pick()
        if(start_or_end=="start"):
            theline=self.window_lines[0][phase]
        elif(start_or_end=="end"):
            theline=self.window_lines[1][phase]
        theline.set_xdata([])
        theline.set_ydata([])
        self.mplwidget_windows.canvas.draw()

    def _pushButton_windows_save_clicked(self):
        if(self.window_lines==None):
            return
        # if it's the first time to save, we have to create a new/ select an existing file
        if(self.firsttime_save):
            self.save_filename = QFileDialog.getSaveFileName(
                None,
                "Select one file to open",
                self.dir_path,
                "text file (*.txt)")[0]
            if(not self.save_filename==''):
                with open(self.save_filename,"a") as f:
                    save_result(f, self.stations_common,
                                self.gcarc_list, self.window_lines, self.not_used_traces, self.last_updated_component)
            self.firsttime_save=False
            text_old = self.textBrowser_windows_log.toPlainText()
            self.textBrowser_windows_log.setText(text_old +
                                                 f"[INFO] {str(datetime.datetime.now())} save windows in {self.save_filename}\n")
            self.textBrowser_welcome_log.setText(text_old +
                                                 f"[INFO] {str(datetime.datetime.now())} save windows in {self.save_filename}\n")
            self.textBrowser_map_log.setText(text_old +
                                             f"[INFO] {str(datetime.datetime.now())} save windows in {self.save_filename}\n")
        else:
            with open(self.save_filename, "a") as f:
                save_result(f, self.stations_common,
                            self.gcarc_list, self.window_lines, self.not_used_traces, self.last_updated_component)
            text_old = self.textBrowser_windows_log.toPlainText()
            self.textBrowser_windows_log.setText(text_old +
                                                 f"[INFO] {str(datetime.datetime.now())} save windows in {self.save_filename}\n")
            self.textBrowser_welcome_log.setText(text_old +
                                                 f"[INFO] {str(datetime.datetime.now())} save windows in {self.save_filename}\n")
            self.textBrowser_map_log.setText(text_old +
                                             f"[INFO] {str(datetime.datetime.now())} save windows in {self.save_filename}\n")

    def _get_windows_to_pick(self):
        status_start_or_end={
            "start":self.radioButton_windows_start.isChecked(),
            "end":self.radioButton_windows_end.isChecked()
        }
        status_phase={
            "p":self.radioButton_windows_p.isChecked(),
            "s":self.radioButton_windows_s.isChecked(),
            "ss":self.radioButton_windows_ss.isChecked(),
            "pp":self.radioButton_windows_pp.isChecked(),
            "sp":self.radioButton_windows_sp.isChecked(),
            "scs":self.radioButton_windows_scs.isChecked(),
            "rayleigh":self.radioButton_windows_rayleigh.isChecked(),
            "love":self.radioButton_windows_love.isChecked()
        }
        start_or_end=None
        phase=None
        for key in status_start_or_end:
            if(status_start_or_end[key]):
                start_or_end=key
                break
        for key in status_phase:
            if(status_phase[key]):
                phase=key
                break
        return (start_or_end,phase)

    def _windows_ratiobuttons_not_change(self, status):
        self.radioButton_windows_end.setEnabled(status)
        self.radioButton_windows_love.setEnabled(status)
        self.radioButton_windows_p.setEnabled(status)
        self.radioButton_windows_pp.setEnabled(status)
        self.radioButton_windows_rayleigh.setEnabled(status)
        self.radioButton_windows_s.setEnabled(status)
        self.radioButton_windows_scs.setEnabled(status)
        self.radioButton_windows_sp.setEnabled(status)
        self.radioButton_windows_sp.setEnabled(status)
        self.radioButton_windows_ss.setEnabled(status)
        self.radioButton_windows_start.setEnabled(status)
    # * ===========================================================

    # * ===========================================================
    # * bind button in the map part
    def bind_button_map(self):
        self.pushButton_map_update_figure.clicked.connect(
            self._pushButton_map_update_figure_clicked)
        self.pushButton_map_select_stations.clicked.connect(self._pushButton_map_select_stations_clicked)

    def _pushButton_map_update_figure_clicked(self):
        if(self.data_asdf == None or self.sync_asdf == None):
            return
        projection = self.comboBox_map_projection.currentText()
        background = self.comboBox_map_background.currentText()
        beachball = self.checkBox_map_beachball.isChecked()

        canvas = self.widget_map.canvas
        df = self.df
        event = self.data_asdf.get_event()
        textBrowser_map_log = self.textBrowser_map_log
        self.map_basemap=plot_map(canvas, df, event, projection, background,
                 beachball,  textBrowser_map_log)

    def _pushButton_map_select_stations_clicked(self):
        self.pushButton_map_select_stations_isdefault=not self.pushButton_map_select_stations_isdefault
        self.pushButton_map_select_stations.setDefault(self.pushButton_map_select_stations_isdefault)
        # bind interactive
        main_map_widget=self.widget_map
        # there are possibility that df==None
        if(isinstance(self.df,type(None))):
            return
        df=self.df
        status=self.pushButton_map_select_stations_isdefault
        map_basemap=self.map_basemap
        data_asdf=self.data_asdf
        sync_asdf=self.sync_asdf
        # we have to set parent for the child window
        parent_self=self
        
        # only if map_basemap!=None
        if(map_basemap!=None):
            self.pushButton_map_select_stations_bind=show_waveforms_on_right_click(main_map_widget,df,status,map_basemap,self.pushButton_map_select_stations_bind,data_asdf,sync_asdf,parent_self)
    # * ===========================================================

    # * ===========================================================
    # * utils
    def check_asdf_read_status(self):
        if(self.sync_asdf == None or self.data_asdf == None):
            return False
        else:
            if(self.sync_asdf.has_asdf() or self.data_asdf.has_asdf()):
                return True
            else:
                return False

    def _update_table(self):
        df = pd.DataFrame(
            columns=["id", "stla", "stlo",  "gcarc(°)", "azimuth"])
        for index, key in enumerate(self.data_asdf.ds.auxiliary_data.Traveltimes.list()):
            value = self.data_asdf.ds.auxiliary_data.Traveltimes[key].parameters
            df.loc[index] = [key.replace(
                "_", "."), value["stla"], value["stlo"], value["gcarc"], value["azimuth"]]
        model = DataFrameModel(df)
        self.tableView_welcome_content.setModel(model)
        self.tableView_welcome_content.horizontalHeader().setStretchLastSection(True)
        self.df = df

    def _update_event(self):
        towrite = "CMTSOLUTION:\n"
        f = io.BytesIO(b"")
        self.data_asdf.writecmtsolution(f)
        self.textBrowser_welcome_event.setText(str(f.getvalue(), 'utf-8'))

    def _update_azimuth_ranges(self):
        # see if it's could be "inted"
        try:
            self.azimuth_width = int(self.lineEdit_window_width.text())
        except:
            self.azimuth_width = 360
        number_azimuth_ranges = int(360//self.azimuth_width)
        self.azimuth_ranges = []
        if(360 % self.azimuth_width == 0):
            for i in range(number_azimuth_ranges):
                self.azimuth_ranges.append(
                    f"{i*self.azimuth_width}-{(i+1)*self.azimuth_width}")
        else:
            for i in range(number_azimuth_ranges):
                self.azimuth_ranges.append(
                    f"{i*self.azimuth_width}-{(i+1)*self.azimuth_width}")
            self.azimuth_ranges.append(
                f"{number_azimuth_ranges*self.azimuth_width}-360")
        self.comboBox_windows_azimuth.clear()
        self.comboBox_windows_azimuth.addItems(self.azimuth_ranges)
        self.comboBox_windows_azimuth.update()

    def _update_windows_slider(self):
        slider_values = self.horizontalSlider_windows_length.value()
        if(slider_values % 100 != 0):
            slider_values = round(slider_values, -2)
            self.horizontalSlider_windows_length.setValue(slider_values)
        self.label_windows_length.setText(
            f"Length({slider_values}s)")

    def _comboBox_map_projection_currentIndexChanged(self):
        if(self.comboBox_map_projection.currentText()=="Equidistant Cylindrical Projection"):
            self.checkBox_map_beachball.setChecked(False)
            self.checkBox_map_beachball.setCheckable(False)
        else:
            self.checkBox_map_beachball.setCheckable(True)

    def handle_dbclick(self,canvas):
        # def dbclick(event):
        #     if(event.dblclick):
        #         print(event.xdata,event.ydata)
        # self.binder["dbclick"]=canvas.mpl_connect('button_press_event', dbclick)
        show_waveforms_on_dblclick(self.mplwidget_windows, self.stations_common,self.gcarc_list,self.data_asdf,self.sync_asdf,self)

    def handle_keyboard(self,canvas):
        # handle the event
        self.not_used_traces,self.not_used_traces_marker=remove_trace_on_press_key(self.mplwidget_windows, self.horizontalSlider_windows_length.value()  ,self.stations_common,self.gcarc_list,self.not_used_traces,self.not_used_traces_marker,self)
    # * ===========================================================

    # * ===========================================================
    # * windows related
    def save_windows(self):
        # a test shows the self.window_lines still get its data
        # print(self.window_lines[0]["p"].get_xdata())
        pass
    def load_windows(self,component,normalize,azimuth_range):
        # print(self.window_lines[0]["p"].get_xdata())
        # update only when the component is the same as the last updated one
        if(component!=self.last_updated_component or self.last_updated_normalize!=normalize or self.last_updated_azimuth_range!=azimuth_range):
            # clean self.window_lines
            self.window_lines=None
            self.not_used_traces=[]
            self.not_used_traces_marker=[]
            return
        canvas = self.mplwidget_windows.canvas
        figure = canvas.fig
        ax = figure.axes[0]

        # the color map
        map_color={
            "p":"blue",
            "s":"green",
            "pp":"y",
            "ss":"k",
            "sp":"r",
            "scs":"magenta",
            "rayleigh":"m",
            "love":"teal"
        }

        for key in self.window_lines[0]:
            theline=self.window_lines[0][key]
            # create a new line since artists couldn't be reused
            xdata=theline.get_xdata()
            ydata=theline.get_ydata()
            theline_new=ax.plot(xdata, ydata, color=map_color[key], alpha=0.5, marker="o", markersize=5)[0]
            # set as the new line
            self.window_lines[0][key]=ax.add_line(theline_new)
        for key in self.window_lines[1]:
            theline=self.window_lines[1][key]
            # create a new line since artists couldn't be reused
            xdata=theline.get_xdata()
            ydata=theline.get_ydata()
            theline_new=ax.plot(xdata, ydata, color=map_color[key], alpha=0.5, marker="o", markersize=5)[0]
            # set as the new line
            self.window_lines[1][key]=ax.add_line(theline_new)
        canvas.draw()
    # * ===========================================================
if __name__ == "__main__":
    from PyQt5 import QtWidgets
    import sys

    # * Create GUI application
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    window.show()
    app.exec_()
