import tkinter as tk

from tkinter import ttk
from PIL import ImageTk, Image
from config import PRIMARY_BG
from card import Card


class WorkArea(tk.Frame):
    def __init__(self, parent: tk.Frame, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.config(width=750, height=600, background=PRIMARY_BG)

        self.close_icon = ImageTk.PhotoImage(file='./assets/close.png')
        self.reset_icon = ImageTk.PhotoImage(file='./assets/reset.png')
        self.visible_icon = ImageTk.PhotoImage(file='./assets/visible.png')
        self.invisible_icon = ImageTk.PhotoImage(file='./assets/invisible.png')

        self.card = None
        self.btn_close = None
        self.btn_reset = None
        self.btn_see_original = None
        self.image_showing = None
        self.resized_image_showing = None
        self.lbl_image = ttk.Label(self)
        self.lbl_image.config(image = self.resized_image_showing)
        
        self.buttons_bar = tk.Frame(self, background=PRIMARY_BG)

        self.bind('<Configure>', self.resize_image)

        self.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    def is_upscaled(self):
        return self.card.image['output'] is not None
    
    def toggle_image(self):
        # Changes showing image between original and output
        if self.card.image['photoImage'] == self.image_showing:
            self.image_showing = self.card.image['output']
            new_icon = self.visible_icon
        else:
            self.image_showing = self.card.image['photoImage']
            new_icon = self.invisible_icon
            
        self.btn_see_original.config(image=new_icon)
        self.resize_image(None)
    
    def reset_image(self):
        self.image_showing = self.card.image['photoImage']
        self.btn_see_original.config(image=self.visible_icon)
        self.resize_image(None)

    def close_file(self):
        self.lbl_image.place_forget()
        self.btn_close.place_forget()
        self.buttons_bar.place_forget()
        self.btn_open.place(relx=0.5, rely=0.5)
        self.btn_see_original.config(image=self.visible_icon)
        self.card = None

    def show_image(self):
        if self.card is None:
            return
        
        self.btn_open.place_forget()

        self.lbl_image.place(relx=0.5, rely=0.5, anchor='center')
        self.btn_close.place(relx=1, rely=1, anchor='se')
        self.buttons_bar.place(relx=1, rely=0, anchor='ne')

        self.resize_image(None)
    
    def resize_image(self, _):
        if self.image_showing is None:
            return
        
        padding = 50
        # Get image
        image = ImageTk.getimage(self.image_showing)

        # Calculate new size
        parent_size = max(self.winfo_width() - padding, padding), max(self.winfo_height() - padding, padding)
        image_size = image.size
        image_ratio = image_size[0] / image_size[1]

        new_size = parent_size[0], round(parent_size[0] / image_ratio)

        if new_size[1] > parent_size[1]:
            new_size = round(parent_size[1] * image_ratio), parent_size[1]

        # Resize and update image
        new_image = image.resize(new_size)
        new_image_tk = ImageTk.PhotoImage(new_image)
        self.resized_image_showing = new_image_tk

        # Update label to refresh image
        self.lbl_image.config(image = self.resized_image_showing)
    
    #########################################  EVENTS  ########################################
    def update_image(self, card: Card):
        self.card = card
        self.image_showing = card.image['output'] if card.image['output'] is not None else card.image['photoImage']
        self.btn_see_original.config(image=self.visible_icon)
        self.resize_image(None)
    
    def on_file_open(self, fn):
        self.btn_open = ttk.Button(self, text='Open', command=fn, cursor='hand2')
        self.btn_open.place(relx=0.5, rely=0.5)
    
    def on_file_close(self, fn):
        self.btn_close = ttk.Button(self, image=self.close_icon, command=fn, cursor='hand2')
    
    def on_reset(self, fn):
        self.btn_reset = ttk.Button(self.buttons_bar, image=self.reset_icon, command=fn, cursor='hand2')
        self.btn_reset.pack(side=tk.RIGHT)

    def on_see_original(self, fn):
        self.btn_see_original = ttk.Button(self.buttons_bar, image=self.visible_icon, command=fn, cursor='hand2')
        self.btn_see_original.pack(side=tk.RIGHT, padx=(0, 10))
