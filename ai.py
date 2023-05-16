import torch
import os
import numpy as np
import cv2
import time

from models.network_rrdbnet import RRDBNet as net
from utils import uint2tensor4, tensor2uint

from PIL import Image


def upscale_process(conn):
    if not os.path.isdir('./outputs'):
        os.mkdir('./outputs')

    model = None
    gpu_id = None
    
    while True:
        conn.poll(timeout=None)
        new_model, new_gpu_id, filepath, images = conn.recv()

        if model != new_model or gpu_id != new_gpu_id:
            model, gpu_id = new_model, new_gpu_id

            # Send info
            conn.send(f'Pytorch version: {torch.__version__}')
            conn.send(f'Cuda version: {torch.version.cuda}')
            conn.send(f'Cudnn version: {torch.backends.cudnn.version()}')

            model_name = model
            sf = 4

            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            
            conn.send(f'Running on: {device}')

            if model_name in ['BSRGANx2']:
                sf = 2

            conn.send(f'Scale factor: {sf}')
            conn.send(f'Model name: {model_name}')

            model_path = os.path.join('model_zoo', model_name+'.pth')  # set model path

            if device == 'cuda':
                torch.cuda.set_device(gpu_id)  # set GPU ID
                torch.cuda.empty_cache()
                conn.send(f'GPU ID: {torch.cuda.current_device()}')

            # --------------------------------
            # define network and load model
            # --------------------------------
            model = net(in_nc=3, out_nc=3, nf=64, nb=23, gc=32, sf=sf)  # define network
            model.load_state_dict(torch.load(model_path), strict=True)
            model.eval()
            
            model = model.to(device)

        with torch.no_grad():
            len_images = len(images)
            video = True if len_images > 1 else False

            for i, image in enumerate(images):
                if i == 0:
                    conn.send(f'Upscaling: {filepath.split("/")[-1]}')
                
                if video:
                    conn.send(f'Upscaling frame: {i + 1} of {len_images} ({round(((i + 1) * 100) / len_images)}%)')

                torch.cuda.empty_cache()

                # Pil to cv2
                img_L = np.array(image)
                img_L = cv2.cvtColor(img_L, cv2.COLOR_RGB2BGR)
                input_img = img_L.copy()
                img_L = uint2tensor4(img_L)

                img_L = img_L.to(device)

                # Model predict
                img_E = model(img_L)
                img_E = tensor2uint(img_E)

                # Image is upscaled, need to resize
                img_E = cv2.resize(img_E, (input_img.shape[1], input_img.shape[0]), interpolation=cv2.INTER_LINEAR)
                
                # cv2 to pil & output image as ImageTk
                output = Image.fromarray(cv2.cvtColor(img_E, cv2.COLOR_BGR2RGB))

                conn.send(output)
            conn.send('done')
