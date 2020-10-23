# _*_ coding=utf-8 _*_ 
from __future__ import print_function
import sys, os
import numpy as np
import math
import pywt
import struct
import bitarray
import matlab.engine
from PIL import Image
import time
from tqdm import tqdm
import pandas as pd
sys.path.append('.')
from dwt_lib import load_img

LIB_PATH = os.path.dirname(__file__)
DOC_PATH = os.path.join(LIB_PATH, '../doc')
SIM_PATH = os.path.join(LIB_PATH, '../simulation')
PRO_PATH = os.path.join(SIM_PATH, 'processing')

LEAN_IMG = os.path.join(DOC_PATH, 'lena.png')
ORCA_IMG = os.path.join(DOC_PATH, 'orca.jpg')
TIMG_IMG = os.path.join(DOC_PATH, 'timg.jpg')
WHALE_IMG= os.path.join(DOC_PATH, 'whale_512.bmp')
OUT_BIN = os.path.join(DOC_PATH, 'out_whale.bin')
OUT_BIN_R = os.path.join(DOC_PATH, 'out_whale_r.bin')
OUT_BIN_G = os.path.join(DOC_PATH, 'out_whale_g.bin')
OUT_BIN_B = os.path.join(DOC_PATH, 'out_whale_b.bin')
LEAN_IMG_NEW = os.path.join(DOC_PATH, 'lena512_reconstruct.bmp')
TIMG_IMG_NEW = os.path.join(DOC_PATH, 'timg_reconstruct.jpg')
WHALE_IMG_NEW = os.path.join(DOC_PATH, 'whale_reconstruct.bmp')
WHALE_IMG_128 = os.path.join(DOC_PATH, 'whale_128.bmp')

BIOR = 'bior4.4'
MODE = 'periodization'
LEVEL = 3


def code_to_file(in_bits_array, file_name=OUT_BIN, add_to=None):
    '''
    将二进制编码写入文件
    in_bits_array : matlab type array, shape[1, n], 每一次是一个通道的SPIHT的二进制编码
    file_name : write to file, 写入的文件名，传入文件名，写完后返回这个文件名
    add_to : 猜测是计算每个通道可以分到的字节数
    '''
    img_enc = in_bits_array
    bitstream = ''
    info_array = []
    for index, i in enumerate(img_enc):
        if index == 0:
            bitstream += format(int(i), "016b")
            pass
        elif index == 1:
            bitstream += format(int(i), "08b")
            pass
        elif index == 2:
            bitstream += format(int(i), "08b")
            pass
        if i == 0 or i == 1:
            bitstream += str(i).replace('.0', '')
        elif i == 2:
            pass
        else:
            pass
            #  info_array.append(i)
            #  bitstream += (bin(int(i)).replace('0b', '') + ',')
    if (add_to is not None) and (add_to - len(bitstream) % add_to > 0):
        gap = int(add_to - len(bitstream) % add_to)
        bitstream += format(0, "0"+str(gap)+"b")
    print('bitstream len : ', len(bitstream))        
    fout = open(file_name, 'wb')
    bits = bitarray.bitarray(bitstream)
    bits.tofile(fout)
    fout.close()
    return file_name

def file_to_code(file_name=OUT_BIN):
    '''
    从文件中读取内容，转化为二进制编码
    read code from file
    '''
    fin = open(file_name, 'rb')
    read_bits = bitarray.bitarray()
    read_bits.fromfile(fin)
    fin.close()
    return read_bits

def func_DWT(I, level=LEVEL, wavelet=BIOR, mode=MODE):
    '''
    后面三个参数在这个文件已经设置了默认值，只要导入图像I即可
    根据输入参数的小波变换等级，小波类型，变换模型将图像 I 转化为小波参数，返回小波参数
    I should be size of 2^n * 2^n
    C 列表好像是没有用的？
    '''
    [width, height] = I.shape

    C = []
    #  I_W size : width, height
    I_W = np.empty((width, height)) #小波系数矩阵大小跟图片一样
    current_size = 0
    for i in range(level):      # i = 0、1、2
        [I, [LH, HL, HH]]= pywt.dwt2(I, wavelet, mode)
        current_size = I.shape[0]

        I_W[0:current_size , current_size:2*current_size] = LH
        I_W[current_size:2*current_size , 0:current_size] = HL
        I_W[current_size:2*current_size , current_size:2*current_size] = HH

        C = list(LH.flatten()) + list(HL.flatten()) + list(HH.flatten()) + C

    I_W[:current_size, :current_size] = I
    C = list(I.flatten()) + C
    return I_W  #   返回小波系数矩阵

def func_IDWT(I_W, level=LEVEL, wavelet=BIOR, mode=MODE):
    '''
    小波逆变换，将输入的小波参数，根据小波变换等级，小波类型，变换模式将小波参数逆变换为原图像
    IDWT
    I_W : numpy array
    level : wavelet level
    wavelet : wavelet type
    mode : wavelet mode
    '''
    width = I_W.shape[0]
    height = I_W.shape[0]
    S = [-1] * level
    current_size = width
    for i in range(level):
        current_size = pywt.dwt_coeff_len(current_size, pywt.Wavelet(BIOR), MODE)
        S[i] = current_size
    S.reverse()
    for current_size in S:
        #  current_size = S[i]
        LL = I_W[0:current_size, 0:current_size]
        LH = I_W[0:current_size, current_size:2*current_size]
        HL = I_W[current_size:2*current_size, 0:current_size]
        HH = I_W[current_size:2*current_size, current_size:2*current_size]
        coeffs = [LL, [LH, HL, HH]]
        I_W[0:2*current_size, 0:2*current_size] = pywt.idwt2(coeffs, wavelet, MODE)
    return I_W

def spiht_encode(I_W, eng=None):
    '''
    SPIHT 压缩编码，将输入的小波系数，压缩为二进制编码01010101， 二进制编码中包含压缩使用到的参数, 返回二进制编码
    I_W : 2D array, image DWT code, 就是小波系数矩阵
    eng : matlab engine
    return : matlab array, spiht code
    '''
    if eng == None:
        print("start a matlab engine")
        eng = matlab.engine.start_matlab()
        eng.addpath(LIB_PATH)   #是要告诉matlab用哪里的程序文件
    max_bits = I_W.shape[0] * I_W.shape[1]
    block_size = I_W.shape[0] * I_W.shape[1]
    level = LEVEL
    m = matlab.double([list(ii) for ii in I_W])
    out_bits = eng.func_MySPIHT_Enc(m, max_bits, block_size, level)
    return out_bits[0]  # 输出压缩二进制编码

def spiht_decode(read_bits, eng=None):
    '''
    SPIHT 解码，将输入的二进制编码，转化为小波系数，二进制编码中含有解码需要的参数
    read_bits : maybe is array
    eng : matlab engine
    return : np.array, image DWT code
    '''
    if eng == None:
        print("start a matlab engine")
        eng = matlab.engine.start_matlab()
        eng.addpath(LIB_PATH)
    img_size = float(int(read_bits[0:16].to01(), 2))
    n_max = float(int(read_bits[16:24].to01(), 2))
    level = float(int(read_bits[24:32].to01(), 2))
    img_code = [img_size, n_max, level]
    img_code.extend(list(read_bits)[32:])
    img_code = matlab.mlarray.double(img_code)
    m = eng.func_SPIHT_Dec(img_code)
    return np.array(m)

def PSNR(img0, img1):
    """
    计算两个图像的PSNR值
    img0 和 img1 的大小需要一样
    """
    Q = 255
    mse = MSE_RGB(img0, img1)
    psnr = 10 * math.log10(Q * Q / mse)
    return psnr

def MSE_RGB(img0, img1):
    '''
    计算两张图片的MSE,
    img0 和 img1 的大小需要一样
    '''
    I0 = load_img(img0)
    I1 = load_img(img1)
    (width, height) = I0.size
    rgb0 = np.array(I0).transpose(1, 2, 0).astype(float)
    rgb1 = np.array(I1).transpose(1, 2, 0).astype(float)
    mse = sum(sum(sum((rgb0 - rgb1) ** 2)))
    return mse

def main():
    # start matlab engine
    print("start a matlab engine")
    eng = matlab.engine.start_matlab()
    eng.addpath(LIB_PATH)
    #  image to mat
    # I = load_img(WHALE_IMG)
    I = load_img(WHALE_IMG_128)
    #  I = load_img(LEAN_IMG)
    #  I = load_img(ORCA_IMG)
    (width, height) = I.size
    mat_r = np.empty((width, height))
    mat_g = np.empty((width, height))
    mat_b = np.empty((width, height))
    for i in range(width):
        for j in range(height):
            [r, g, b] = I.getpixel((i, j))
            mat_r[i, j] = r 
            mat_g[i, j] = g 
            mat_b[i, j] = b 
    #  encode part
    print("load image done, image shape : (", mat_r.shape[0], ",", mat_r.shape[1], ")")
    I_W_r = func_DWT(mat_r, LEVEL)
    I_W_g = func_DWT(mat_g, LEVEL)
    I_W_b = func_DWT(mat_b, LEVEL)
    print("image 2d DWT done, level : ", LEVEL)
    out_bits_r = spiht_encode(I_W_r, eng)
    out_bits_g = spiht_encode(I_W_g, eng)
    out_bits_b = spiht_encode(I_W_b, eng)
    print("spiht encode done , out bits len : ", len(out_bits_r))
    out_file_r = code_to_file(out_bits_r, OUT_BIN_R)
    out_file_g = code_to_file(out_bits_g, OUT_BIN_G)
    out_file_b = code_to_file(out_bits_b, OUT_BIN_B)
    
    #decode part
    read_bits_r = file_to_code(out_file_r)
    read_bits_g = file_to_code(out_file_g)
    read_bits_b = file_to_code(out_file_b)
    print("read bits from file, bits len : ", len(read_bits_r))
    I_W_decode_r = spiht_decode(read_bits_r, eng)
    I_W_decode_g = spiht_decode(read_bits_g, eng)
    I_W_decode_b = spiht_decode(read_bits_b, eng)

    I_W_re_r = func_IDWT(I_W_decode_r, LEVEL)
    I_W_re_g = func_IDWT(I_W_decode_g, LEVEL)
    I_W_re_b = func_IDWT(I_W_decode_b, LEVEL)
    dwt_img = Image.new('RGB', (width, height), (0, 0, 20))
    for i in range(width):
        for j in range(height):
            R = I_W_re_r[i, j]
            G = I_W_re_g[i, j]
            B = I_W_re_b[i, j]
            new_value = (int(R), int(G), int(B))
            dwt_img.putpixel((i, j), new_value)
    dwt_img.save(WHALE_IMG_NEW)            
    return I_W_r, out_bits_r, read_bits_r

def progressive_test():
    """
    测试渐进传输的效果，将图像的渐进编码写入文件，分别读取文件的部分用于恢复图像，看是否会有从模糊到清晰的过程
    """
    print("start a matlab engine")
    eng = matlab.engine.start_matlab()
    eng.addpath(LIB_PATH)
    width = 128
    height = 128

    out_file_r = OUT_BIN_R
    out_file_g = OUT_BIN_G
    out_file_b = OUT_BIN_B

    part_num = 100
    out_file_size = len(file_to_code(out_file_r))
    psnr_list = [0] * part_num
    file_list = [' '] * part_num
    size_list = [0] * part_num

    tap = 0
    test_res_dir = os.path.join(PRO_PATH,time.asctime().replace(' ', '_').replace(':', '_'))
    os.mkdir(test_res_dir)
    for k in tqdm([ii + 1 for ii in range(part_num)]):
        read_size = int(float(k) / part_num * out_file_size)
        read_bits_r = file_to_code(out_file_r)[:read_size]
        read_bits_g = file_to_code(out_file_g)[:read_size]
        read_bits_b = file_to_code(out_file_b)[:read_size]
        #  print("read bits from file, bits len : ", len(read_bits_r))
        try : 
            I_W_decode_r = spiht_decode(read_bits_r, eng)
            I_W_decode_g = spiht_decode(read_bits_g, eng)
            I_W_decode_b = spiht_decode(read_bits_b, eng)

            I_W_re_r = func_IDWT(I_W_decode_r, LEVEL)
            I_W_re_g = func_IDWT(I_W_decode_g, LEVEL)
            I_W_re_b = func_IDWT(I_W_decode_b, LEVEL)
            dwt_img = Image.new('RGB', (width, height), (0, 0, 20))
            for i in range(width):
                for j in range(height):
                    R = I_W_re_r[i, j]
                    G = I_W_re_g[i, j]
                    B = I_W_re_b[i, j]
                    new_value = (int(R), int(G), int(B))
                    dwt_img.putpixel((i, j), new_value)
            temp_name = os.path.join(test_res_dir, 'whale_' + str(k)+'_'+str(part_num)+".bmp")
            dwt_img.save(os.path.join(temp_name))
            psnr_list[tap] = PSNR(WHALE_IMG_128, temp_name)
            file_list[tap] = temp_name
            size_list[tap] = float(k) / part_num
        except:
            print('spiht decode error !!')
        tap += 1
    res = pd.DataFrame({'psnr':psnr_list, 
        'size':size_list, 
        'file_list':file_list})
    res.to_csv(os.path.join(test_res_dir, 'res.csv'))


if __name__ == '__main__':
    start = time.clock()
    #  I_W, out_bits, read_bits = main()
#      psnr = PSNR(WHALE_IMG, WHALE_IMG_NEW)
    #  print 'psnr : ', psnr
    #  print 'mse : ', MSE_RGB(WHALE_IMG, WHALE_IMG_NEW)
    progressive_test()
    # main()
