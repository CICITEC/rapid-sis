import matplotlib

# matplotlib.use("Agg")
import matplotlib.gridspec as gridspec
import matplotlib.pylab as plt
from mpl_toolkits.basemap import Basemap
import sys
import numpy as np
from obspy.geodetics.base import gps2dist_azimuth

# Tuple: latitude, longitude, description
known_stations = {
    "PAUS": (
        9.029969,
        -79.522035,
        "TITAN SMA instalado en el depósito del Centro de Estudios de Artes Audiovisuales de la USMA en Ciudad de Panamá.",
    ),
    "PACO": (
        8.534394,
        -79.88648,
        "TITAN SMA instalado en residencia ubicada en Coronado, Panamá Oeste (no está vinculado al servidor).",
    ),
    "CHUS": (
        8.459445,
        -82.433284,
        "TITAN SMA instalado en la sede de la USMA en David, Chiriquí.",
    ),
}


def compute_distance(lat, lon, station_lat, station_lon):
    # Compute the distance between a point, given in latitude and longitude, and our station. Returns the distance in meters.
    dist = gps2dist_azimuth(lat, lon, station_lat, station_lon)
    return dist[0]


# TODO: Add working with points
def gen_map(fig, gspec, comp_bundle, path):
    ax = fig.add_subplot(gspec)

    station_name = comp_bundle.comp_list[0].trace.stats.station
    station_lat = comp_bundle.station_latitude
    station_lon = comp_bundle.station_longitude
    # No station position provided
    empty_station = False
    if station_lat == 0.0 and station_lon == 0.0:
        if station_name in known_stations:
            station_lat = known_stations[station_name][0]
            station_lon = known_stations[station_name][1]
        else:
            empty_station = True

    # No event position provided
    ev_lat = comp_bundle.latitude
    ev_lon = comp_bundle.longitude
    sys.stderr.write(f"{ev_lat}, {ev_lon}")
    empty_ev = False
    if ev_lat == 0 and ev_lon == 0:
        empty_ev = True

    # We know one or both of them is 0,
    # so we can add safely
    if empty_station or empty_ev:
        lat_zero = station_lat + ev_lat
        lon_zero = station_lon + ev_lon
    else:
        # the middle point between station and epicenter
        lat_zero = (station_lat + ev_lat) / 2
        lon_zero = (station_lon + ev_lon) / 2

    sys.stderr.write(f"{station_name}")
    m = Basemap(
        projection="aeqd",
        resolution="l",
        width=4.5e5,
        height=4.5e5,
        lat_0=lat_zero,
        lon_0=lon_zero,
    )
    m.drawcoastlines()
    m.drawcounties()
    m.drawstates()
    m.drawrivers()

    # Plot lines of longitudes
    m.drawparallels(
        np.arange(-90.0, 120.0, 1),
        labels=[1, 1, 1, 1],
        color="black",
        textcolor="black",
        fontsize=16,
    )

    # Plot latitudes
    m.drawmeridians(
        np.arange(-180.0, 180.0, 1),
        labels=[1, 0, 0, 1],
        color="black",
        textcolor="black",
        fontsize=16,
    )

    # Get the X and Y of station and add label
    station_x, station_y = m(station_lon, station_lat)
    event_x, event_y = m(ev_lon, ev_lat)

    sys.stderr.write(f"Lat:{ev_lat} Lon:{ev_lon}, ev_x:{
    event_x}, ev_y:{event_y}")
    sys.stderr.write(f"Lat:{station_lat} Lon:{station_lon}, ev_x:{
        station_x}, ev_y:{station_y}")
    if not empty_station and not empty_ev:
        epic_dist = compute_distance(
            ev_lat, ev_lon, station_lat, station_lon
        )
        line_x = np.array([station_x, event_x])
        line_y = np.array([station_y, event_y])
        plt.plot(line_x, line_y, "-.k", label="Distance")
        plt.title(f"Epicentral distance:{
        round(epic_dist / 1000, 2)} km", fontsize=18)

    if not empty_ev:
        plt.plot(
            event_x, event_y, "db", markersize=12, label="Epicenter"
        )
    if not empty_station:
        plt.plot(
            station_x, station_y, "or", markersize=12, label="Station"
        )

    plt.grid()
    plt.legend(fontsize=20)
    plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)
    plt.tight_layout()
    plt.savefig(path)
