import numpy as np

def get_clicked_station(stlo,stla,lons,lats,ids):
    """
    get the nearest station
    """
    dists = (lats-stla)**2+(lons-stlo)**2
    min_dist = np.min(dists)
    if(min_dist>0.8):
        return None
    else:
        min_pos = np.argmin(dists)
        return (ids[min_pos],lons[min_pos],lats[min_pos])