import os
import gc
import math
import tkinter as tk
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
# https://blog.csdn.net/qq_44817900/article/details/124302515
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter
import threading

from gnss_client import GNSSClient
from trail import Trail
from utils import CPrint


class SatLocate(object):
    def __init__(self, root, bg_img):
        self.root = root
        self.bg_img = bg_img

    def update_pic(self, gnss_data):
        sat_use = 0
        sat_total = 0
        hdop = "--"
        stime = "--"
        if "sat" in gnss_data:
            sats = gnss_data["sat"]
            self.root.delete("sat")

            for sat in sats:
                sat_info = sats[sat]
                if not sat_info._sig:
                    continue
                sat_total += 1
                rmax = 85
                r = rmax * math.cos(math.radians(sat_info._ele))
                az = (90 - sat_info._az)
                x = 102 + r * math.cos(math.radians(az)) + 4
                y = 140 + -1 * r * math.sin(math.radians(az))

                if sat_info._is_use:
                    sat_use += 1
                img_key = sat_info._sys + ("" if sat_info._is_use else "_NU")
                self.root.create_image(
                    x, y, image=self.bg_img[img_key], anchor=tk.NW, tags=("sat"))
        if "gga" in gnss_data and gnss_data["gga"] is not None:
            gga_info = gnss_data["gga"]
            if gga_info._status == 1:
                hdop = gga_info._hdop + \
                    ("" if len(gga_info._hdop) > 3 else "m")
                stime = gga_info._time
                h = stime[:2]
                m = stime[2:4]
                s = stime[4:6]
                stime = "{hh}:{mm}:{ss}".format(hh=h, mm=m, ss=s)
        self.root.create_text(
            67, 15, text="{}/{}".format(sat_use, sat_total), fill='#878787', font=("Arial", 8, "bold"), anchor=tk.NW, tags=("sat"))
        self.root.create_text(
            116, 15, text=hdop, fill='#878787', font=("Arial", 8, "bold"), anchor=tk.NW, tags=("sat"))
        self.root.create_text(
            165, 15, text=stime, fill='#878787', font=("Arial", 8, "bold"), anchor=tk.NW, tags=("sat"))


class Recorder(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.active = False
        self.trail = None
        self.last_trail_img = None
        self.trail_cache_image = None
        self.now_at = "home"
        self.trail_mode = True

        self.figure_2d = Figure(figsize=(2.8, 3), dpi=100, facecolor="#242424")
        self.subplot_2d = self.figure_2d.add_subplot(1, 1, 1)
        self.subplot_2d.axis('off')

        self.figure_3d = Figure(figsize=(2.8, 3), dpi=100, facecolor="#242424")
        self.subplot_3d = self.figure_3d.add_subplot(1, 1, 1, projection='3d')
        self.subplot_3d.axis('on')

        self.title("Recorder")
        self.geometry("320x240")

        # set grid layout 1x2
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        customtkinter.set_appearance_mode("Dark")

        # load images with light and dark mode image
        image_path = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "image")
        self.logo_image = customtkinter.CTkImage(Image.open(os.path.join(
            image_path, "send.png")), size=(26, 26))
        self.main_bg_image = tk.PhotoImage(
            file=os.path.join(image_path, "main.png"))
        self.edit_image = tk.PhotoImage(
            file=os.path.join(image_path, "edit.png"))
        self.edit_active_image = tk.PhotoImage(
            file=os.path.join(image_path, "edit_active.png"))
        self.main_status_image = tk.PhotoImage(
            file=os.path.join(image_path, "status_bar.png"))
        self.main_status_side_image = tk.PhotoImage(
            file=os.path.join(image_path, "status_bar_side.png"))
        self.image_icon_image = customtkinter.CTkImage(Image.open(
            os.path.join(image_path, "send.png")), size=(20, 20))
        self.sat_image = {
            "BD": tk.PhotoImage(file=os.path.join(image_path, "beidou.png")),
            "GP": tk.PhotoImage(file=os.path.join(image_path, "gps.png")),
            "GL": tk.PhotoImage(file=os.path.join(image_path, "glonass.png")),
            "NU": tk.PhotoImage(file=os.path.join(image_path, "notuse.png")),
            "BD_NU": tk.PhotoImage(file=os.path.join(image_path, "beidou_nu.png")),
            "GP_NU": tk.PhotoImage(file=os.path.join(image_path, "gps_nu.png")),
            "GL_NU": tk.PhotoImage(file=os.path.join(image_path, "glonass_nu.png")),
        }
        self.home_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "home.png")),
                                                 dark_image=Image.open(os.path.join(image_path, "home.png")), size=(20, 20))
        self.paper_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "paper.png")),
                                                  dark_image=Image.open(os.path.join(image_path, "paper.png")), size=(20, 20))
        self.close_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "close.png")),
                                                  dark_image=Image.open(os.path.join(image_path, "close.png")), size=(20, 20))
        self.location_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "location.png")),
                                                     dark_image=Image.open(os.path.join(image_path, "location.png")), size=(20, 20))

        # create navigation frame
        self.navigation_frame = customtkinter.CTkFrame(
            self, corner_radius=0, width=70)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(5, weight=1)

        self.navigation_frame_label = customtkinter.CTkLabel(self.navigation_frame, text=" GNSS", image=self.logo_image,
                                                             compound="left", font=customtkinter.CTkFont(size=15, weight="bold"))
        self.navigation_frame_label.grid(row=0, column=0, padx=10, pady=10)

        self.home_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, width=70, height=40, border_spacing=10, text="HOME",
                                                   fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                   image=self.home_image, anchor="w", command=self.home_button_event)
        self.home_button.grid(row=1, column=0, sticky="ew")

        self.trail_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, width=70, height=40, border_spacing=10, text="TRAIL",
                                                    fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                    image=self.location_image, anchor="w", command=self.trail_button_event)
        self.trail_button.grid(row=2, column=0, sticky="ew")

        self.info_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, width=70, height=40, border_spacing=10, text="INFO",
                                                   fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                   image=self.paper_image, anchor="w", command=self.info_button_event)
        self.info_button.grid(row=3, column=0, sticky="ew")

        self.exit_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, width=70, height=40, border_spacing=10, text="EXIT",
                                                   fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray10", "gray10"),
                                                   image=self.close_image, anchor="w", command=self.exit_button_event)
        self.exit_button.grid(row=4, column=0, sticky="ew")

        # create home frame
        self.home_frame = customtkinter.CTkFrame(
            self, corner_radius=0, fg_color="transparent", border_width=0)
        self.home_frame.grid_columnconfigure(0, weight=0)

        self.canvas = tk.Canvas(
            self.home_frame, height=240, width=230)
        self.canvas.create_image(
            -90, 2, image=self.main_bg_image, anchor=tk.NW)
        self.canvas.create_image(
            37, 7, image=self.main_status_image, anchor=tk.NW)
        self.canvas.create_image(
            4, 7, image=self.main_status_side_image, anchor=tk.NW, tags=("log_trail"))
        self.log_icon = self.canvas.create_image(
            15, 14, image=self.edit_image, anchor=tk.NW, tags=("log_trail"))
        self.canvas.tag_bind('log_trail', '<Button-1>', self.log_trail)
        self.canvas.place(x=-4, y=-2)

        # create trail frame
        self.trail_frame = customtkinter.CTkFrame(
            self, corner_radius=0, fg_color="transparent")
        self.trail_canvas = tk.Canvas(
            self.trail_frame, height=240, width=230, bg="#242424")

        self.canvas_tk_agg_2d = FigureCanvasTkAgg(
            self.figure_2d, master=self.trail_canvas)
        self.canvas_widget_2d = self.canvas_tk_agg_2d.get_tk_widget()
        self.canvas_widget_2d.tag_bind('trail_mode', '<Button-1>',
                                       self.update_trail_mode)

        self.canvas_tk_agg_3d = FigureCanvasTkAgg(
            self.figure_3d, master=self.trail_canvas)
        self.canvas_widget_3d = self.canvas_tk_agg_3d.get_tk_widget()
        self.canvas_widget_3d.tag_bind('trail_mode', '<Button-1>',
                                       self.update_trail_mode)
        self.canvas_widget_now = self.canvas_widget_2d
        self.canvas_widget_now.place(x=-32, y=-32)

        self.update_trail_mode(None)
        self.trail_canvas.place(x=0, y=0)

        # create info frame
        self.info_frame = customtkinter.CTkFrame(
            self, corner_radius=0, fg_color="transparent")
        self.infobox = customtkinter.CTkTextbox(
            self.info_frame, width=206, height=220)
        self.infobox.grid(row=0, column=1, padx=(
            10, 10), pady=(10, 10), sticky="nsew")
        CPrint.set_text_box(self.infobox)

        # select default frame
        self.sat_locate_updater = SatLocate(
            self.canvas, self.sat_image)
        self.gnss_client = GNSSClient()
        self.select_frame_by_name("home")
        self.clear_temp_file()
        self.active = True
        self.auto_update()

    def select_frame_by_name(self, name):
        # set button color for selected button
        self.home_button.configure(
            fg_color=("gray75", "gray25") if name == "home" else "transparent")
        self.trail_button.configure(
            fg_color=("gray75", "gray25") if name == "trail" else "transparent")
        self.info_button.configure(
            fg_color=("gray75", "gray25") if name == "info" else "transparent")

        self.now_at = name

        # show selected frame
        if name == "home":
            self.home_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.home_frame.grid_forget()
        if name == "trail":
            self.trail_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.trail_frame.grid_forget()
        if name == "info":
            self.info_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.info_frame.grid_forget()

    def log_trail(self, event):
        self.canvas.delete(self.log_icon)
        if self.trail == None:
            self.log_icon = self.canvas.create_image(
                15, 14, image=self.edit_active_image, anchor=tk.NW, tags=("log_trail"))
            self.trail = Trail()
        else:
            self.trail.save()
            self.trail = None
            self.log_icon = self.canvas.create_image(
                15, 14, image=self.edit_image, anchor=tk.NW, tags=("log_trail"))

    def auto_update(self):
        gnss_data = self.gnss_client.get_current_data()
        self.sat_locate_updater.update_pic(gnss_data)
        if self.trail:
            self.trail.update(gnss_data)
            self.update_trail_pic()
        self.after(500, self.auto_update)

    def update_trail_mode(self, event):
        if event is not None:
            self.trail_mode = not self.trail_mode
            if not self.trail_mode:
                self.canvas_widget_2d.place_forget()
                self.canvas_widget_3d.place(x=-32, y=-32)
                self.canvas_widget_now = self.canvas_widget_3d
            else:
                self.canvas_widget_3d.place_forget()
                self.canvas_widget_2d.place(x=-32, y=-32)
                self.canvas_widget_now = self.canvas_widget_2d

        self.canvas_widget_now.delete("trail_mode")
        text = "2D" if self.trail_mode else "3D"
        self.canvas_widget_now.create_image(
            34, 37, image=self.main_status_side_image, anchor=tk.NW, tags=("trail_mode"))
        self.canvas_widget_now.create_text(
            45, 44, text=text, fill='#878787', font=("Arial", 10, "bold"), anchor=tk.NW, tags=("trail_mode", "text"))

    def update_trail_pic_2d(self):
        self.subplot_2d.clear()
        self.subplot_2d.axis('off')
        line_x = list()
        line_y = list()
        for p in self.trail._points:
            line_x.append(p._lat)
            line_y.append(p._lng)

        eps = 0.001
        if self.trail._lat_lim:
            lat_lim_dif = self.trail._lat_lim[1] - self.trail._lat_lim[0]
            lng_lim_dif = self.trail._lng_lim[1] - self.trail._lng_lim[0]
            max_lim = max(lat_lim_dif, lng_lim_dif) + eps
            lat_lim_dif = (max_lim - lat_lim_dif) / 2 + max_lim * 0.1
            lng_lim_dif = (max_lim - lng_lim_dif) / 2 + max_lim * 0.1
            self.subplot_2d.set_xlim(self.trail._lat_lim[0] -
                                     lat_lim_dif, self.trail._lat_lim[1] + lat_lim_dif)
            self.subplot_2d.set_ylim(self.trail._lng_lim[0] -
                                     lng_lim_dif, self.trail._lng_lim[1] + lng_lim_dif)

        self.subplot_2d.plot(line_x, line_y, alpha=0.8, color="#6495ED")
        if len(line_x):
            self.subplot_2d.scatter([line_x[-1]], [line_y[-1]],
                                    alpha=0.8, color="#6495ED")
        self.canvas_tk_agg_2d.draw()

    def update_trail_pic_3d(self):
        self.subplot_3d.clear()
        self.subplot_3d.axis('on')
        self.subplot_3d.patch.set_facecolor('#242424')
        self.subplot_3d.w_xaxis.set_pane_color((0.0, 0.0, 0.0, 0.0))
        self.subplot_3d.w_yaxis.set_pane_color((0.0, 0.0, 0.0, 0.0))
        self.subplot_3d.w_zaxis.set_pane_color((0.0, 0.0, 0.0, 0.0))
        line_config = {"linewidth": 1.2, "color": "#777777"}
        self.subplot_3d.xaxis._axinfo["grid"].update(line_config)
        self.subplot_3d.yaxis._axinfo["grid"].update(line_config)
        self.subplot_3d.zaxis._axinfo["grid"].update(line_config)
        self.subplot_3d.w_xaxis.set_ticklabels([])
        self.subplot_3d.w_yaxis.set_ticklabels([])
        self.subplot_3d.w_zaxis.set_ticklabels([])
        plt.rcParams['figure.dpi'] = 100
        line_x = list()
        line_y = list()
        line_z = list()
        for p in self.trail._points:
            line_x.append(p._lat)
            line_y.append(p._lng)
            line_z.append(p._msl)

        eps = 0.001
        if self.trail._lat_lim:
            lat_lim_dif = self.trail._lat_lim[1] - self.trail._lat_lim[0]
            lng_lim_dif = self.trail._lng_lim[1] - self.trail._lng_lim[0]
            max_lim = max(lat_lim_dif, lng_lim_dif) + eps
            lat_lim_dif = (max_lim - lat_lim_dif) / 2
            lng_lim_dif = (max_lim - lng_lim_dif) / 2
            self.subplot_3d.set_xlim(self.trail._lat_lim[0] -
                                     lat_lim_dif, self.trail._lat_lim[1] + lat_lim_dif)
            self.subplot_3d.set_ylim(self.trail._lng_lim[0] -
                                     lng_lim_dif, self.trail._lng_lim[1] + lng_lim_dif)
            self.subplot_3d.set_zlim(self.trail._msl_lim[0] -
                                     50, self.trail._msl_lim[1] + 50)

        self.subplot_3d.plot(line_x, line_y, line_z,
                             alpha=0.8, color="#6495ED")
        if len(line_x):
            self.subplot_3d.scatter([line_x[-1]], [line_y[-1]],
                                    [line_z[-1]], alpha=0.8, color="#6495ED")
        self.canvas_tk_agg_3d.draw()

    def update_trail_pic(self):
        self.update_trail_pic_2d()
        self.update_trail_pic_3d()
        self.update_trail_mode(None)

    def clear_temp_file(self):
        for root, dirs, files in os.walk("."):
            for file in files:
                path = os.path.join(root, file)
                if file[0] == "_":
                    CPrint.print("[info] remove temp file {f}".format(f=path))
                    os.remove(path)

    def home_button_event(self):
        self.select_frame_by_name("home")

    def trail_button_event(self):
        self.select_frame_by_name("trail")

    def info_button_event(self):
        self.select_frame_by_name("info")

    def exit_button_event(self):
        self.active = False
        CPrint.set_text_box(None)
        self.gnss_client.stop_sync_gnss()
        if self.trail:
            self.trail.save()
        self.quit()
        self.destroy()


if __name__ == "__main__":
    recorder = Recorder()
    recorder.overrideredirect(False)
    recorder.mainloop()
