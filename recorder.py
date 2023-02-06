import math
import tkinter as tk
from gnss_client import GNSSClient


class SatLocate(object):
    def __init__(self, canvas, width):
        self._canvas = canvas
        self._width = width
        self._sat_pic_list = list()
        self.init_bg()

    def init_bg(self):
        init_bg_cfg = [
            (0, "90", None),
            (0.5 * 0.9, "60", (4, 2)),
            (0.7071 * 0.9, "45", (4, 2)),
            (0.9, "0", None),
        ]
        for pct, txt, dash in init_bg_cfg:
            r = pct * self._width / 2
            st_px = self._width / 2 - r
            ed_px = self._width / 2 + r
            self._canvas.create_oval(
                st_px, st_px, ed_px, ed_px, dash=dash)
            self._canvas.create_text(
                ed_px, self._width / 2, text=txt, fill="dimgray")

    def update_pic(self, gnss_data):
        if "sat" not in gnss_data:
            return
        for sat in self._sat_pic_list:
            self._canvas.delete(sat)
        self._sat_pic_list = list()
        sats = gnss_data["sat"]
        color_map = {
            "GP": "cornflowerblue",
            "BD": "darkorange",
            "GL": "lightgreen",
        }
        sys_in_use = dict()
        for sat in sats:
            sat_info = sats[sat]
            if not sat_info._sig:
                continue
            rmax = self._width * 0.45
            r = rmax * math.cos(math.radians(sat_info._ele))
            _az = (90 - sat_info._az)
            x = self._width / 2 + r * math.cos(math.radians(_az))
            y = self._width / 2 + -1 * r * math.sin(math.radians(_az))

            rpic = 8
            line_color = "black"
            if sat_info._is_use:
                line_color = "white"
                sys_in_use[sat_info._sys] = True

            sat_pic = self._canvas.create_oval(
                x-rpic, y-rpic, x+rpic, y+rpic, width=0, fill=color_map[sat_info._sys])
            sat_txt = self._canvas.create_text(
                x, y, text=int(sat_info._sig), fill=line_color)
            self._sat_pic_list.append(sat_pic)
            self._sat_pic_list.append(sat_txt)

        rtext = 9
        y_delta = 0
        for sys in color_map:
            fill_color = "black"
            if sys in sys_in_use:
                fill_color = "white"
            self._canvas.create_oval(
                200-rtext, 15-rtext+y_delta, 200+rtext, 15+rtext+y_delta, width=0, fill=color_map[sys])
            self._canvas.create_text(
                200, 15+y_delta, text=sys, fill=fill_color)
            y_delta += 20


class Recorder(object):
    WIDTH = 320
    HEIGHT = 240

    def __init__(self, master, **kwargs):
        self.root = master
        self._gnss_client = GNSSClient()

        self._b_close = tk.Button(root, text="EXIT", bd=1, command=self.close)

        self._b_main_page = tk.Button(
            root, text="MAIN", bd=1, command=self.render_main_page)
        self._b_info_page = tk.Button(
            root, text="INFO", bd=1, command=self.render_info_page)
        self._b_trail_page = tk.Button(
            root, text="TRAIL", bd=1, command=self.render_trail_page)

        self._sat_locate = tk.Canvas(
            root, height=Recorder.HEIGHT-28, width=Recorder.HEIGHT-28)
        self._sat_locate_updater = SatLocate(
            self._sat_locate, width=Recorder.HEIGHT-28)

        self.root.geometry('320x240')
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.end_fullscreen)

        self._page_common = [
            (self._b_close, {"x": Recorder.WIDTH -
             34, "y": 0}),
            (self._b_main_page, {"x": 0, "y": 0}),
            (self._b_info_page, {"x": 43, "y": 0}),
            (self._b_trail_page, {"x": 43+39, "y": 0}),
        ]
        self._main_page = self._page_common + [
            (self._sat_locate, {"x": 0, "y": 28})
        ]
        self._info_page = self._page_common + [

        ]
        self._trail_page = self._page_common + [

        ]
        self._total_comp = [
            self._b_close,
            self._b_main_page,
            self._b_info_page,
            self._b_trail_page,
            self._sat_locate
        ]
        self.render_main_page()
        self.auto_update()

    def toggle_fullscreen(self, event=None):
        self.root.attributes("-fullscreen", True)
        return "break"

    def end_fullscreen(self, event=None):
        self.root.attributes("-fullscreen", False)
        return "break"

    def update_all_pic(self):
        gnss_data = self._gnss_client.get_current_data()
        self._sat_locate_updater.update_pic(gnss_data)

    def render_main_page(self):
        self.clean_page()
        for comp, args in self._main_page:
            comp.place(**args)

    def render_info_page(self):
        self.clean_page()
        for comp, args in self._info_page:
            comp.place(**args)

    def render_trail_page(self):
        self.clean_page()
        for comp, args in self._trail_page:
            comp.place(**args)

    def clean_page(self):
        for comp in self._total_comp:
            comp.place_forget()

    def auto_update(self):
        self.update_all_pic()
        self.root.after(500, self.auto_update)

    def close(self):
        self._gnss_client.stop_sync_gnss()
        exit(0)


root = tk.Tk()
app = Recorder(root)
root.mainloop()
