import os
import time
import pickle

from gnss_client import GGAInfo
from utils import CPrint


class Point(object):
    def __init__(self, lat, lng, msl=0.0, u_lat="N", u_lng="E", time_=None, hdop=0):
        self._lat = lat
        self._lng = lng
        self._u_lat = u_lat
        self._u_lng = u_lng
        self._msl = msl
        self._time = time_
        if not time_:
            self._time = time.time()
        self._hdop = hdop


class Trail(object):
    def __init__(self, file=None):
        if file:
            try:
                load_file = open(file, "rb")
                self = pickle.load(load_file)
                return
            except Exception as e:
                CPrint.print(
                    "[error] load trail fail: {file}".format(file=file), e)

        self._path = "data"
        self._create_time = time.time()
        self._last_save = time.time()
        self._name = time.strftime(
            '%Y%m%d_%H%M', time.localtime(self._create_time))
        self._points = list()
        self._lat_lim = None
        self._lng_lim = None
        self._msl_lim = None

    def update(self, gnss_data):
        if "gga" not in gnss_data or gnss_data["gga"] is None:
            return
        gga_info = gnss_data["gga"]
        if gga_info._status != 1:
            return
        # if len(self._points) != 0:
        #     last_p = self._points[-1]
        #     if last_p._lat == gga_info._lat and last_p._lng == gga_info._lng:
        #         return
        if not self._lat_lim:
            self._lat_lim = [gga_info._lat, gga_info._lat]
            self._lng_lim = [gga_info._lng, gga_info._lng]
            self._msl_lim = [gga_info._msl, gga_info._msl]
        else:
            self._lat_lim = [min(gga_info._lat, self._lat_lim[0]), max(
                gga_info._lat, self._lat_lim[1])]
            self._lng_lim = [min(gga_info._lng, self._lng_lim[0]), max(
                gga_info._lng, self._lng_lim[1])]
            self._msl_lim = [min(gga_info._msl, self._msl_lim[0]), max(
                gga_info._msl, self._msl_lim[1])]

        self._points.append(Point(
            gga_info._lat,
            gga_info._lng,
            u_lat=gga_info._u_lat,
            u_lng=gga_info._u_lng,
            msl=gga_info._msl,
            hdop=gga_info._hdop
        ))
        if time.time() - self._last_save > 60 * 5:
            self._last_save = time.time()
            self.save(auto=True)

    def save(self, auto=False):
        auto_append = ""
        auto_log = ""
        if auto:
            auto_append = "_auto"
            auto_log = "(auto save)"
        dump_file_name = os.path.join(self._path, self._name) + auto_append
        dump_file = open(dump_file_name, "wb")
        pickle.dump(self, dump_file)
        dump_file.close()

        CPrint.print(
            "[info]{auto} pickle file {file} dump success".format(file=dump_file, auto=auto_log))
