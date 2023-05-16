import tkinter as tk

from tkinter import ttk
from config import PRIMARY_BG


class Slider(tk.Frame):
    def __init__(self, parent: tk.Frame, *args, **kwargs) -> None:
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.config(background=PRIMARY_BG)

        self.scala = ttk.Scale(self, from_=0, to=10, orient='horizontal')
        self.scala.pack(padx=10, pady=10, fill=tk.X)

    def set_max_value(self, value: int) -> None:
        self.scala.config(to=value)
    
    def on_change(self, fn):
        self.scala.config(command=fn)

    def show(self) -> None:
        self.pack(side=tk.TOP, fill=tk.X)
    
    def hide(self) -> None:
        self.pack_forget()
