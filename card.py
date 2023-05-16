import tkinter as tk
import cv2
import numpy as np

from config import SECONDARY_BG, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS

from tkinter import ttk
from PIL import Image, ImageTk


MAX_THUMBNAIL_SIZE = 75


class Card(tk.Frame):
    def __init__(self, parent: tk.Frame, filepath: str, index: int, *args, **kwargs) -> None:
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.config(background=SECONDARY_BG, padx=3, pady=3, cursor='hand2')
        self.selected = False
        self.index = index  # Position in footer

        # Read and load image/video
        self.image = {}
        self.image['path'] = filepath  # str
        self.image['output'] = None  # PhotoImage (PIL)

        extension = filepath.split('.')[-1]

        if extension in IMAGE_EXTENSIONS:
            self.is_image = True
            self.image['file'] = Image.open(filepath)  # Image (PIL)
            self.image['photoImage'] = ImageTk.PhotoImage(self.image['file'])  # PhotoImage (PIL)

        elif extension in VIDEO_EXTENSIONS:
            self.is_image = False
            self.video_cap = cv2.VideoCapture(filepath)
            self.frames_length = self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT)
            self.fps = self.video_cap.get(cv2.CAP_PROP_FPS)
            self.select_video_frame(0)
        else:
            raise ValueError # Handle this later

        self.thumbnail_image = self._create_thumbnail_image()

        # Image Label
        self.lbl_img = ttk.Label(self, image=self.thumbnail_image)
        self.lbl_img.pack(side=tk.LEFT)

        # Make image resolution label
        w, h = self.image['file'].size
        self.lbl_info = ttk.Label(self, text=f'{self.image["path"].split("/")[-1]}\n{w}x{h}', background=SECONDARY_BG)
        self.lbl_info.pack(side=tk.LEFT)

        # Bind to click event
        for child in self.winfo_children():
            # WidgetName eg tk::Label
            child.bindtags((child, child.widgetName.split(':')[-1], self, '.', 'all'))
    
    def select_video_frame(self, pointer: int):
        self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, pointer - 1)
        res, frame = self.video_cap.read()

        if res:
            self.image['file'] = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            self.image['photoImage'] = ImageTk.PhotoImage(self.image['file'])
            return self.image
    
    def select_subclip(self, start: int, end: int) -> list:
        self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, start - 1)

        clip = []
        for _ in range(start, end):
            res, frame = self.video_cap.read()

            if res:
                image = {}
                image['file'] = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                image['photoImage'] = ImageTk.PhotoImage(image['file'])
                clip.append(image)

        return clip
    
    def _create_thumbnail_image(self) -> ImageTk.PhotoImage:
        ratio = self.image['file'].size[0] / self.image['file'].size[1]
        new_size = MAX_THUMBNAIL_SIZE, round(MAX_THUMBNAIL_SIZE / ratio)

        if new_size[1] > MAX_THUMBNAIL_SIZE:
            new_size = round(MAX_THUMBNAIL_SIZE * ratio), MAX_THUMBNAIL_SIZE

        thumbnail = self.image['file'].resize(new_size)
        return ImageTk.PhotoImage(thumbnail)

    def toggle_border(self) -> None:
        color = 'white' if not self.selected else SECONDARY_BG
        self.selected = not self.selected
        self.config(highlightbackground=color, highlightthickness=1)
