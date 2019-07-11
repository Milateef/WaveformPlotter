from mpl_toolkits.basemap import Basemap
import numpy as np
import datetime
from obspy.geodetics import degrees2kilometers
from obspy.imaging.beachball import beach
import copy
from utils import get_clicked_station

def plot_map(canvas, df, event, projection, background, beachball, textBrowser_map_log):
    figure = canvas.fig
    figure.clf()
    ax = figure.add_subplot(111)

    # * for different projection methods, we have different Basemap
    origin = event.preferred_origin() or event.origins[0]
    evla = origin.latitude
    evlo = origin.longitude
    evdp = origin.depth/1000

    # info from ds
    lats = df.values[:, 1]
    lons = df.values[:, 2]
    ids = df.values[:, 0]

    max_gcarc = np.max(df.values[:, 3])
    width = degrees2kilometers(max_gcarc)*1000
    if(projection == "Azimuthal Equidistant Projection"):
        # find the max gcarc, use it as the reference of the width
        m = Basemap(width=width*2, height=width*2, projection='aeqd',
                    lat_0=evla, lon_0=evlo, ax=ax, resolution="c")
        # draw parallels and meridians
        m.drawparallels(np.linspace(round(evla-max_gcarc, -1), round(evla+max_gcarc, -1),
                                    int((round(evla+max_gcarc, -1)-round(evla-max_gcarc, -1))//10)+1), labels=[False, True, True, False])
        m.drawmeridians(np.linspace(round(evlo-max_gcarc, -1), round(evlo+max_gcarc, -1),
                                    int((round(evlo+max_gcarc, -1)-round(evlo-max_gcarc, -1))//10)+1), labels=[True, False, False, True])
    elif(projection == "Mercator Projection"):
        # just don'y consider 180 line
        maxlat = np.max(lats)
        minlat = np.min(lats)
        maxlon = np.max(lons)
        minlon = np.min(lons)
        m = Basemap(projection='merc', llcrnrlat=minlat, urcrnrlat=maxlat,
                    llcrnrlon=minlon, urcrnrlon=maxlon, lat_ts=(maxlat+minlat)/2, resolution='c',ax=ax)
        # draw parallels and meridians
        m.drawparallels(np.linspace(round(minlat, -1), round(maxlat, -1),
                                    int((round(maxlat, -1)-round(minlat, -1))//10)+1), labels=[False, True, True, False])
        m.drawmeridians(np.linspace(round(minlon, -1), round(maxlon, -1),
                                    int((round(maxlon, -1)-round(minlon, -1))//10)+1), labels=[True, False, False, True])
    elif(projection=="Equidistant Cylindrical Projection"):
        # just don'y consider 180 line
        maxlat = np.max(lats)
        minlat = np.min(lats)
        maxlon = np.max(lons)
        minlon = np.min(lons)
        m = Basemap(projection='cyl', llcrnrlat=minlat, urcrnrlat=maxlat,
                    llcrnrlon=minlon, urcrnrlon=maxlon, lat_ts=(maxlat+minlat)/2, resolution='c',ax=ax)
        # draw parallels and meridians
        m.drawparallels(np.linspace(round(minlat, -1), round(maxlat, -1),
                                    int((round(maxlat, -1)-round(minlat, -1))//10)+1), labels=[False, True, True, False])
        m.drawmeridians(np.linspace(round(minlon, -1), round(maxlon, -1),
                                    int((round(maxlon, -1)-round(minlon, -1))//10)+1), labels=[True, False, False, True])
    

    if(background == "normal"):
        m.drawmapboundary(fill_color='aqua')
        m.drawcoastlines(linewidth=0.5)
        m.fillcontinents(color='coral', lake_color='aqua')

    if(beachball):
        # draw beach ball
        tensor = event.focal_mechanisms[0].moment_tensor.tensor
        moment_list = [tensor.m_rr, tensor.m_tt, tensor.m_pp,
                       tensor.m_rt, tensor.m_rp, tensor.m_tp]
        moment_list = copy.deepcopy(moment_list)
        x, y = m(evlo, evla)
        b = beach(moment_list, xy=(x, y), width=width/18)
        b.set_zorder(10)
        ax.add_collection(b)
    else:
        x, y = m(evlo, evla)
        m.plot(x, y, "r*", markersize=5.0)

    # plot stations
    for index, row in df.iterrows():
        xpt, ypt = m(row.stlo, row.stla)
        m.plot(xpt, ypt, "ko", markersize=1.5)

    # change coordinate show
    def set_coord_format(x, y):
        lon, lat = m(x, y, inverse=True)
        result=get_clicked_station(lon,lat,lons,lats,ids)
        if(result==None):
            return f"lon: {lon:.3f}, lat: {lat:.3f}"
        else:
            return f"id: {result[0]}, lon: {result[1]}, lat: {result[2]}"
    ax.format_coord = lambda x, y: set_coord_format(x, y)

    canvas.draw()
    return m