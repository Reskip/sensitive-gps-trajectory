import time
import serial
import serial.tools.list_ports
import threading
import copy
import re


def fill_zero(origin):
    return "0" if origin == "" else origin


class Sat(object):
    def __init__(self, sys, svid, ele, az, sig, is_use=False):
        self._sys = sys
        self._svid = int(svid)
        self._ele = float(fill_zero(ele))
        self._az = float(fill_zero(az))
        self._sig = float(fill_zero(sig))
        self._is_use = is_use
        self._update_time = time.time()

    def key(self):
        return "{sys}:{svid}".format(sys=self._sys, svid=self._svid)

    def __repr__(self):
        return "[SAT-{sys}-{svid}] ({ele}, {az}) sig: {sig}, {time}".format(
            sys=self._sys,
            svid=self._svid,
            ele=self._ele,
            az=self._az,
            sig=self._sig,
            time=time.strftime("%H:%M:%S", time.localtime(self._update_time))
        )


class GGAInfo(object):
    def __init__(self, cmd):
        cmd_l = cmd.split(",")
        self._time = cmd_l[1]
        self._lat = None
        self._u_lat = cmd_l[3]
        self._lng = None
        self._u_lng = cmd_l[5]
        if len(cmd_l[2]) != 0:
            self._lat = float(cmd_l[2]) / 100
        if len(cmd_l[4]) != 0:
            self._lng = float(cmd_l[4]) / 100
        self._status = int(cmd_l[6])
        self._num_sv = cmd_l[7]
        self._hdop = cmd_l[8]
        self._msl = cmd_l[9]

    def __repr__(self):
        resp = "[GGA] {valid}".format(
            valid="VALID" if self._status == 1 else "INVALID"
        )
        if self._status != 1:
            return resp
        resp += " ({lat}{ulat}, {lng}{ulng}) {msl}M\n".format(
            lat=self._lat,
            ulat=self._u_lat,
            lng=self._lng,
            ulng=self._u_lng,
            msl=self._msl
        )
        resp += "sat num: {num_sv}, hdop: {hdop}".format(
            num_sv=self._num_sv,
            hdop=self._hdop
        )
        return resp


class GNSSClient(object):
    GNSS_SERIAL_PORT_NAME = "USB-SERIAL CH340"
    CMD_PATTERN = re.compile("^\\$(.*?)\\*")
    BAUDRATE = 38400

    def __init__(self):
        self._connect_serial_port()
        self._serial_lock = threading.Lock()
        self._stop_update_thread = False
        self._sat = dict()
        self._last_gaa = None
        self.CMD_MAP = {
            "GSV": self._GSV,
            "GGA": self._GAA,
            "GSA": self._GSA,
            "RMC": self._RMC,
            "VTG": self._VTG,
            "GLL": self._GLL,
            "TXT": self._TXT,
            "ZDA": self._ZDA
        }
        self._sync_thread = threading.Thread(target=self._sync_gnss_info)
        self._sync_thread.start()

    def _connect_serial_port(self):
        port_list = list(serial.tools.list_ports.comports())
        self._device_port = ""
        for port in port_list:
            if GNSSClient.GNSS_SERIAL_PORT_NAME not in port.description:
                continue
            self._device_port = port.device
        try:
            self._serial_device = serial.Serial(
                self._device_port, GNSSClient.BAUDRATE)
            assert self._serial_device.isOpen()
        except Exception as e:
            print("[error] cannot connect serial device \"{device}\"".format(
                device=self._device_port), e)

    def stop_sync_gnss(self):
        self._serial_lock.acquire()
        self._stop_update_thread = True
        self._serial_lock.release()

    def get_current_data(self):
        self._serial_lock.acquire()
        resp = {
            "sat": copy.deepcopy(self._sat),
            "gaa": copy.deepcopy(self._last_gaa)
        }
        self._serial_lock.release()
        return resp

    def _sync_gnss_info(self):
        print("[info] start sync gnss info")
        self._stop_update_thread = False
        while True:
            self._serial_lock.acquire()
            if self._stop_update_thread:
                self._serial_lock.release()
                break

            while self._serial_device.inWaiting() > 20:
                line = self._serial_device.readline()
                try:
                    line = line.decode('utf-8').strip()
                    cmd = line.split(",")[0][-3:]
                    cmd_line = GNSSClient.CMD_PATTERN.findall(line)
                    if len(cmd_line) != 1:
                        print("[warning] can not recognize cmd \"{line}\"".format(
                            line=line
                        ))
                        continue
                    if cmd not in self.CMD_MAP:
                        print("[warning] no matched cmd {cmd}".format(cmd=cmd))
                        continue
                    self.CMD_MAP[cmd](cmd_line[0])
                except Exception as e:
                    print("[error] parse nmea info error: {e}".format(e=e))

            self._serial_lock.release()
        print("[info] stop sync gnss info")

    def _GSV(self, cmd):
        cmd_l = cmd.split(",")
        sys = cmd_l[0][:2]
        cmd_l = cmd_l[4:]
        if len(cmd_l) % 4:
            print("[error] invalid GSV data \"{data}\"".format(data=cmd))
            return
        for i in range(len(cmd_l) // 4):
            svid = cmd_l[i*4+0]
            ele = cmd_l[i*4+1]
            az = cmd_l[i*4+2]
            sig = cmd_l[i*4+3]
            is_use = False
            new_sat = Sat(sys, svid, ele, az, sig)
            if new_sat.key() in self._sat:
                new_sat._is_use = self._sat[new_sat.key()]._is_use
            self._sat[new_sat.key()] = new_sat

    def _GAA(self, cmd):
        self._last_gaa = GGAInfo(cmd)

    def _GSA(self, cmd):
        cmd_l = cmd.split(",")
        sys = cmd_l[0][:2]
        sat_ids = filter(lambda x: x is not None and x != "", cmd_l[3:15])
        sat_ids = [int(i) for i in sat_ids]
        for sat in self._sat:
            if self._sat[sat]._sys == sys:
                self._sat[sat]._is_use = False
            if self._sat[sat]._svid in sat_ids:
                self._sat[sat]._is_use = True

    def _RMC(self, cmd):
        pass

    def _VTG(self, cmd):
        pass

    def _GLL(self, cmd):
        pass

    def _TXT(self, cmd):
        pass

    def _ZDA(self, cmd):
        pass


if __name__ == "__main__":
    gnss_client = GNSSClient()

    for i in range(10):
        print(time.time())
        print(gnss_client.get_current_data())
        time.sleep(1)

    gnss_client.stop_sync_gnss()
