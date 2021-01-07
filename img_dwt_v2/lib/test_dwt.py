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
from math import ceil
sys.path.append('.')
from dwt_lib import load_img
from spiht_dwt_lib import func_DWT, func_IDWT, spiht_encode, spiht_decode
from spiht_dwt_lib import code_to_file, file_to_code

LIB_PATH = os.path.dirname(__file__)
DOC_PATH = os.path.join(LIB_PATH, '../doc')

WHALE_IMG_128 = os.path.join(DOC_PATH, 'whale128.bmp')
img_path = WHALE_IMG_128

BIOR = 'bior4.4'
MODE = 'periodization'
LEVEL = 3

eng = matlab.engine.start_matlab()
eng.addpath(LIB_PATH)

chunk_size = 60

def _321(file_list, each_chunk_size=2500):
        '''
        将三个文件和并为一个文件
        file_list : 存储了三个通道编码文件的列表
        each_chunk_size : 每个通道的平均码长
        最后返回的m应该就是要传送的数据
        '''
        #  m_list = [open(ii, 'r').read() for ii in file_list]
        m_list = []
        """ 修改 """
        """ m_list.append(open(file_list[0], 'r').read())
        m_list.append(open(file_list[1], 'r').read())
        m_list.append(open(file_list[2], 'r').read()) """
        m_list.append(file_to_code(file_list[0]))
        m_list.append(file_to_code(file_list[1]))
        m_list.append(file_to_code(file_list[2]))

        #  a = [print(len(ii)) for ii in m_list]
        m_bytes = b''
        print('r bitstream len : ', len(m_list[0]))
        print('g bitstream len : ', len(m_list[1]))
        print('b bitstream len : ', len(m_list[2]))
        print('rbg bitstream len : ', len(m_list))
        print('data bytes should be : ', len(m_list) / 8)
        for i in range(int(ceil(len(m_list[0]) / float(each_chunk_size)))):
            start = i * each_chunk_size
            end = min((i + 1) * each_chunk_size, len(m_list[0]))
            #  m += ''.join([ii[start:end] for ii in m_list])
            m_bytes += m_list[0][start: end].toBytes()
            m_bytes += m_list[1][start: end].toBytes()
            m_bytes += m_list[2][start: end].toBytes()
            #  print(len(m))            
        return m_bytes, each_chunk_size * 3

def coding_test():
    temp_file = img_path
    rgb_list = ['r', 'g', 'b']
    temp_file_list = [temp_file + '_' + ii for ii in rgb_list]  #3个通道rgb名字而非内容的列表
    print('process imgage: {:s}'.format(img_path))
    img = load_img(img_path)           #加载图像
    (width, height) = img.size              #图像大小，二维的维度，width和height不用在意
    mat_r = np.empty((width, height))       #创建三个通道的数据阵
    mat_g = np.empty((width, height))
    mat_b = np.empty((width, height))
    for i in range(width):
        for j in range(height):
            [r, g, b] = img.getpixel((i, j))
            mat_r[i, j] = r #分别读入三个通道的像素值
            mat_g[i, j] = g #原来每个像素点都包含ri+gi+bi
            mat_b[i, j] = b #现在是将每个像素的rgb通道分开
    img_mat = [mat_r, mat_g, mat_b]    #rgb三个通道的列表
    dwt_coeff = [func_DWT(ii) for ii in img_mat]  #按顺序处理rgb数据，然后3个通道的生成小波系数矩阵的列表
    spiht_bits = [spiht_encode(ii, eng) for ii in dwt_coeff] #3个通道列表分别进行多级树集合分裂编码
                                                             #输出3个通道的二进制编码列表
    #  trick 
    a =[code_to_file(spiht_bits[ii],
        temp_file_list[ii],
        add_to=chunk_size / 3 * 8) 
            for ii in range(len(rgb_list))]  #a是存储了3个通道SPIHT编码的文件名字，只是个工具变量，重点是temp_file_list列表在_321
    
    m, _chunk_size = _321(temp_file_list, each_chunk_size=chunk_size / 3)
    print("len(m) = ", len(m))


if __name__ == '__main__':
    print("test begin!")
    coding_test()
