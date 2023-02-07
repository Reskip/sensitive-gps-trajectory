import os
import math
import tkinter as tk
from PIL import Image
import customtkinter

from gnss_client import GNSSClient


class SatLocate(object):
    def __init__(self, root, bg_img):
        self.root = root
        self.bg_img = bg_img
        self.sat_pic_list = list()

    def update_pic(self, gnss_data):
        if "sat" not in gnss_data:
            return

        new_sat_pic_list = list()
        sats = gnss_data["sat"]

        for sat in sats:
            sat_info = sats[sat]
            if not sat_info._sig:
                continue
            rmax = 85
            r = rmax * math.cos(math.radians(sat_info._ele))
            az = (90 - sat_info._az)
            x = 102 + r * math.cos(math.radians(az)) + 4
            y = 140 + -1 * r * math.sin(math.radians(az))

            img_key = sat_info._sys + ("" if sat_info._is_use else "_NU")
            sat_pic = self.root.create_image(
                x, y, image=self.bg_img[img_key], anchor=tk.NW)

            # sat_txt = self.root.create_text(
            #     x, y, text=int(sat_info._sig), fill=line_color)
            new_sat_pic_list.append(sat_pic)
            # new_sat_pic_list.append(sat_txt)

        for sat in self.sat_pic_list:
            self.root.delete(sat)
        self.sat_pic_list = new_sat_pic_list


class Recorder(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.gnss_client = GNSSClient()
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
            4, 7, image=self.main_status_side_image, anchor=tk.NW)
        self.canvas.place(x=-4, y=-2)

        # create second frame
        self.trail_frame = customtkinter.CTkFrame(
            self, corner_radius=0, fg_color="transparent")

        # create third frame
        self.info_frame = customtkinter.CTkFrame(
            self, corner_radius=0, fg_color="transparent")

        # select default frame
        self.sat_locate_updater = SatLocate(
            self.canvas, self.sat_image)
        self.select_frame_by_name("home")
        self.auto_update()

    def select_frame_by_name(self, name):
        # set button color for selected button
        self.home_button.configure(
            fg_color=("gray75", "gray25") if name == "home" else "transparent")
        self.trail_button.configure(
            fg_color=("gray75", "gray25") if name == "trail" else "transparent")
        self.info_button.configure(
            fg_color=("gray75", "gray25") if name == "info" else "transparent")

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

    def update_all_pic(self):
        gnss_data = self.gnss_client.get_current_data()
        self.sat_locate_updater.update_pic(gnss_data)

    def auto_update(self):
        self.update_all_pic()
        self.after(500, self.auto_update)

    def home_button_event(self):
        self.select_frame_by_name("home")

    def trail_button_event(self):
        self.select_frame_by_name("trail")

    def info_button_event(self):
        self.select_frame_by_name("info")

    def exit_button_event(self):
        self.gnss_client.stop_sync_gnss()
        exit(0)


if __name__ == "__main__":
    recorder = Recorder()
    recorder.overrideredirect(True)
    recorder.mainloop()
