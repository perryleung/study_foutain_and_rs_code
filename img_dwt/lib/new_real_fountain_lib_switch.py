# _*_ coding=utf-8 _*_
from __future__ import print_function
from degree_distribution_func import *
from math import ceil, log
import sys, os
import random
import json
import bitarray
import numpy as np
from time import sleep
import time
import logging
import pandas as pd
sys.setrecursionlimit(1000000)
LIB_PATH = os.path.dirname(__file__)
DOC_PATH = os.path.join(LIB_PATH, '../doc')
SIM_PATH = os.path.join(LIB_PATH, '../simulation')
NEW_SIM_PATH = os.path.join(LIB_PATH, '../new_simulation')

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
    return ''.join(chr(ord(charN(str1,i)) ^ ord(charN(str2,i))) for i in range(length))

def robust_randChunkNums(num_chunks):
    size = robust_soliton(num_chunks).__next__()
    return [ii for ii in random.sample(range(num_chunks), size)]

def open_randChunkNums(chunk_id, num_chunks, a=0.075):
    if chunk_id <= a * num_chunks:
        size = binary_exp_func(num_chunks).__next__()
    else:
        size = robust_soliton(num_chunks).__next__()
    return [ii for ii in random.sample(range(num_chunks), size)]

def all_at_once_randChunkNums(chunks):
    return [ii for ii in np.random.choice(chunks, 1, False)]


class Droplet:
    ''' 储存随机数种子，并有一个计算本水滴中包含的数据块编码的方法'''
    def __init__(self, data, seed, num_chunks, process, chunk_id):
        self.data = data
        self.seed = seed
        self.num_chunks = num_chunks
        self.process = process
        self.chunk_id = chunk_id

    def robust_chunkNums(self):
        random.seed(self.seed)
        np.random.seed(self.seed)
        return robust_randChunkNums(self.num_chunks)

    def open_chunkNums(self):
        random.seed(self.seed)
        np.random.seed(self.seed)
        return open_randChunkNums(self.chunk_id, self.num_chunks)

    def all_at_once_chunkNums(self):
        random.seed(self.seed)
        np.random.seed(self.seed)
        return all_at_once_randChunkNums(self.process)

    def toString(self):
        return json.dumps(
            {
                'seed':self.seed,
                'num_chunks':self.num_chunks,
                'data':self.data
            })
    
class Fountain(object):
    # 继承了object对象，拥有了好多可操作对象，这些都是类中的高级特性。python 3 中已经默认加载了object
    def __init__(self, data, chunk_size, seed=None, process=[]):
        self.data = data
        self.chunk_size = chunk_size
        self.num_chunks = int(ceil(len(data) / float(chunk_size)))
        self.seed = seed
        self.all_at_once = False
        self.chunk_selected = []
        self.chunk_process = process
        random.seed(seed)
        np.random.seed(seed)
        self.chunk_id = 0

    def droplet(self):
        self.updateSeed()
        ### 修改
        self.chunk_id += 1
        if not self.all_at_once:
            self.chunk_selected = open_randChunkNums(self.chunk_id, self.num_chunks)
            #self.chunk_selected = robust_randChunkNums(self.num_chunks)
        else:
            self.chunk_selected = all_at_once_randChunkNums(self.chunk_process)

        #logging.info("seed: {}".format(self.seed))
        #logging.info("send chunk list: {}".format(self.chunk_selected)) #this shows the chunks which are selected everytime!
        data = None
        for num in self.chunk_selected:
            if data is None:
                data = self.chunk(num)
            else:
                data = xor(data, self.chunk(num))

        return Droplet(data, self.seed, self.num_chunks, self.chunk_process, self.chunk_id)

    def chunk(self, num):
        start = self.chunk_size * num
        end = min(self.chunk_size * (num+1), len(self.data))
        return self.data[start:end]

    def updateSeed(self):
        self.seed = random.randint(0, 2**31-1)
        random.seed(self.seed)
        np.random.seed(self.seed)

class EW_Fountain(Fountain):
    ''' 扩展窗喷泉码 '''
    def __init__(self, data, chunk_size, seed=None, process=[], w1_size=0.1, w1_pro=0.084):
        Fountain.__init__(self, data, chunk_size=chunk_size, seed=None, process=process)
        # logging.info("-----------------EW_Fountain------------")
        self.w1_p = w1_size
        self.w1_pro = w1_pro
        self.windows_id_gen = self.windows_selection()
        self.w1_size = int(round(self.num_chunks * self.w1_p))
        self.w2_size = self.num_chunks
        self.w1_random_chunk_gen = robust_soliton(self.w1_size),
        self.w2_random_chunk_gen = robust_soliton(self.w2_size)
        self.all_at_once = False
        self.chunk_process = process
        self.chunk_selected = []
        # logging.info('w1_size : ', self.w1_size)
        # logging.info('w2_size : ', self.w2_size)
        # logging.info('w size ; ', self.num_chunks)

    def droplet(self):
        self.updateSeed()
        # 修改
        if not self.all_at_once:
            self.chunk_selected = self.EW_robust_RandChunkNums(self.num_chunks)
        else:
            self.chunk_selected = self.EW_all_at_once_RandChunkNums()
        # wrong sentence
        # chunk_selected = self.EW_RandChunkNums(self.num_chunks)

        # logging.info("send seed: {}\tnum_chunks: {}".format(self.seed, self.num_chunks))
        data = None
        for num in self.chunk_selected:
            if data is None:
                data = self.chunk(num)
            else:
                data = xor(data, self.chunk(num))

        # logging.info('send chunk_list : {}'.format(chunk_selected))
        return EW_Droplet(data, self.seed, self.num_chunks, self.chunk_process)

    # not used
    def EW_RandChunkNums(self, num_chunks):
        '''扩展窗的不同在这里'''
        window_id = self.windows_id_gen.__next__()
        #  logging.info('window_id: ', window_id)
        if window_id == 1:
            size = self.w1_random_chunk_gen[0].__next__()          # 鲁棒孤波返回的度值
            return random.sample(range(self.w1_size), size)
        else:
            size = self.w2_random_chunk_gen.__next__()
            return [ii for ii in random.sample(range(self.w2_size), size)]

    def EW_robust_RandChunkNums(self, num_chunks):
        '''扩展窗的不同在这里'''
        window_id = self.windows_id_gen.__next__()
        if window_id == 1:
            size = self.w1_random_chunk_gen[0].__next__()          # 鲁棒孤波返回的度值
            return random.sample(range(self.w1_size), size)
        else:
            size = self.w2_random_chunk_gen.__next__()
            return [ii for ii in random.sample(range(self.w2_size), size)]

    def EW_all_at_once_RandChunkNums(self):
        # w1未译出的块
        w1_chunk_process = []
        for i in self.chunk_process:
            if i <= self.w1_size:
                w1_chunk_process.append(i)

        window_id = self.windows_id_gen.__next__()
        if (window_id == 1 and not len(w1_chunk_process) == 0):
            return [ii for ii in np.random.choice(w1_chunk_process, 1, False)]          
        else:
            return [ii for ii in np.random.choice(self.chunk_process, 1, False)]

    def windows_selection(self):
        '''以概率[{p:1, 1-p:2}返回选择的窗口'''
        d = [1, 2]
        w1_p = self.w1_pro
        w_f = [w1_p, 1-w1_p]
        while True:
            i = np.random.choice(d, 1, False, w_f)[0]    # 从d中以概率w_f，随机选择1个,replace抽样之后还放不放回去
            yield i

    def show_robust_soliton(self, N=10000):
        w1_stat = [0] * (self.w1_size + 1)
        w2_stat = [0] * (self.w2_size + 1)
        for i in range(N):
            w1_stat[self.w1_random_chunk_gen[0].__next__()] += 1
            w2_stat[self.w2_random_chunk_gen.__next__()] += 1

class EW_Droplet(Droplet):
    '''扩展窗喷泉码专用水滴, 计算水滴使用的数据块列表'''
    def __init__(self, data, seed, num_chunks, process, w1_size=0.1, w1_pro=0.084):
        Droplet.__init__(self, data, seed, num_chunks, process)
        m = ' ' * num_chunks * len(data)
        self.ower = EW_Fountain(m, len(self.data), process=process, w1_size=w1_size, w1_pro=w1_pro)

    def robust_chunkNums(self):
        random.seed(self.seed)
        np.random.seed(self.seed)
        return self.ower.EW_robust_RandChunkNums(self.num_chunks)

    def all_at_once_chunkNums(self):
        random.seed(self.seed)
        np.random.seed(self.seed)
        return self.ower.EW_all_at_once_RandChunkNums()

    # not used
    def chunkNums(self):
        random.seed(self.seed)
        np.random.seed(self.seed)
        return self.ower.EW_RandChunkNums(self.num_chunks)

class Glass:
    '''接收水滴：与或计算后的数据，'''
    def __init__(self, num_chunks):
        self.entries = []
        self.droplets = []
        self.num_chunks = num_chunks
        self.chunks = [None] * num_chunks
        self.chunk_bit_size = 0
        self.dropid = 0
        self.all_at_once = False
        
    def addDroplet(self, drop):
        self.dropid += 1
        self.droplets.append(drop)
        # logging.info("recv seed: {}\tnum_chunks: {}".format(drop.seed, drop.num_chunks))    # \t=tab
        entry = [drop.open_chunkNums(), drop.data] if not self.all_at_once else [drop.all_at_once_chunkNums(), drop.data] 
        self.entries.append(entry)
        #logging.info('recv chunk_list : {}'.format(entry[0]))
        self.updateEntry(entry)

    # not used
    def droplet_from_Bytes(self, d_bytes):

        byte_factory = bitarray.bitarray(endian='big')
        byte_factory.frombytes(d_bytes[0:2])

        num_chunks = int(byte_factory.to01(), base=2)

        byte_factory1 = bitarray.bitarray(endian='big')
        byte_factory1.frombytes(d_bytes[2:6])
        seed = int(byte_factory1.to01(), base=2)

        data = d_bytes[6:]

        logging.info(' seed: {}\tglass num_chunks : {}\t data len: {},'.format(seed, num_chunks, len(data)))
        if self.chunk_bit_size == 0:
            byte_factory2 = bitarray.bitarray(endian='big')
            byte_factory2.frombytes(data)
            self.chunk_bit_size = byte_factory2.length()

        d = Droplet(data, seed, num_chunks, [])
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
                # entry[1] = x_o_r(entry[1], self.chunks[chunk_num])
                entry[0].remove(chunk_num)
        #  若度为 1,则说明该度的码块已经被解码出来，更新 chunk 后继续进行entry 中的其他
        #  元素的更新
        if len(entry[0]) == 1:
            self.chunks[entry[0][0]] = entry[1]
            self.entries.remove(entry)
            for former_entry in self.entries:
                if entry[0][0] in former_entry[0]:
                    self.updateEntry(former_entry)
                    
    def getString(self):
        return ''.join(x or ' _ ' for x in self.chunks)

    def isDone(self):
        return (None not in self.chunks) and (len(self.chunks) != 0) 

    # 返回未译出码块
    def getProcess(self):
        idx = 0
        process = []
        for chunk in self.chunks:
            if chunk is None:
                process.append(idx)
            idx += 1
        return process

    def chunksDone(self):
        count = 0
        for c in self.chunks:
            if c is not None:
                count+=1
        return count


def test_LT_fountain():
    testFile = 'open_' + time.asctime().replace(' ', '_').replace(':', '_')
    test_dir = os.path.join(
                NEW_SIM_PATH,
                "LT",
                testFile
                )
    if not os.path.exists(test_dir):
            os.mkdir(test_dir)
    suffix_list = ['100.txt', '150.txt', '200.txt', '250.txt', '300.txt', '350.txt', '400.txt', '450.txt', '500.txt', '1000.txt']
    file_list = [DOC_PATH + '/test_data/' + ii for ii in suffix_list]
    avg_drops_list = [0]*len(suffix_list)
    avg_idx = 0

    for f in file_list:
        m = open(f, 'r').read()
        # 测试1000次
        num_chunks_list = [0]*100
        times_list = [0]*100
        drop_num_used_list = [0]*100
        times = 0
        K = 0
        while times < 100:
            fountain = Fountain(m, 1)
            K = fountain.num_chunks
            glass = Glass(fountain.num_chunks)
            while not glass.isDone():
                a_drop = fountain.droplet()       # send
                glass.addDroplet(a_drop)          # recv

            num_chunks_list[times] = fountain.num_chunks
            times_list[times] = times
            drop_num_used_list[times] = glass.dropid

            logging.info("K = " + str(fountain.num_chunks) +" times: " + str(times+1) + ' done, receive_drop_used: ' + str(glass.dropid) + " chunk_id : " + str(fountain.chunk_id))
            times += 1

        res = pd.DataFrame({'num_chunks':num_chunks_list, 
            'times':times_list, 
            'drop_num_used':drop_num_used_list})
        res.to_csv(os.path.join(test_dir, 'K' + '_'+ str(K) + '_' + time.asctime().replace(' ', '_').replace(':', '_') + '.csv'),  mode='a')

        avg_drops_list[avg_idx] = float(sum(drop_num_used_list) / len(drop_num_used_list))
        avg_idx += 1
    
    avg_res = pd.DataFrame({'K': [ii.split('.')[0] for ii in suffix_list], 
            'avgs':avg_drops_list})
    avg_res.to_csv(os.path.join(test_dir, 'avgs' + '_' + 'open' + '.csv'),  mode='a')

def test_LT_feedback_fountain():
    testFile = 'open_' + time.asctime().replace(' ', '_').replace(':', '_')
    test_dir = os.path.join(
                NEW_SIM_PATH,
                "LT_feedback",
                testFile
                )
    if not os.path.exists(test_dir):
        os.mkdir(test_dir)
    suffix_list = ['100.txt', '150.txt', '200.txt', '250.txt', '300.txt', '350.txt', '400.txt', '450.txt', '500.txt', '1000.txt']
    file_list = [DOC_PATH + '/test_data/' + ii for ii in suffix_list]
    avg_drops_list = [0]*len(suffix_list)
    avg_idx = 0

    for f in file_list:
        m = open(f, 'r').read()
        # 测试1000次
        num_chunks_list = [0]*100
        times_list = [0]*100
        drop_num_used_list = [0]*100

        times = 0
        K = 0
        while times < 100:
            fountain = Fountain(m, 1)
            K = fountain.num_chunks
            glass = Glass(fountain.num_chunks)
            while not glass.isDone():
                a_drop = fountain.droplet()       # send
                
                glass.addDroplet(a_drop)          # recv
                if (glass.dropid >= K):
                    glass.all_at_once = True
                    fountain.all_at_once = True
                    if ((glass.dropid - K) % 10 == 0):
                    # 每10倍数未发则监测重传一次
                        #print(glass.getProcess())
                        fountain.chunk_process = glass.getProcess()

                # logging.info('+++++++++++++++++++++++++++++')
                # logging.info(glass.getString())

            num_chunks_list[times] = fountain.num_chunks
            times_list[times] = times
            drop_num_used_list[times] = glass.dropid

            logging.info("K = " + str(fountain.num_chunks) +" times: " + str(times+1) + ' done, receive_drop_used: ' + str(glass.dropid))
            times += 1

        res = pd.DataFrame({'num_chunks':num_chunks_list, 
            'times':times_list, 
            'drop_num_used':drop_num_used_list})
        res.to_csv(os.path.join(test_dir, 'feedback_K' + '_'+ str(K) + '_' + time.asctime().replace(' ', '_').replace(':', '_') + '.csv'),  mode='a')

        avg_drops_list[avg_idx] = float(sum(drop_num_used_list) / len(drop_num_used_list))
        avg_idx += 1
    
    avg_res = pd.DataFrame({'K': [ii.split('.')[0] for ii in suffix_list], 
            'avgs':avg_drops_list})
    avg_res.to_csv(os.path.join(test_dir, 'feedback_avgs' + '_' + 'open' + '.csv'),  mode='a')

def test_LT_fountain_short():
    testFile = 'open_short_' + time.asctime().replace(' ', '_').replace(':', '_')
    test_dir = os.path.join(
                NEW_SIM_PATH,
                "LT",
                testFile
                )
    if not os.path.exists(test_dir):
            os.mkdir(test_dir)
    suffix_list = []
    for i in range(85):
        suffix_list.append(str(66 + i) + str('.txt'))
    for i in range(7):
        suffix_list.append(str(i*50+200) + str('.txt')) 
    file_list = [DOC_PATH + '/test_data/' + ii for ii in suffix_list]
    avg_drops_list = [0]*len(suffix_list)
    avg_idx = 0

    for f in file_list:
        m = open(f, 'r').read()
        # 测试1000次
        num_chunks_list = [0]*100
        times_list = [0]*100
        drop_num_used_list = [0]*100
        times = 0
        K = 0
        while times < 100:
            fountain = Fountain(m, 1)
            K = fountain.num_chunks
            glass = Glass(fountain.num_chunks)
            while not glass.isDone():
                a_drop = fountain.droplet()       # send
                glass.addDroplet(a_drop)          # recv

            num_chunks_list[times] = fountain.num_chunks
            times_list[times] = times
            drop_num_used_list[times] = glass.dropid

            logging.info("K = " + str(fountain.num_chunks) +" times: " + str(times+1) + ' done, receive_drop_used: ' + str(glass.dropid) + " chunk_id : " + str(fountain.chunk_id))
            times += 1

        res = pd.DataFrame({'num_chunks':num_chunks_list, 
            'times':times_list, 
            'drop_num_used':drop_num_used_list})
        res.to_csv(os.path.join(test_dir, 'K' + '_'+ str(K) + '_' + time.asctime().replace(' ', '_').replace(':', '_') + '.csv'),  mode='a')

        avg_drops_list[avg_idx] = float(sum(drop_num_used_list) / len(drop_num_used_list))
        avg_idx += 1
    
    avg_res = pd.DataFrame({'K': [ii.split('.')[0] for ii in suffix_list], 
            'avgs':avg_drops_list})
    avg_res.to_csv(os.path.join(test_dir, 'avgs' + '_' + 'short' + '.csv'),  mode='a')

def test_LT_feedback_fountain_short():
    testFile = 'open_short_' + time.asctime().replace(' ', '_').replace(':', '_')
    test_dir = os.path.join(
                NEW_SIM_PATH,
                "LT_feedback",
                testFile
                )
    if not os.path.exists(test_dir):
        os.mkdir(test_dir)
    suffix_list = []
    for i in range(85):
        suffix_list.append(str(66 + i) + str('.txt'))  #
    for i in range(7):
        suffix_list.append(str(i*50+200) + str('.txt'))
    file_list = [DOC_PATH + '/test_data/' + ii for ii in suffix_list]
    avg_drops_list = [0]*len(suffix_list)
    avg_idx = 0

    for f in file_list:
        m = open(f, 'r').read()
        # 测试1000次
        num_chunks_list = [0]*100
        times_list = [0]*100
        drop_num_used_list = [0]*100

        times = 0
        K = 0
        while times < 100:
            fountain = Fountain(m, 1)
            K = fountain.num_chunks
            glass = Glass(fountain.num_chunks)
            while not glass.isDone():
                a_drop = fountain.droplet()       # send
                
                glass.addDroplet(a_drop)          # recv
                if (glass.dropid >= K):
                    glass.all_at_once = True
                    fountain.all_at_once = True
                    if ((glass.dropid - K) % 10 == 0):
                    # 每10倍数未发则监测重传一次
                        #print(glass.getProcess())
                        fountain.chunk_process = glass.getProcess()

                # logging.info('+++++++++++++++++++++++++++++')
                # logging.info(glass.getString())

            num_chunks_list[times] = fountain.num_chunks
            times_list[times] = times
            drop_num_used_list[times] = glass.dropid

            logging.info("K = " + str(fountain.num_chunks) +" times: " + str(times+1) + ' done, receive_drop_used: ' + str(glass.dropid))
            times += 1

        res = pd.DataFrame({'num_chunks':num_chunks_list, 
            'times':times_list, 
            'drop_num_used':drop_num_used_list})
        res.to_csv(os.path.join(test_dir, 'feedback_K' + '_'+ str(K) + '_' + time.asctime().replace(' ', '_').replace(':', '_') + '.csv'),  mode='a')

        avg_drops_list[avg_idx] = float(sum(drop_num_used_list) / len(drop_num_used_list))
        avg_idx += 1
    
    avg_res = pd.DataFrame({'K': [ii.split('.')[0] for ii in suffix_list], 
            'avgs':avg_drops_list})
    avg_res.to_csv(os.path.join(test_dir, 'feedback_avgs' + '_' + 'short' + '.csv'),  mode='a')

def test_EW_fountain():
    testFile = 'RSD_' + time.asctime().replace(' ', '_').replace(':', '_')
    test_dir = os.path.join(
                NEW_SIM_PATH,
                "EW",
                testFile
                )
    if not os.path.exists(test_dir):
            os.mkdir(test_dir)
    #suffix_list = ['50.txt', '100.txt', '150.txt', '200.txt', '250.txt', '300.txt', '350.txt', '400.txt', '450.txt', '500.txt', '1000.txt', '1500.txt', '2000.txt', '2500.txt', '3000.txt', '3500.txt', '4000.txt', '4500.txt', '5000.txt']
    suffix_list = ['5000.txt']
    file_list = [DOC_PATH + '/test_data/' + ii for ii in suffix_list]
    avg_drops_list = [0]*len(suffix_list)
    avg_idx = 0

    for f in file_list:
        m = open(f, 'r').read()
        # 测试1000次
        num_chunks_list = [0]*100
        times_list = [0]*100
        drop_num_used_list = [0]*100

        times = 0
        K = 0
        while times < 100:
            fountain = EW_Fountain(m, 1)
            K = fountain.num_chunks
            glass = Glass(fountain.num_chunks)
            ew_drop = None
            while not glass.isDone():
                a_drop = fountain.droplet()       # send
                ew_drop = EW_Droplet(a_drop.data, a_drop.seed, a_drop.num_chunks, a_drop.process)
                glass.addDroplet(ew_drop)          # recv

            num_chunks_list[times] = fountain.num_chunks
            times_list[times] = times
            drop_num_used_list[times] = glass.dropid

            logging.info("EW K=" + str(fountain.num_chunks) +" times: " + str(times+1) + ' done, receive_drop_used: ' + str(glass.dropid))
            times += 1

        res = pd.DataFrame({'num_chunks':num_chunks_list, 
            'times':times_list, 
            'drop_num_used':drop_num_used_list})
        res.to_csv(os.path.join(test_dir, 'EW_K' + '_'+ str(K) + '_' + time.asctime().replace(' ', '_').replace(':', '_') + '.csv'),  mode='a')

        avg_drops_list[avg_idx] = float(sum(drop_num_used_list) / len(drop_num_used_list))
        avg_idx += 1
    
    avg_res = pd.DataFrame({'K': [ii.split('.')[0] for ii in suffix_list], 
            'avgs':avg_drops_list})
    avg_res.to_csv(os.path.join(test_dir, 'avgs' + '_' + time.asctime().replace(' ', '_').replace(':', '_') + '.csv'),  mode='a')

def test_EW_feedback_fountain():
    testFile = 'RSD_' + time.asctime().replace(' ', '_').replace(':', '_')
    test_dir = os.path.join(
                NEW_SIM_PATH,
                "EW_feedback",
                testFile
                )
    if not os.path.exists(test_dir):
            os.mkdir(test_dir)
    suffix_list = ['50.txt', '100.txt', '150.txt', '200.txt', '250.txt', '300.txt', '350.txt', '400.txt', '450.txt', '500.txt', '1000.txt', '1500.txt', '2000.txt', '2500.txt', '3000.txt', '3500.txt', '4000.txt', '4500.txt', '5000.txt']
    file_list = [DOC_PATH + '/test_data/' + ii for ii in suffix_list]
    avg_drops_list = [0]*len(suffix_list)
    avg_idx = 0

    for f in file_list:
        m = open(f, 'r').read()
        # 测试1000次
        num_chunks_list = [0]*100
        times_list = [0]*100
        drop_num_used_list = [0]*100

        times = 0
        K = 0
        while times < 100:
            fountain = EW_Fountain(m, 1)
            K = fountain.num_chunks
            glass = Glass(fountain.num_chunks)
            ew_drop = None
            while not glass.isDone():
                a_drop = fountain.droplet()       # send
                ew_drop = EW_Droplet(a_drop.data, a_drop.seed, a_drop.num_chunks, a_drop.process)

                glass.addDroplet(ew_drop)          # recv
                if(glass.dropid >= K):
                    glass.all_at_once = True
                    fountain.all_at_once = True
                    # 之后每10个包反馈进度
                    if ((glass.dropid - K) % 10 == 0):
                        print(glass.getProcess())
                        fountain.chunk_process = glass.getProcess()
                        ew_drop.process = glass.getProcess()


            num_chunks_list[times] = fountain.num_chunks
            times_list[times] = times
            drop_num_used_list[times] = glass.dropid

            logging.info("feedback_EW_K=" + str(fountain.num_chunks) +" times: " + str(times) + 'done, receive_drop_used: ' + str(glass.dropid))
            times += 1

        res = pd.DataFrame({'num_chunks':num_chunks_list, 
            'times':times_list, 
            'drop_num_used':drop_num_used_list})
        res.to_csv(os.path.join(test_dir, 'feedback_EW_K' + '_'+ str(K) + '_' + time.asctime().replace(' ', '_').replace(':', '_') + '.csv'),  mode='a')

        avg_drops_list[avg_idx] = float(sum(drop_num_used_list) / len(drop_num_used_list))
        avg_idx += 1
    
    avg_res = pd.DataFrame({'K': [ii.split('.')[0] for ii in suffix_list], 
            'avgs':avg_drops_list})
    avg_res.to_csv(os.path.join(test_dir, 'feedback_EW_avgs' + '_' + time.asctime().replace(' ', '_').replace(':', '_') + '.csv'),  mode='a')

def test_LT_open_a():
    a = 0.25
    testFile = 'open_test_a_is_'+str(a)
    test_dir = os.path.join(
                NEW_SIM_PATH,
                "LT/open_test/",
                testFile
                )
    if not os.path.exists(test_dir):
            os.mkdir(test_dir)
    suffix_list = ['70.txt', '100.txt', '150.txt', '200.txt', '250.txt', '300.txt', '350.txt', '400.txt', '450.txt', '500.txt']
    file_list = [DOC_PATH + '/test_data/' + ii for ii in suffix_list]
    avg_drops_list = [0]*len(suffix_list)
    avg_idx = 0

    for f in file_list:
        m = open(f, 'r').read()
        # 测试1000次
        num_chunks_list = [0]*100
        times_list = [0]*100
        drop_num_used_list = [0]*100
        times = 0
        K = 0
        while times < 100:
            fountain = Fountain(m, 1)
            K = fountain.num_chunks
            glass = Glass(fountain.num_chunks)
            while not glass.isDone():
                a_drop = fountain.droplet()       # send
                glass.addDroplet(a_drop)          # recv

            num_chunks_list[times] = fountain.num_chunks
            times_list[times] = times
            drop_num_used_list[times] = glass.dropid

            logging.info("K = " + str(fountain.num_chunks) +" times: " + str(times+1) + ' done, receive_drop_used: ' + str(glass.dropid) + " chunk_id : " + str(fountain.chunk_id))
            times += 1

        res = pd.DataFrame({'num_chunks':num_chunks_list, 
            'times':times_list, 
            'drop_num_used':drop_num_used_list})
        res.to_csv(os.path.join(test_dir, 'K' + '_'+ str(K) + '_' + time.asctime().replace(' ', '_').replace(':', '_') + '.csv'),  mode='a')

        avg_drops_list[avg_idx] = float(sum(drop_num_used_list) / len(drop_num_used_list))
        avg_idx += 1
    
    avg_res = pd.DataFrame({'K': [ii.split('.')[0] for ii in suffix_list], 
            'avgs':avg_drops_list})
    avg_res.to_csv(os.path.join(test_dir, 'avgs' + '_' + str(a) + '.csv'),  mode='a')

def main_test_ew_fountain():
    m = open(os.path.join(DOC_PATH, 'fountain.txt'), 'r').read()
    run_times = 10
    scale_list = [0.0] * run_times
    j = 0
    while j < run_times:
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
            # logging.info('+++++++++++++++++++++++++++++')
            # logging.info(glass.getString())
        logging.info("data size : {}".format(len(m)))
        logging.info("send drop num : {} drop size : {}".format(i, drop_size))        
        logging.info("send data size : {}".format(i * drop_size))
        logging.info("scale : {}".format((i * drop_size) / float(len(m))))
        logging.info("self.dropid of glass : {}".format(glass.dropid))
        logging.info('done')
        scale_list[j] = (i * drop_size) / float(len(m))
        j += 1
    logging.info("average scale : {}".format(sum(scale_list) / (run_times*1.0)))
    logging.info("")
    logging.info("sum of scale_list : {}".format(sum(scale_list)))
    logging.info("scale_list : {}".format(scale_list))

def main_test_normal_fountain():
    m = open(os.path.join(DOC_PATH, 'fountain.txt'), 'r').read()
    run_times = 100
    scale_list = [0.0]*run_times
    #fountain = Fountain(m, chunk_size=10)
    #glass = Glass(fountain.num_chunks)
    drop_size = 0
    j = 0
    while j < run_times:
        i = 0
        logging.info("***** running the {} time now!".format(j+1))
        fountain = Fountain(m, chunk_size=10)
        glass = Glass(fountain.num_chunks)
        K = fountain.num_chunks
        while not glass.isDone():
            i += 1
            a_drop = fountain.droplet()
            drop_size = len(a_drop.data)
            glass.addDroplet(a_drop)
            '''
            # with or without feedback
            if(glass.dropid >= K):
                fountain.all_at_once = True
                if((glass.dropid-K)%10 == 0):
                    print(glass.getProcess())
                    fountain.chunk_process = glass.getProcess()
            else:
                fountain.all_at_once = False

            sleep(0.5)
            '''
            #logging.info('+++++++++++++++++++++++++++++')
            #logging.info(glass.getString())
        logging.info("data size : {} num of chunk : {}".format(len(m), a_drop.num_chunks))
        logging.info("send drop num : {} drop size : {}".format(i, drop_size))        
        logging.info("send data size : {}".format(i * drop_size))
        logging.info("scale : {}".format((i * drop_size) / float(len(m))))
        logging.info("self.dropid of glass : {}".format(glass.dropid))
        logging.info('done')
        scale_list[j] = (i * drop_size) / float(len(m))
        j += 1
    logging.info("average scale : {}".format(sum(scale_list) / (run_times*1.0)))
    logging.info("")
    logging.info("sum of scale_list : {}".format(sum(scale_list)))
    logging.info("scale_list : {}".format(scale_list))

if __name__ == "__main__":
    #test_LT_fountain()
    #test_LT_feedback_fountain()
    #test_LT_fountain_short()
    test_LT_feedback_fountain_short()
    #test_EW_fountain()
    #test_EW_feedback_fountain()
    #test_LT_open_a()
    pass


