from simulation import PSNR
import pywt
import sys, os

if __name__ == '__main__':
    LIB_PATH = os.path.dirname(__file__)
    img0 = os.path.join(LIB_PATH,"whale_128.bmp")
    img1 = os.path.join(LIB_PATH,"134.bmp")
    img2 = os.path.join(LIB_PATH,"whale_reconstruct_6.jpg") 
    img3 = os.path.join(LIB_PATH,"whale_reconstruct_1.jpg")
    psnr = PSNR(img2,img3)
    print(psnr)
