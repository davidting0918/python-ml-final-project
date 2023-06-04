import base64
from PIL import Image
from io import BytesIO
import numpy as np


def base64_to_image(base64_string, save_path):
    image_data = base64.b64decode(base64_string)
    image = Image.open(BytesIO(image_data))
    image.save(save_path, "PNG")


def create_rgba_from_file(path):
    lena_img = Image.open(path).convert('RGBA')
    xdim, ydim = lena_img.size

    img = np.empty((ydim, xdim), dtype=np.uint32)
    view = img.view(dtype=np.uint8).reshape((ydim, xdim, 4))
    view[:, :, :] = np.flipud(np.asarray(lena_img))

    dim = max(xdim, ydim)
    return img, xdim, ydim, dim
