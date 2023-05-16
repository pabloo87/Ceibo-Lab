import tkinter as tk
import torch
import asyncio
import threading
import time
import math
import os
import numpy as np
import cv2
from moviepy.editor import *

from control_panel import ControlPanel
from work_area import WorkArea
from footer import Footer
from card import Card
from slider import Slider

from ai import upscale_process
from config import PRIMARY_BG, SECONDARY_BG, DEFAULT_OUTPUT_FOLDER, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS

from tkinter.filedialog import askopenfilenames, askdirectory
from tkinter import ttk
from PIL import ImageTk, Image


# TO DO: Make a scrollbar for the footer
MAX_FILES_OPEN = 18


class MainApplication(tk.Frame):
    def __init__(self, parent, conn, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent.title('Ceibo Upscaling Lab')

        # Connection to other process
        self.conn = conn

        # PARAMS
        self.model = 'BSRGAN'
        self.gpu_id = torch.cuda.current_device()
        self.output_format = 'png'
        self.output_folder = DEFAULT_OUTPUT_FOLDER

        # TKINTER FRAMES
        self.upper_frame = tk.Frame(self)
        self.lower_frame = tk.Frame(self)

        self.control_panel = ControlPanel(self.upper_frame)  # UPPER
        self.work_area = WorkArea(self.upper_frame)  # UPPER

        self.slider = Slider(self.lower_frame)  # LOWER
        self.footer = Footer(self.lower_frame)  # LOWER

        # CONFIG FRAMES
        self.upper_frame.config(height=500)
        self.lower_frame.config(height=75)

        # EVENTS
        self.control_panel.on_model_change(self.change_model)
        self.control_panel.on_gpu_change(self.change_gpu)
        self.control_panel.on_output_format_change(self.output_format_change)
        self.control_panel.on_output_folder_change(self.change_output_folder)
        self.control_panel.on_select_folder(self.select_folder)
        self.control_panel.on_ready(self.upscale_image)
        self.control_panel.on_save(self.save_image)
        self.control_panel.on_video_end_change(self.video_end_change)
        self.control_panel.on_video_upscale(self.upscale_and_save_video)

        self.work_area.on_file_open(self.open_file)
        self.work_area.on_file_close(self.close_file)
        self.work_area.on_reset(self.reset_image)
        self.work_area.on_see_original(self.see_original)

        self.footer.on_footer_change(self.update_footer)
        self.footer.on_card_selected(self.card_selected)

        self.slider.on_change(self.slider_change)

        # PACK FRAMES
        self.upper_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.lower_frame.pack(side=tk.TOP, fill=tk.X)
    
    #########################################  EVENTS  #########################################
    def change_model(self, model_selector):
        self.model = model_selector.get()

    def change_gpu(self, gpu_selector):
        self.gpu_id = gpu_selector.current()

    def output_format_change(self, output_format_selector):
        self.output_format = output_format_selector.get()

    def change_output_folder(self, output_folder_entry):
        self.output_folder = output_folder_entry.get()
    
    def select_folder(self):
        filepath = askdirectory()

        if not filepath:
            return
        
        self.control_panel.output_folder_entry.delete(0, tk.END)
        self.control_panel.output_folder_entry.insert(0, filepath)
    
    def save_image(self):
        if not self.work_area.is_upscaled():
            return
        
        file_name = self.work_area.card.image['path'].split('/')[-1]
        file_name = file_name.split('.')[0] + '_upscaled_'
        filepath = os.path.join(self.output_folder, f'{file_name}.{self.output_format}')
        image_tk = self.work_area.card.image['output']
        image = ImageTk.getimage(image_tk)
        image.save(filepath)

    def open_file(self):
        filetypes = (
            ('Image files', [f'.{e}' for e in (*IMAGE_EXTENSIONS, *VIDEO_EXTENSIONS)]),
            ('All files', '*.*')
        )
        filepaths = askopenfilenames(filetypes=filetypes,)

        if len(filepaths) == 0:
            return
        
        filepaths = filepaths[:MAX_FILES_OPEN]
        
        for i, filepath in enumerate(filepaths):
            self.footer.create_card(filepath, i)
                
        self.footer.update_grid()

        # Load to workplace the first thumbnail
        self.select_card_by_index(0)
    
    def card_selected(self, card: Card):
        self.select_card_by_index(card.index)

    def select_card_by_index(self, index: int):
        # Select and get card
        card = self.footer.select_card_by_index(index)

        if card.image['output'] is None:
            self.control_panel.btn_save.pack_forget()
        else:
            self.control_panel.btn_save.pack(side=tk.BOTTOM, pady=(0, 15))

        if card.is_image:
            # Is image
            self.slider.hide()
            self.control_panel.hide_video_controls()
        else:
            # Is video
            frames_length = int(card.frames_length)
            self.slider.set_max_value(frames_length)
            self.control_panel.set_video_length(frames_length)
            self.control_panel.show_video_controls()
            self.slider.show()

        # Show new workplace
        self.work_area.update_image(card)
        self.work_area.show_image()
    
    def slider_change(self, value):
        # On slider change create a new card with the selected frame loaded
        value = round(float(value))
        card = self.footer.get_current_card()
        card.select_video_frame(value)
        self.control_panel.set_video_length(value)
        self.work_area.update_image(card)

    def update_footer(self, _):
        self.footer.update_grid()
    
    def close_file(self):
        self.work_area.close_file()
        index = self.footer.current_card_index()
        self.footer.remove_card_by_index(index)

        if len(self.footer.cards) > 0:
            self.select_card_by_index(0)
    
    def reset_image(self):
        self.work_area.reset_image()
        self.control_panel.btn_save.pack_forget()

    def see_original(self):
        if not self.work_area.is_upscaled():
            return

        self.work_area.toggle_image()
    
    def video_end_change(self, end_entry):
        if end_entry.get() == '':
            end_entry.insert(0, 1)
        self.slider_change(end_entry.get())
    
    def upscale_image(self):
        if not self.footer.is_card_loaded():  # Checks if there are any card loaded
            return

        card = self.footer.get_current_card()
        path, image = card.image['path'], card.image['file']
        self.upscale(path, (image, ))
    
    def upscale_and_save_video(self):
        start = int(self.control_panel.start_entry.get())
        end = int(self.control_panel.end_entry.get())

        card = self.footer.get_current_card()
        images = [image['file'] for image in card.select_subclip(start, end)]
        self.upscale(card.image['path'], images)
    
    #########################################  METHODS  #########################################
    def upscale(self, path, images):        
        modal = tk.Toplevel(self, padx=15, pady=15, background=PRIMARY_BG)
        modal.title('Upscaling')

        # Calculate position of modal (center of parent window)
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_w = self.parent.winfo_width()
        parent_h = self.parent.winfo_height()
        w, h = 350, 400  # Modal size
        offset_x = round((parent_w - w) / 2)
        offset_y = round((parent_h - h) / 2)
        modal.geometry(f'{w}x{h}+{parent_x + offset_x}+{parent_y + offset_y}')

        # Styling modal
        modal.tk.call('set_theme', 'dark')

        # Label widget
        lbl_title = ttk.Label(modal, text='Please wait till the work is done...', background=PRIMARY_BG)
        lbl_title.config(font=('Segoe Ui', 10))
        lbl_title.pack(side=tk.TOP, fill=tk.X)

        # Text widget
        txt_messages = tk.Text(modal, background=SECONDARY_BG, height=17)
        txt_messages.config(highlightbackground=SECONDARY_BG, font=('Segoe Ui', 10), state='disabled', fg='white')
        txt_messages.pack(side=tk.TOP, fill=tk.X, pady=(5,))

        # Close button
        close_btn = ttk.Button(modal, text='Wait', command=modal.destroy, state='disabled')
        close_btn.pack(side=tk.TOP)

        # Send images to scaling process
        self.conn.send([self.model, self.gpu_id, path, images])

        # Wait for process to finish
        threading.Thread(target=lambda loop: loop.run_until_complete(self.wait_for_upscaled_images(txt_messages, close_btn, is_video=len(images) > 1)),
                         args=(asyncio.new_event_loop(),)).start()

    
    async def wait_for_upscaled_images(self, txt_messages, close_btn, is_video):
        def write_message(message):
            txt_messages.config(state='normal')
            txt_messages.insert(tk.END, f'{message}\n')
            txt_messages.config(state='disabled')
            txt_messages.see(tk.END)
        
        index = self.footer.current_card_index()
        card = self.footer.get_current_card()
        video_buffer = []

        while True:
            self.conn.poll(timeout=None)
            message = self.conn.recv()

            if isinstance(message, Image.Image):
                output_image = ImageTk.PhotoImage(message)
                card.image['output'] = output_image

                if not is_video:
                    # Is image
                    # Update card with output
                    self.footer.update_card(card, index)
                    self.work_area.update_image(card)
                else:
                    # Is video
                    image = np.array(ImageTk.getimage(output_image))  # PIL to opencv
                    video_buffer.append(image)
                    
            elif message == 'done':
                if is_video:
                    # Is video
                    # Save video
                    fps = card.fps
                    filename = card.image['path'].split('/')[-1]  # Remove path
                    filename = filename.split('.')[0]  # Remove extension
                    extension = 'mp4'
                    filepath = os.path.join(self.output_folder, f'{filename}_upscaled_.{extension}')

                    start = int(self.control_panel.start_entry.get())
                    end = int(self.control_panel.end_entry.get())
                    audio = AudioFileClip(card.image['path']).subclip(start / fps, end / fps)

                    write_message('Saving video:')
                    write_message(filepath)

                    final = ImageSequenceClip(video_buffer, fps=fps).set_audio(audio)
                    final.write_videofile(filepath, fps=fps)

                break
            else:
                write_message(message)

        write_message('Done!')
        close_btn.config(text='Close', state='normal')
        if self.footer.get_current_card().is_image:
            self.control_panel.btn_save.pack(side=tk.BOTTOM, pady=(0, 15))


if __name__ == '__main__':
    torch.multiprocessing.set_start_method('spawn')

    # Comunications between processes
    ui_conn, ai_conn = torch.multiprocessing.Pipe(duplex=True)

    # UPSCALING PROCESS
    upscaling_daemon = torch.multiprocessing.Process(target=upscale_process, args=(ai_conn,), daemon=True)
    upscaling_daemon.start()
    
    # APP
    root = tk.Tk()

    # Styles
    root.tk.call('source', 'azure.tcl')
    root.tk.call('set_theme', 'dark')

    MainApplication(root, ui_conn).pack(side='top', fill='both', expand=True)
    root.mainloop()
