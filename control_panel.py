import tkinter as tk
import torch

from tkinter import ttk
from PIL import ImageTk
from config import SECONDARY_BG, PRIMARY_BG, DEFAULT_OUTPUT_FOLDER, IMAGE_EXTENSIONS


LEFT_PADDING = 20


class ControlPanel(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.config(width=350, background=SECONDARY_BG)

        #########################################  TEMPLATE  #########################################

        # AI MODELS
        self.lbl_selector = ttk.Label(self, text='AI Model:', background=SECONDARY_BG)
        self.lbl_selector.pack(side=tk.TOP, pady=(15, 0), padx=(LEFT_PADDING, 0), anchor='w')

        models_list = ['BSRGAN', 'BSRGANx2', 'ESRGAN', 'FSSR_JPEG', 'RealSR_DPED', 'RealSR_JPEG', 'RRDB']
        self.model_selector = ttk.Combobox(self, values=models_list, state='readonly', cursor='hand2')
        self.model_selector.current(0)  # Select first option
        self.model_selector.pack(side=tk.TOP, pady=5, padx=(LEFT_PADDING,), anchor='w')

        # GPU DEVICES
        self.lbl_device = ttk.Label(self, text='GPU Device:', background=SECONDARY_BG)
        self.lbl_device.pack(side=tk.TOP, pady=(15, 0), padx=(LEFT_PADDING, 0), anchor='w')

        devices = []
        for i in range(torch.cuda.device_count()):
            devices.append(torch.cuda.get_device_properties(i).name)
        self.gpu_selector = ttk.Combobox(self, values=devices, state='readonly', cursor='hand2')
        self.gpu_selector.current(0)  # Select first option
        self.gpu_selector.pack(side=tk.TOP, pady=5, padx=(LEFT_PADDING, 0), anchor='w')

        # OUTPUT FORMAT
        self.lbl_output_format = ttk.Label(self, text='Output format:', background=SECONDARY_BG)
        self.lbl_output_format.pack(side=tk.TOP, pady=(15, 0), padx=(LEFT_PADDING, 0), anchor='w')

        self.output_format_selector = ttk.Combobox(self, values=IMAGE_EXTENSIONS, state='readonly', cursor='hand2')
        self.output_format_selector.current(0)  # Select first option
        self.output_format_selector.pack(side=tk.TOP, pady=5, padx=(LEFT_PADDING,), anchor='w')

        # OUTPUT FOLDER
        self.lbl_output_folder = ttk.Label(self, text='Output folder:', background=SECONDARY_BG)
        self.lbl_output_folder.pack(side=tk.TOP, pady=(20, 0), padx=(LEFT_PADDING, 0), anchor='w')

        self.output_folder_entry = ttk.Entry(self)
        self.output_folder_entry.insert(0, DEFAULT_OUTPUT_FOLDER)
        self.output_folder_entry.pack(side=tk.TOP, pady=5, padx=(LEFT_PADDING, 0), anchor='w')

        self.btn_folder = ttk.Button(self, text='Select', cursor='hand2')
        self.btn_folder.pack(side=tk.TOP, pady=5, padx=(LEFT_PADDING, 0), anchor='w')

        # UPSCALE BUTTON
        self.btn_upscale = ttk.Button(self, text='Upscale', cursor='hand2')
        self.btn_upscale.pack(side=tk.TOP, pady=(50, 0))

        # VIDEO CONTROL
        self.video_frm = tk.Frame(self, background=SECONDARY_BG)

        self.start_lbl = ttk.Label(self.video_frm, text='Start', background=SECONDARY_BG)
        self.start_entry = ttk.Entry(self.video_frm, width=6)
        self.start_entry.insert(0, 0)
        self.start_entry.bind('<Key>', self.start_no_empty)

        self.end_lbl = ttk.Label(self.video_frm, text='End', background=SECONDARY_BG)
        self.end_entry = ttk.Entry(self.video_frm, width=6)

        self.btn_upscale_video_and_save = ttk.Button(self.video_frm, text='Upscale & Save')

        self.start_lbl.grid(row=0, column=0, padx=(0, 5))
        self.start_entry.grid(row=1, column=0, padx=(0, 5))
        self.end_lbl.grid(row=0, column=1, padx=(5, 0))
        self.end_entry.grid(row=1, column=1, padx=(5, 0))
        self.btn_upscale_video_and_save.grid(row=2, column=0, columnspan=2, pady=10)

        # SEPARATOR
        self.separator = tk.Frame(self)
        self.separator.config(height=2, width=300, background=PRIMARY_BG)
        self.separator.pack(side=tk.BOTTOM)

        # SAVE BUTTON
        self.btn_save = ttk.Button(self, text='Save to file', width=20, cursor='hand2')

        self.pack(side=tk.LEFT, fill=tk.Y)

    #########################################  METHODS  #########################################
    def set_video_length(self, end) -> None:
        entry = round(float(self.start_entry.get()))
        if end < entry:
            self.start_entry.delete(0, tk.END)
            self.start_entry.insert(0, max(end - 1, 0))

        self.end_entry.delete(0, tk.END)
        self.end_entry.insert(0, end)
    
    def show_video_controls(self) -> None:
        self.separator.pack_forget()
        self.video_frm.pack(side=tk.BOTTOM)
    
    def hide_video_controls(self) -> None:
        self.video_frm.pack_forget()
        self.separator.pack(side=tk.BOTTOM)

    #########################################  EVENTS  #########################################
    def start_no_empty(self, _):
        if self.start_entry.get() == '':
            self.start_entry.insert(0, 0)

    def on_model_change(self, fn):
        self.model_selector.bind('<<ComboboxSelected>>', lambda _, entry=self.model_selector: fn(entry))

    def on_gpu_change(self, fn):
        self.gpu_selector.bind('<<ComboboxSelected>>', lambda _, entry=self.gpu_selector: fn(entry))

    def on_output_format_change(self, fn):
        self.output_format_selector.bind('<Key>', lambda _, entry=self.output_format_selector: fn(entry))

    def on_output_folder_change(self, fn):
        self.output_folder_entry.bind('<Key>', lambda _, entry=self.output_folder_entry: fn(entry))

    def on_select_folder(self, fn):
        self.btn_folder.config(command=fn)
    
    def on_ready(self, fn):
        self.btn_upscale.config(command=fn)

    def on_save(self, fn):
        self.btn_save.config(command=fn)

    def on_video_upscale(self, fn):
        self.btn_upscale_video_and_save.config(command=fn)

    def on_video_end_change(self, fn):
        self.end_entry.bind('<Key>', lambda _, entry=self.end_entry: fn(entry))
