import numpy as np
import math


def SPIHT_Encode(m, max_bits, block_size, level):
    '''
    % input:    m : input image in wavelet domain
    %           max_bits : maximum bits can be used
    %           block_size : image size
    %           level : wavelet decomposition level
    %
    % output:   out : bit stream
    '''
    #-----------   Initialization  -----------------
    bitctr = 0
    out = 2 * np.ones((1, max_bits))
    n_max = math.floor(math.log(abs(np.max(m)), 2))
    Bits_Header = 0
    Bits_LSP = 0
    Bits_LIP = 0
    Bits_LIS = 0
    #-----------   output bit stream header   ----------------
    # image size, number of bit plane, wavelet decomposition level should be
    # written as bit stream header.
    out[:, 0:3] = [m.shape[0], n_max, level]    #输出矩阵的行数
    bitctr = bitctr + 24
    index = 4
    Bits_Header = Bits_Header + 24
    # -----------   Initialize LIP, LSP, LIS   ----------------
    temp = []  #????
    bandsize = 2 ** (math.log(m.shape[0], 2) - level + 1)
    

