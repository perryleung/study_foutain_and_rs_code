# _*_ coding=utf-8 _*_ 
from __future__ import print_function


from unireedsolomon import rs
from math import ceil, log
import numpy as np
import struct, bitarray
from builtins import chr
import six
import os

LIB_PATH = os.path.dirname(__file__)
DOC_PATH = os.path.join(LIB_PATH, '../doc')
SIM_PATH = os.path.join(LIB_PATH, '../simulation')
PRO_PATH = os.path.join(SIM_PATH, 'processing')

RS_FILE = "timg.jpg.rs"
RE_CONTRUCT_IMAGE = "timg_recontruct.jpg"
PACKET_SIZE = 73

WHALE_128_JPG = os.path.join(DOC_PATH, "whale_128.jpg")
TWINS_256_JPG = os.path.join(DOC_PATH, "twins_256.jpg")
FISH_128_JGP = os.path.join( DOC_PATH, "undwer_128.jpg")

def n_k_s_to_image(image_file, packet_size):

    s = packet_size
    with open(image_file, 'rb') as f:
        image_contain = f.read()
    k = int(ceil((len(image_contain) + 8) / float(packet_size)))
    n = int(2 ** ceil(log(k) / log(2)) - 1)
    print("n,k,and packet_size:")
    print(n, k, packet_size)
    bits_n = format(n, "016b")
    bits_k = format(k, "016b")
    bits_s = format(packet_size, "032b")
    byte_n = bitarray.bitarray(bits_n).tobytes()
    byte_k = bitarray.bitarray(bits_k).tobytes()
    byte_s = bitarray.bitarray(bits_s).tobytes()
   
    image_contain = byte_n + byte_k + byte_s + image_contain 
    return n, k, packet_size, image_contain 

def n_k_s_from_image(image_file):
    with open(image_file, 'rb') as f:
        image_contain = f.read()
    n_bytes = image_contain[0:2]
    k_bytes = image_contain[2:4]
    s_bytes = image_contain[4:8]
    image_contain = image_contain[8:]

    byte_factory = bitarray.bitarray(endian='big')
    byte_factory.frombytes(n_bytes)
    n_bits = byte_factory.to01()
    n = int(n_bits, base=2)

    byte_factory = bitarray.bitarray(endian='big')
    byte_factory.frombytes(k_bytes)
    k_bits = byte_factory.to01()
    k = int(k_bits, base=2)

    byte_factory = bitarray.bitarray(endian='big')
    byte_factory.frombytes(s_bytes)
    s_bits = byte_factory.to01()
    s = int(s_bits, base=2)

    return n, k, s, image_contain


    

def rs_encode_image(image_file, packet_size):
    '''
    读取文件，按 packet_size大小划分为待编码块
    按行排列，
    按纵向进行RS编码，增加冗余的编码数据块

                  packet_size 
    -------------------------------------------
    | |              图像文件                 |
RS  -------------------------------------------
    | |              图像文件                 |
    -------------------------------------------
编  | |              图像文件                 |
    -------------------------------------------
    | |              图像文件                 |
码  -------------------------------------------
    | |              图像文件                 |
    -------------------------------------------
块  |*|**************冗余编码*****************|
    -------------------------------------------
    |*|**************冗余编码*****************|
    -------------------------------------------

    '''
    n, k, _, image_contain = n_k_s_to_image(image_file, packet_size)
    # with open(image_file, 'rb') as f:
        # image_contain = f.read()
    #k = 9
    #n = 16
    print("k,n:")
    print(k, n)
    output_rs_file = image_file + '.rs'
    fout = open(output_rs_file, 'wb')
    mat = []
    for i in range(k):
        if(len(image_contain) > (i+1) * packet_size):
            if six.PY3:
                mat_temp = list(image_contain[i * packet_size: (i+1) * packet_size])
            else:
                mat_temp = [ord(ii) for ii in list(image_contain[i * packet_size: (i+1) * packet_size])]
            mat.append(mat_temp)
        else:
            empty = [0 for ii in range(packet_size)]
            if six.PY3:
                if(len(image_contain) > i * packet_size):
                    empty[:(len(image_contain) - i * packet_size)] = \
                        list(image_contain[i * packet_size: len(image_contain)])
            else:
                if(len(image_contain) > i * packet_size):
                    empty[:(len(image_contain) - i * packet_size)] = \
                        [ord(ii) for ii in list(image_contain[i * packet_size: len(image_contain)])]
            mat.append(empty)
    for i in range(n-k):
        mat.append([0 for ii in range(packet_size)])

    mat_arr_orig = np.array(mat)
    mat_arr_code = mat_arr_orig
    print("size of original mat")
    print(mat_arr_orig.shape)
    print(mat_arr_orig)
    

    coder = rs.RSCoder(n, k)
    for i in range(packet_size):
        #  source = bytes([int(ii) for ii in mat_arr_orig[:k, i]])
        source = ''.join([chr(ii) for ii in mat_arr_orig[:k, i]])
        code_word = list(coder.encode(source))
        mat_arr_code[:, i] = [ord(ii) for ii in code_word]

    out_image_contain = b''
    for line in mat_arr_code:
        if six.PY3:
            # print(list(line))
            out_bytes = b''.join([struct.pack("B", ii) for ii in list(line)])
        elif six.PY2:
            # print(list(line))
            out_bytes = b''.join([struct.pack("B", int(ii)) for ii in list(line)])
        out_image_contain += out_bytes
        fout.write(out_bytes)
    fout.close()           
    return output_rs_file

def count_errpos(recv_packet, n):
    errpos = []
    for i in range(n):
        if recv_packet.count(i) == 0:
            errpos.append(i)
    return errpos


def rs_decode_image(rs_file, recv_packet):
    # with open(rs_file, 'rb') as f:
        # rs_contain = f.read()
    n, k, s, rs_contain = n_k_s_from_image(rs_file)
    errpos = count_errpos(recv_packet, n)
    print("errpos is : {}".format(errpos))
    packet_size = int(s)

    out_file_name = os.path.basename(rs_file)
    out_file_dir = os.path.dirname(rs_file)
    out_name = os.path.join(out_file_dir, out_file_name[:-3].replace(".jpg", "_re.jpg"))

    fout = open(out_name, 'wb')
    print("re image save : {}".format(out_name))

    mat = []
    for i in range(n):
        if(len(rs_contain) >= (i+1) * packet_size):
            if six.PY3:
                mat_temp = list(rs_contain[i * packet_size: (i+1) * packet_size])
            else:
                mat_temp = [ord(ii) for ii in list(rs_contain[i * packet_size: (i+1) * packet_size])]
            mat.append(mat_temp)
        else:
            empty = [0 for ii in range(packet_size)]
            if len(rs_contain) > i * packet_size:
                if six.PY3:
                    empty[:(len(rs_contain) - i * packet_size)] = \
                            list(rs_contain[i * packet_size: len(rs_contain)])
                else:
                    empty[:(len(rs_contain) - i * packet_size)] = \
                            [ord(ii) for ii in list(rs_contain[i * packet_size: len(rs_contain)])]

            mat.append(empty)
    mat_arr_code = np.array(mat)            
    mat_arr_orig = mat_arr_code[:k, :]
    print("mat code is:")
    print(mat_arr_code)
    print("size of mat code is:")
    print(mat_arr_code.shape)

    coder = rs.RSCoder(n, k)
    try:
        for i in range(packet_size):
            code_word = b''.join(struct.pack("B", ii) for ii in mat_arr_code[:, i]) # bytes
            source = coder.decode(code_word, erasures_pos = errpos)[0] # list str
            source = [ii for ii in source]
            if len(source) < k:
                mat_arr_orig[0:(k-len(source)), i] = [0 for ii in range(k-len(source))]
                mat_arr_orig[(k-len(source)):, i] = [ord(ii) for ii in source]
            else:
                mat_arr_orig[:, i] = [ord(ii) for ii in source]
    except Exception, e:
        print(e.message)

    out_image_contain = b''
    
    # out_bytes = b''.join([struct.pack("B", ii) for ii in mat_arr_orig[0, 4:]])
    # fout.write(out_bytes)
    # for line in mat_arr_orig[1:, :]:
    for line in mat_arr_orig[:, :]:
        out_bytes = b''.join([struct.pack("B", ii) for ii in list(line)])
        out_image_contain += out_bytes
        fout.write(out_bytes)
    fout.close()        
    return out_name
    # return mat_arr_code, mat_arr_orig, rs_contain, out_image_contain


if __name__ == "__main__":
    # img = FISH_128_JGP
    img = WHALE_128_JPG
    print(rs_encode_image(img, PACKET_SIZE))
    print(rs_decode_image(img +".rs"))

    # n_k_s_to_image(img, PACKET_SIZE)

