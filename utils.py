import numpy as np


def get_clicked_station(stlo, stla, lons, lats, ids):
    """
    get the nearest station
    """
    dists = (lats-stla)**2+(lons-stlo)**2
    min_dist = np.min(dists)
    if(min_dist > 0.8):
        return None
    else:
        min_pos = np.argmin(dists)
        return (ids[min_pos], lons[min_pos], lats[min_pos])


def remove_nearby_points(x, y, xall, yall):
    # get distance array
    distances = np.sqrt((x-np.array(xall))**2+(y-np.array(yall))**2)
    min_distance = np.min(distances)
    if(min_distance > 10.0):
        return None
    else:
        min_pos = distances == min_distance
        # xall.remove(xall[min_pos])
        # yall.remove(yall[min_pos])
        xall = xall[~ min_pos]
        yall = yall[~ min_pos]
        return xall, yall
