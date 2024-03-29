import time
import serial
import serial.tools.list_ports
import threading
import copy
import re

from utils import CPrint, str_to_gps84


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
        self._msl = None
        if len(cmd_l[2]) != 0:
            self._lat = str_to_gps84(*cmd_l[2].split("."))
        if len(cmd_l[4]) != 0:
            self._lng = str_to_gps84(*cmd_l[4].split("."))
        if len(cmd_l[9]) != 0:
            self._msl = float(cmd_l[9])
        self._status = int(cmd_l[6])
        self._num_sv = cmd_l[7]
        self._hdop = cmd_l[8]

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
        self._status = False
        self._connect_serial_port()
        self._serial_lock = threading.Lock()
        self._stop_update_thread = False
        self._sat = dict()
        self._last_gga = None
        self.CMD_MAP = {
            "GSV": self._GSV,
            "GGA": self._GGA,
            "GSA": self._GSA,
            "RMC": self._RMC,
            "VTG": self._VTG,
            "GLL": self._GLL,
            "TXT": self._TXT,
            "ZDA": self._ZDA
        }
        if not self._status:
            return
        self._sync_thread = threading.Thread(target=self._sync_gnss_info)
        self._sync_thread.start()

    def _connect_serial_port(self):
        port_list = list(serial.tools.list_ports.comports())
        self._device_port = ""
        for port in port_list:
            if "usb" not in port.description.lower() or "serial" not in port.description.lower():
                continue
            self._device_port = port.device
        try:
            self._serial_device = serial.Serial(
                self._device_port, GNSSClient.BAUDRATE)
            assert self._serial_device.isOpen()
            self._status = True
        except Exception as e:
            CPrint.print("[error] cannot connect serial device \"{device}\", {e}".format(
                device=self._device_port, e=e))

    def stop_sync_gnss(self):
        self._serial_lock.acquire()
        self._stop_update_thread = True
        self._serial_device.close()
        self._serial_lock.release()

    def get_current_data(self):
        self._serial_lock.acquire()
        resp = {
            "sat": copy.deepcopy(self._sat),
            "gga": copy.deepcopy(self._last_gga)
        }
        self._serial_lock.release()
        return resp

    def _sync_gnss_info(self):
        CPrint.print("[info] start sync gnss info")
        self._stop_update_thread = False
        while True:
            self._serial_lock.acquire()
            if self._stop_update_thread:
                self._serial_lock.release()
                break

            try:
                while self._serial_device.inWaiting() > 20:
                    line = self._serial_device.readline()
                    try:
                        line = line.decode('utf-8').strip()
                        cmd = line.split(",")[0][-3:]
                        cmd_line = GNSSClient.CMD_PATTERN.findall(line)
                        if len(cmd_line) != 1:
                            CPrint.print("[warning] can not recognize cmd \"{line}\"".format(
                                line=line
                            ))
                            continue
                        if cmd not in self.CMD_MAP:
                            CPrint.print(
                                "[warning] no matched cmd {cmd}".format(cmd=cmd))
                            continue
                        self.CMD_MAP[cmd](cmd_line[0])
                    except Exception as e:
                        CPrint.print(
                            "[error] parse nmea info error: {e}".format(e=e))
            except Exception as e:
                CPrint.print(
                    "[error] serial connect error: {e}".format(e=e))
                self._status = False
                self._serial_lock.release()
                break

            self._serial_lock.release()
        CPrint.print("[info] stop sync gnss info")

    def _GSV(self, cmd):
        cmd_l = cmd.split(",")
        sys = cmd_l[0][:2]
        cmd_l = cmd_l[4:]
        if len(cmd_l) % 4:
            CPrint.print(
                "[error] invalid GSV data \"{data}\"".format(data=cmd))
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

    def _GGA(self, cmd):
        self._last_gga = GGAInfo(cmd)

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
        CPrint.print(time.time())
        CPrint.print(gnss_client.get_current_data())
        time.sleep(1)

    gnss_client.stop_sync_gnss()
