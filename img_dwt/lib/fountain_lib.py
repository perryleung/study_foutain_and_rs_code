# _*_ coding=utf-8 _*_
from __future__ import print_function
from math import ceil, log
from degree_distribution_func import *
import sys, os
import random
import json
import bitarray
import numpy as np
from time import sleep
import logging
#  from matplotlib import pyplot as plt
#  plt.ion()
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
    '''
    按位运算str1, str2
    将 str1 和 str2 中每一个字符转为acsii 表中的编号，再将两个编号转为2进制按位异或运算
    ，最后返回异或运算的数字在ascii 表中的字符
    '''
    length = max(len(str1),len(str2))
    return ''.join(chr(ord(charN(str1,i)) ^ ord(charN(str2,i))) for i in xrange(length))

def randChunkNums(num_chunks):
    '''
    size 是每次选取的度数，这里选取的是一个度函数，size 分布是
    度函数的文章要在这里做, 这里的度函数是一个 5 到 K 的均匀分布
    num_chunks : int, 编码块总数量
    return : list, 被选中的编码块序号
    '''
    size = random.randint(1,min(5, num_chunks))
    # random.sample 是一个均匀分布的采样
    return random.sample(xrange(num_chunks), size)



class Droplet:
    ''' 储存随机数种子，并有一个计算本水滴中包含的数据块编码的方法'''
    def __init__(self, data, seed, num_chunks):
        self.data = data
        #  seed 随机数种子，用于随机产成 n 个数字放入num_chunks 列表中
        self.seed = seed
        #  num_chunks: int 编码块总数量
        self.num_chunks = num_chunks

    def chunkNums(self):
        random.seed(self.seed)
        np.random.seed(self.seed)
        return randChunkNums(self.num_chunks)

    def toString(self):
        return json.dumps(
            {
                'seed':self.seed,
                'num_chunks':self.num_chunks,
                'data':self.data
            })
    
    def toBytes(self):
        '''
        使用一个字节存储chunks_size,
        num_chunks int 度数，一个字节
        seed 随机数种子，两个字节
        返回的结构是一个字节加后面跟着2 * n 个字节，后续跟着数据（备注错了应该是1+2+data字节）
        '''
        num_chunks_bits = format(int(self.num_chunks), "016b")  # 单字节记录num_chunks
        seed_bits = format(int(self.seed), "032b")  # 双字节记录种子
        logging.info('fountain num_chunks : {}, seed : {}'.format(self.num_chunks, self.seed))
        return bitarray.bitarray(num_chunks_bits + seed_bits).tobytes() + self.data

class Fountain(object):
    def __init__(self, data, chunk_size=1000, seed=None):
        self.data = data
        self.chunk_size = chunk_size
        self.num_chunks = int(ceil(len(data) / float(chunk_size)))  #数据块数量
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)    # 种种子
        self.show_info()        # 打印信息

    def show_info(self):
        logging.info('Fountain info')
        logging.info('data len: {}'.format(len(self.data)))
        logging.info('chunk_size: {}'.format(self.chunk_size))
        logging.info('num_chunks: {}'.format(self.num_chunks))

    def droplet(self):
        '''
        开始编码
        Droplet编码函数，
        '''
        self.updateSeed()
        chunk_nums = randChunkNums(self.num_chunks)     # 随机拿几个数据包, list, 被选中的编码块序号
        logging.info("seed: {}".format(self.seed))
        logging.info("send chunk list: {}".format(chunk_nums))
        data = None
        for num in chunk_nums:  # 创建LT编码
            if data is None:
                data = self.chunk(num) # 迭代刚开始
            else:
                data = xor(data, self.chunk(num))

        return Droplet(data, self.seed, self.num_chunks)

    def chunk(self, num):
        start = self.chunk_size * num
        end = min(self.chunk_size * (num+1), len(self.data))
        return self.data[start:end]

    def updateSeed(self):
        self.seed = random.randint(0,2**31-1)
        random.seed(self.seed)
        np.random.seed(self.seed)

class EW_Fountain(Fountain):
    ''' 扩展窗喷泉码 '''
    def __init__(self, data,  chunk_size=50, seed=None, w1_size=0.1, w1_pro=0.084):
        Fountain.__init__(self, data, chunk_size=chunk_size, seed=None)
        logging.info("-----------------init EW_Fountain------------")
        self.w1_p=w1_size
        self.w1_pro=w1_pro
        self.windows_id_gen = self.windows_selection()          # 选择两种窗口中的其中之一
        self.w1_size = int(round(self.num_chunks * self.w1_p))  # 重要窗的规模大小，既可以容下多少个编码块
        #  self.w2_size = int(self.num_chunks - self.w1_size)   
        self.w2_size = self.num_chunks                          # 次要窗的规模大小
	#self.w1_random_chunk_gen = robust_soliton(self.w1_size),# 这个逗号是认真的 
        #self.w2_random_chunk_gen = robust_soliton(self.w2_size) # 返回的是度数，代表编码块个数
        #  logging.info('w1_size : ', self.w1_size)
        #self.w1_random_chunk_gen = robust_soliton(self.w1_size),# 这个逗号是认真的 
        #self.w2_random_chunk_gen = first_degree_distribution_func() # 返回的是度数，代表编码块个数
        #  logging.info('w1_size : ', self.w1_size)
        #self.w1_random_chunk_gen = robust_soliton(self.w1_size),# 这个逗号是认真的 
        #self.w2_random_chunk_gen = second_degree_distribution_func() # 返回的是度数，代表编码块个数
	#  logging.info('w1_size : ', self.w1_size)
        self.w1_random_chunk_gen = robust_soliton(self.w1_size),# 这个逗号是认真的 
        self.w2_random_chunk_gen = mrds_func(self.w2_size) # 返回的是度数，代表编码块个数
        #  logging.info('w2_size : ', self.w2_size)
        #self.w1_random_chunk_gen = robust_soliton(self.w1_size),# 这个逗号是认真的 
        #self.w2_random_chunk_gen = binary_exp_func(self.w2_size) # 返回的是度数，代表编码块个数
        #  logging.info('w1_size : ', self.w1_size)
        #self.w1_random_chunk_gen = robust_soliton(self.w1_size),# 这个逗号是认真的 
        #self.w2_random_chunk_gen = poisson_func(self.w2_size) # 返回的是度数，代表编码块个数
        #  logging.info('w1_size : ', self.w1_size)
    def droplet(self):
        self.updateSeed()
        chunk_list = self.EW_RandChunkNums(self.num_chunks)
        logging.info("send seed: {}\tnum_chunks: {}".format(self.seed, self.num_chunks))
        data = None
        for num in chunk_list:
            if data is None:
                data = self.chunk(num)
            else:
                data = xor(data, self.chunk(num))

        logging.info('send chunk_list : {}'.format(chunk_list))
        return EW_Droplet(data, self.seed, self.num_chunks)

    def EW_RandChunkNums(self, num_chunks):
        '''扩展窗的不同在这里'''
        window_id = self.windows_id_gen.next()
        if window_id == 1:
            size = self.w1_random_chunk_gen[0].next()
            return random.sample(xrange(self.w1_size), size)
        else:
            size = self.w2_random_chunk_gen.next()
            return [ii for ii in random.sample(xrange(self.w2_size), size)] 

    def windows_selection(self):
        '''以概率[{p:1, 1-p:2}返回选择的窗口'''
        d = [1, 2]
        w1_p = self.w1_pro
        w_f = [w1_p, 1-w1_p]    # 两种窗口的概率
        while True:
            i = np.random.choice(d, 1, False, w_f)[0]
            yield i
    def show_robust_soliton(self, N=10000):
        w1_stat = [0] * (self.w1_size + 1)
        w2_stat = [0] * (self.w2_size + 1)
        for i in range(N):
            w1_stat[self.w1_random_chunk_gen[0].next()] += 1
            w2_stat[self.w2_random_chunk_gen.next()] += 1
#          f = plt.figure()
        #  plt.plot(range(len(w1_stat)), [ii / float(10000) for ii in w1_stat])
        #  plt.show()
        #  f = plt.figure()
        #  plt.plot(range(len(w2_stat)), [ii / float(10000) for ii in w2_stat])
        #  plt.show()

class EW_Droplet(Droplet):
    '''扩展窗喷泉码专用水滴, 计算水滴使用的数据块列表'''
    def __init__(self, data, seed, num_chunks, w1_size=0.1, w1_pro=0.084):
        Droplet.__init__(self, data, seed, num_chunks)
        m = ' ' * num_chunks * len(data)
        #  self.ew_randChunkNums = EW_Fountain(m).EW_RandChunkNums
        self.ower = EW_Fountain(m, len(self.data), w1_size=w1_size, w1_pro=w1_pro)

    def chunkNums(self):
        random.seed(self.seed)
        np.random.seed(self.seed)
        return self.ower.EW_RandChunkNums(self.num_chunks)


class Glass:
    '''接收水滴：与或计算后的数据，'''
    def __init__(self, num_chunks):
        self.entries = []
        self.droplets = []      # 水滴数据列表
        self.num_chunks = num_chunks    # 总个数
        self.chunks = [None] * num_chunks
        self.chunk_bit_size = 0
        
    def addDroplet(self, d):
        self.droplets.append(d)     # 把水滴对象加到对象列表中
        logging.info("recv seed: {}\tnum_chunks: {}".format(d.seed, d.num_chunks))
        entry = [d.chunkNums(), d.data]
        self.entries.append(entry)
        logging.info('recv chunk_list : {}'.format(entry[0]))
        self.updateEntry(entry)

    def droplet_from_Bytes(self, d_bytes):  # 把一开始收到的水滴数据放在这里处理，只能说是一串字节数据，不是一个完整的水滴
        byte_factory = bitarray.bitarray(endian='big')
        byte_factory.frombytes(d_bytes[0:2])    # 取前两个字节，记录的是 num_chunks
        num_chunks = int(byte_factory.to01(), base=2)

        byte_factory = bitarray.bitarray(endian='big')
        byte_factory.frombytes(d_bytes[2:6])    # 取第3到第6个字节，记录的是 seed种子
        seed = int(byte_factory.to01(), base=2)
        data = d_bytes[6:]                      # 剩下的从第7个字节开始到最后是数据部分
        logging.info(' seed: {}\tglass num_chunks : {}\t data len: {},'.format(seed, num_chunks, len(data)))
        if self.chunk_bit_size == 0:
            byte_factory = bitarray.bitarray(endian='big')
            byte_factory.frombytes(data)
            self.chunk_bit_size = byte_factory.length()


        d = Droplet(data, seed, num_chunks) # 把数据转换成水滴，返回的是一个水滴对象
        return d

        
    def updateEntry(self, entry):
        '''
        BP 译码算法
        #  logging.info(entry[0])
        #  entry 是一个解码缓存结果
        #  entry[0] 是喷泉码编码时选中的源符号编号列表，长度即为度
        #  entry[1] 是喷泉码选中的符号 xor 后的结果
        #  chunk 是解码后的结果
        '''
        #  下面的 for 用于更新 entry 中的水滴，若水滴中包含已解码的码块，则将该部分去除
        #  执行结果是 entry 中的水滴不包含已解码的码块，度会减少或不变
        for chunk_num in entry[0]:
            if self.chunks[chunk_num] is not None:
                entry[1] = xor(entry[1], self.chunks[chunk_num])
                entry[0].remove(chunk_num)
        #  若度为 1,则说明该度的码块已经被解码出来，更新 chunk 后继续进行entry 中的其他
        #  元素的更新
        if len(entry[0]) == 1:
            self.chunks[entry[0][0]] = entry[1]
            self.entries.remove(entry)
            for d in self.entries:
                if entry[0][0] in d[0]:
                    self.updateEntry(d)
                    
    def getString(self):
        return ''.join(x or ' _ ' for x in self.chunks)

    def get_bits(self):
        current_bits = ''
        bitarray_factory = bitarray.bitarray(endian='big')
	logging.info('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
        logging.info('current chunks')
	logging.info('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
        #logging.info([ii if ii == None else '++++' for ii in self.chunks])
        count = 0
	for c in self.chunks:
	    if c is not None:
		count = count + 1
	logging.info('&&&&&&&&&&&&&&&&&&&&&&')
	logging.info('count = {}'.format(count))
	logging.info('&&&&&&&&&&&&&&&&&&&&&&')
	for chunk in self.chunks:
            if chunk == None:
                break
            else :
                #  trick
                tmp = [bitarray_factory.frombytes(ii) for ii in chunk]
        return bitarray_factory
        
    def isDone(self):
        return (None not in self.chunks) and (len(self.chunks) != 0) 

    def is_w1_done(self, w1_size):
        return None not in self.chunks[:int(round(self.num_chunks * w1_size))]

    def chunksDone(self):
        count = 0
        for c in self.chunks:
            if c is not None:
                count+=1
        return count

def fillAmt(fountain, glass, amt):
    #  amt = int(amt)
    g = glass 
    for i in xrange(amt):
        g.addDroplet(fountain.droplet())
    return 0

def fill_glass(drop, glass):
    pass
    
def main_test_fountain():
    m = open('../doc/fountain.txt', 'r').read()
    fountain = Fountain(m)
    glass = Glass(fountain.num_chunks)
    while not glass.isDone():
        a_drop = fountain.droplet()
        glass.addDroplet(a_drop)
        sleep(2)
        logging.info('+++++++++++++++++++++++++++++')
        logging.info(glass.getString())
    logging.info('done')

def main_test_ew_fountain():
    m = open(os.path.join(DOC_PATH, 'fountain.txt'), 'r').read()
    fountain = EW_Fountain(m, chunk_size=10)
    glass = Glass(fountain.num_chunks)
    ew_drop = None
    i = 0
    drop_size = 0
    while not glass.isDone():
        i += 1
        a_drop = fountain.droplet()
        ew_drop = EW_Droplet(a_drop.data, a_drop.seed, a_drop.num_chunks)
        drop_size = len(ew_drop.data)
        glass.addDroplet(ew_drop)
        #  sleep(1)
        logging.info('+++++++++++++++++++++++++++++')
        logging.info(glass.getString())
    logging.info("data size : {}".format(len(m)))
    logging.info("send drop num : {} drop size : {}".format(i, drop_size))        
    logging.info("send data size : {}".format(i * drop_size))
    logging.info("scale : {}".format((i* drop_size) / float(len(m))))
    logging.info('done')



if __name__ == "__main__":
    #  main_test_fountain()
    main_test_ew_fountain()
    pass


