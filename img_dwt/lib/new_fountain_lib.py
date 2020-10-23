from __future__ import print_function
from math import ceil, log
import sys, os
import random
import json
import bitarray
import numpy as np
from time import sleep
import logging

LIB_PATH = os.path.dirname(__file__)
DOC_PATH = os.path.join(LIB_PATH, '../doc')
SIM_PATH = os.path.join(LIB_PATH, '../simulation')

logging.basicConfig(level=logging.INFO, 
        format="%(asctime)s %(filename)s:%(lineno)s %(levelname)s-%(message)s",)

def charN(str, N):
    if N < len(str):
        return str[N]
    return 'X'

def xor(str1, str2):
    length = max(len(str1), len(str2))
    return ''.join(chr(ord(charN(str1, i)) ^ ord(charN(str2, i))) for i in xrange(length))

def randChunkNums(num_chunks):
    size = random.randint(1, min(5, num_chunks))
    return random.sample(xrange(num_chunks), size)

def soliton(k):
    d = [ii + 1 for ii in range(k)]
    d_f = [1.0 / k if ii == 1 else 1.0 / (ii * (ii - 1)) for ii in d]
    while 1:
        yield np.random.choice(d, 1, False, d_f)[0]

def robust_soliton(k, c=0.03, delta=0.05):
    d = [ii + 1 for ii in range(k)]
    soliton_d_f = [1.0 / k if ii == 1 else 1.0 / (ii * (ii - 1)) for ii in d]
    S = c * log(k / delta) * (k ** 0.5)
    interval_0 = [ii + 1 for ii in list(range(int(round(k / S)) - 1))]
    interval_1 = [int(round(k / S))]
    tau = [S / (k * dd) if dd in interval_0 
            else S / float(k) * log(S / delta) if dd in interval_1
            else 0 for dd in d]
    Z = sum([soliton_d_f[ii] + tau[ii] for ii in range(k)])
    u_d_f = [(soliton_d_f[ii] + tau[ii]) / Z for ii in range(k)]

    while True :
        yield np.random.choice(d, 1, False, u_d_f)[0]

class Droplet:
    def __init__(self, data, seed, num_chunks):
        self.data = data
        self.seed = seed
        self.num_chunks = num_chunks

    def chunkNums(self):
        random.seed(self.seed)
        np.random.seed(self.seed)
        return randChunkNums(self.num_chunks)

    def toString(self):
        return json.dumps(
            {
                'seed': self.seed,
                'num_chunks': self.num_chunks,
                'data':self.data
            }
        )
    
    def toBytes(self):
        num_chunks_bits = format(int(self.num_chunks), "016b")
        seed_bits = format(int(self.seed), "032b")
        logging.info('fountain num_chunks : {}, seed : {}'.format(self.num_chunks, self.seed))
        return bitarray.bitarray(num_chunks_bits + seed_bits).tobytes() + self.data
    
class EW_Droplet(Droplet):
    def __init__(self, data, seed, num_chunks, w1_size=0.1, w1_pro=0.084):
        Droplet.__init__(self, data, seed, num_chunks)
        m = ' ' * num_chunks * len(data)
        self.ower = EW_Fountain(m, len(self.data), w1_size=w1_size, w1_pro=w1_pro)
    
    def chunkNums(self):
        random.seed(self.seed)
        np.random.seed(self.seed)
        return self.ower.EW_RandChunkNums(self.num_chunks)
    
class Fountain(object):
    def __init__(self, data, chunk_size=1000, seed=None):
        self.data = data
        self.chunk_size = chunk_size
        self.num_chunks = int(ceil(len(data) / float(chunk_size)))
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        self.show_info()
    
    def show_info(self):
        logging.info('Fountain info')
        logging.info('data len : {}'.format(len(self.data)))
        logging.info('chunk_size : {}'.format(self.chunk_size))
        logging.info('num_chunks : {}'.format(self.num_chunks))
    
    def updateSeed(self):
        self.seed = random.randint(0, 2 ** 31 - 1)
        random.seed(self.seed)
        np.random.seed(self.seed)
    
    def chunk(self, num):
        start = self.chunk_size * num
        end = min(self.chunk_size * (num + 1), len(self.data))
        return self.data[start:end]

    def droplet(self):
        self.updateSeed()
        chunk_nums = randChunkNums(self.num_chunks)
        logging.info("seed : {}".format(self.seed))
        logging.info("send chunk list : {}".format(chunk_nums))
        data = None
        for num in chunk_nums:
            if data is None:
                data = self.chunk(num)
            else:
                data = xor(data, self.chunk(num))
        return Droplet(data, self.seed, self.num_chunks)
    
class EW_Fountain(Fountain):
    def __init__(self, data, chunk_size=50, seed=None, w1_size=0.1, w1_pro=0.084):
        Fountain.__init__(self, data, chunk_size=chunk_size, seed=None)
        logging.info("-----------------init EW_Fountain------------")
        self.w1_p = w1_size
        self.w1_pro = w1_pro
        self.windows_id_gen = self.windows_selection()
        self.w1_size = int(round(self.num_chunks * self.w1_p))
        self.w2_size = self.num_chunks
        self.w1_random_chunk_gen = robust_soliton(self.w1_size)
        self.w2_random_chunk_gen = robust_soliton(self.w2_size)

    def windows_selection(self):
        d = [1, 2]
        w1_p = self.w1_pro
        w_f = [w1_p, 1 - w1_p]
        while True:
            i = np.random.choice(d, 1, False, w_f)[0]
            yield i