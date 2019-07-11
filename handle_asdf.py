import pyasdf
import obspy
from matplotlib.figure import Figure
import numpy as np


class ASDF_helper(object):
    """
    handle all operations on the asdf file.
    """

    def __init__(self, asdf_file_name):
        self.ds = None
        try:
            self.ds = pyasdf.ASDFDataSet(asdf_file_name, mode="r")
        except:
            pass

    def has_asdf(self):
        if(self.ds == None):
            return False
        else:
            return True

    def writecmtsolution(self, filename):
        event = self.ds.events[0]
        event.write(filename, format="CMTSOLUTION")

    def get_event(self):
        return self.ds.events[0]
