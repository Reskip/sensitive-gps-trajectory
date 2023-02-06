import os
import time
import pickle


class Point(object):
    def __init__(self, lat, lng, u_lat="N", u_lng="E", time=None, hdop=0):
        self._lat = lat,
        self._lng = lng,
        self._u_lat = u_lat,
        self._u_lng = u_lng,
        self._time = time
        if not time:
            self._time = time.time()
        self._hdop = hdop


class Trail(object):
    def __init__(self, file=None):
        if file:
            try:
                self = pickle.load(file)
                return
            except Exception as e:
                print("[error] load trail fail: {file}".format(file=file))

        self._create_time = time.time()
        self._name = time.strftime(
            '%Y%m%d_%H%M', time.localtime(self._create_time))
        self._points = list()

    def save(self, path):
        dump_file = os.path.join(path, self._name)
        pickle.dump(self, dump_file)
        print("[info] pickle file {file} dump success".format(file=dump_file))
