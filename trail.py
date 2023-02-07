import os
import time
import pickle

from gnss_client import GGAInfo
from utils import CPrint


class Point(object):
    def __init__(self, lat, lng, u_lat="N", u_lng="E", time_=None, hdop=0):
        self._lat = lat,
        self._lng = lng,
        self._u_lat = u_lat,
        self._u_lng = u_lng,
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

        self._create_time = time.time()
        self._name = time.strftime(
            '%Y%m%d_%H%M', time.localtime(self._create_time))
        self._points = list()

    def update(self, gnss_data):
        if "gaa" not in gnss_data or gnss_data["gaa"] is None:
            return
        gaa_info = gnss_data["gaa"]
        if gaa_info._status != 1:
            return
        if len(self._points) != 0:
            last_p = self._points[-1]
            if last_p._lat == gaa_info._lat and last_p._lng == gaa_info._lng:
                return
        self._points.append(Point(
            gaa_info._lat,
            gaa_info._lng,
            u_lat=gaa_info._u_lat,
            u_lng=gaa_info._u_lng,
            hdop=gaa_info._hdop
        ))

    def save(self, path):
        dump_file_name = os.path.join(path, self._name)
        dump_file = open(dump_file_name, "wb")
        pickle.dump(self, dump_file)
        dump_file.close()
        CPrint.print(
            "[info] pickle file {file} dump success".format(file=dump_file))
