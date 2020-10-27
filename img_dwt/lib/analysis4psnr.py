import sys,os
import pywt
import numpy as np
from PIL import Image
from math import log10


def load_img(path):
    try:
        return Image.open(path)
    except IOError:
        return None

def PSNR(img0, img1):
    Q = 255
    mse = MSE_RGB(img0, img1)
    psnr = 10 * log10(Q * Q / mse)
    return psnr

def MSE_RGB(img0, img1):
    I0 = load_img(img0)
    I1 = load_img(img1)
    (width, height) = I0.size
    rgb0 = np.array(I0).transpose(1, 2, 0).astype(float)
    rgb1 = np.array(I1).transpose(1, 2, 0).astype(float)
    mse = sum(sum(sum((rgb0 - rgb1) ** 2))) / (width * height * 3)
    return mse

if __name__ == '__main__':
    picture_path = str(sys.argv[1])
    LIB_PATH = os.path.dirname(__file__)
    img_yuantu = os.path.join(LIB_PATH,"./whale_128.bmp")
    img_ceshi = os.path.join(LIB_PATH,"./fountain/tornadochannel/2_Jumps/Fri_Jul_26_10_55_59_2019/167.bmp")
    psnr = PSNR(img_yuantu,img_ceshi)
    print('PSNR = {}'.format(psnr))
