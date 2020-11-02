# _*_ coding=utf-8 _*_ 
from __future__ import print_function
import sys, os
import numpy as np
from math import ceil
import struct
import pywt
import bitarray
import matlab.engine
from PIL import Image
import time, socket, select, re
sys.path.append('.')
from dwt_lib import load_img
from send_recv import Sender, Receiver
from send_recv import EW_Sender, EW_Receiver

LIB_PATH = os.path.dirname(__file__)
DOC_PATH = os.path.join(LIB_PATH, '../doc')
SIM_PATH = os.path.join(LIB_PATH, '../simulation')
WHALE_IMG_128 = os.path.join(DOC_PATH, 'whale_128.bmp')


PORT_LIKE = 100         # 端口号
NORNAL = ord('0')       # 一般数据包号 0
SIGNIFICANT = ord('1')  # 重要数据包号 1

PARA_PACKET = 1         # 参数数据包类型 1
ACK_APP = 2             # ACK数据包类型 2
STOP_APP = 3            # 停止数据包类型 3
FILLING = '\0' * 5      # 填充字节 5个'\0'

SEND_ID = 1             # 发送节点 ID
RECV_ID = 2             # 接收节点 ID

HOST = '127.0.0.1'      # IP地址


def find_stop_app(read_byte):
    stop_app_pattern = ''.join([PORT_LIKE, SIGNIFICANT, '.', STOP_APP])
    if re.search(stop_app_pattern, read_byte):
        #在stop_app_pattern中找read_byte
        return True
    else:
        return False

class Stack_Sender(EW_Sender):
    def __init__(self,
            img_path = WHALE_IMG_128,
            chunk_size = 60,
            stack_port = 9080,
            seed = 233
            ):
        self.stack_port = stack_port    
        Sender.__init__(self, img_path, fountain_chunk_size=chunk_size, fountain_type='ew', seed=seed)
        self.drop_interval = 10
        ACK_app = False # 是否收到ACK_app
        

    def socket_builder(self):
        stack_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        stack_socket.connect((HOST, self.stack_port))   #都连接的是协议栈的端口
        print("connect to {} ...".format(self.stack_port))
        return stack_socket

    def sender_main(self):
        '''
        100 : 类似端口
        1 ：关键数据包,见demo.cc:64
        2 ：目标节点ID
        1 ：包类型是参数数据包para_packet,发送和接收自己约定
        78: chunk_size
        '''
        contant_para_packet = [
                PORT_LIKE,
                SIGNIFICANT,
                RECV_ID, 
                PARA_PACKET, 
                self.fountain.chunk_size]
        # 将contant_para_packet格式化成"integer", "B"'s Ctype is unsigned char
        para_packet = ''.join([struct.pack("B", ii) for ii in contant_para_packet]) + FILLING 
        self.write_fd.send(para_packet)     # 1、先发送参数数据包，重要
        print("para_packet len: {}, {}".format(len(para_packet), [ord(ii) for ii in para_packet]))
        print("the size of para_packet is : {}".format(sys.getsizeof(para_packet))) 
        while True:
            read_byte = self.write_fd.recv(self.fountain_chunk_size + 3)
            if not read_byte:   # 2、等待接收ACK
                pass
            elif ord(read_byte[0]) == PORT_LIKE \
                    and ord(read_byte[1]) == SIGNIFICANT \
                    and ord(read_byte[3]) == ACK_APP:
                print("recv ACK_app len : {}, {}".format(len(read_byte), [ord(ii) for ii in read_byte]))
                print("the size of ACK_app is : {}".format(sys.getsizeof(read_byte))) 
                break
        self.send_drops_use_socket()    # 3、然后发喷泉码数据包


    def catch_stop_app(self):
        self.write_fd.setblocking(0)    # 0 = false
        ready = select.select([self.write_fd], [], [], self.drop_interval)
        if ready[0]:
            # 非阻塞读数据
            read_byte = self.write_fd.recv(999)
            print("recv len {} : {}".format(len(read_byte), [ord(ii) for ii in read_byte]))
            if not read_byte:
                return False
            byte_to_deal = len(read_byte)
            # 处理读取的数据
            while byte_to_deal > 0:
                # 处理非本程序的数据
                if ord(read_byte[0]) != PORT_LIKE:
                    byte_to_deal -= 46
                    read_byte = read_byte[46:]
                # 处理本程序的数据    
                else:
                    # 收到了stop_app
                    if ord(read_byte[0]) == PORT_LIKE and \
                        ord(read_byte[1]) == SIGNIFICANT and ord(read_byte[3]) == STOP_APP:
                            print('recv STOP_APP and stop')
                            return True
                    else:
                        byte_to_deal -= 4
                        read_byte = read_byte[4:]
            return False

    def send_drops_use_socket(self):
        recv_stop_app = False
        while not recv_stop_app:
            time.sleep(self.drop_interval)          #sleep for drop_interval seconds
            recv_stop_app = self.catch_stop_app()

            print('drop id : ', self.drop_id)
            a_drop = self.a_drop()
            header = [PORT_LIKE, NORNAL, RECV_ID]
            # print("Header Size : {}".format(len(''.join([struct.pack("B", ii) for ii in header]))))
            send_buff = ''.join([struct.pack("B", ii) for ii in header]) + a_drop + FILLING
            print("the size of drop_packet(send_buff) is : {}".format(sys.getsizeof(send_buff))) 
            # print("Send Raw len {} : {}".format(len(send_buff), [ord(ii) for ii in send_buff]))
            self.write_fd.send(send_buff)


class Stack_Receiver(EW_Receiver):
    def __init__(self, stack_port = 9079 + RECV_ID):
        print('stack_port : {}'.format(stack_port))
        self.stack_port = stack_port
        EW_Receiver.__init__(self)
        self.chunk_size = 0

    def socket_builder(self):
        socket_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_recv.connect((HOST, self.stack_port))
        print("connect to port {}".format(self.stack_port))
        return socket_recv


    def begin_to_catch(self):
        '''
        100 : 类似端口
        1：关键数据包,见demo.cc:64
        1 ：目标节点ID
        2 ：包类型是参数数据包ACK_APP,发送和接收自己约定
        '''
         # 等待参数数据包
        while True:
            read_byte = self.socket_recv.recv(PORT_LIKE)
            if not read_byte:
                pass
            elif ord(read_byte[0]) == PORT_LIKE \
                    and ord(read_byte[1]) == SIGNIFICANT \
                    and ord(read_byte[3]) == PARA_PACKET:
                # 收到参数数据包
                print("recv PARA_PACKET len : {}, {}".format(len(read_byte), [ord(ii) for ii in read_byte]))
                self.chunk_size = ord(read_byte[4])
                
                # 发送 ACK_APP[100, ord('1'), 1, 2]
                contant_ACK_app = [PORT_LIKE, SIGNIFICANT, SEND_ID, ACK_APP]
                ACK_app = ''.join([struct.pack("B", ii) for ii in contant_ACK_app]) + FILLING
                self.socket_recv.send(ACK_app)
                break;
        # 接收水滴数据包    
        while True:
            a_drop = self.catch_a_drop_use_socket()
            data_offset = 6 # fountain_lib.py:238
            if not a_drop == None:
                self.drop_id += 1
                print("drops id : ", self.drop_id)
                self.drop_byte_size = len(a_drop)
                if len(a_drop) >= self.chunk_size + data_offset:
                    a_drop = a_drop[:self.chunk_size+data_offset]
                    self.add_a_drop(a_drop)
                    if self.glass.isDone():
                        print('recv done drop num {}'.format(self.drop_id))
                        break
                else:
                    print('recv broken drop, discard it ----------------')
        stop_app = [PORT_LIKE, SIGNIFICANT, SEND_ID, STOP_APP]
        buff_stop_app = ''.join([struct.pack("B", ii) for ii in stop_app]) + FILLING
        print('send STOP APP len {} : {}'.format(len(buff_stop_app), [ord(ii) for ii in buff_stop_app]))
        self.socket_recv.send(buff_stop_app)
        self.socket_recv.close()


    def catch_a_drop_use_socket(self):
        read_byte = self.socket_recv.recv(self.drop_byte_size + 3)
        if not read_byte:
            return None;
        elif not ord(read_byte[0]) == PORT_LIKE:
            print("not a drop !!! size: {}".format(len(read_byte)))
            return None;
        # print("Read Raw Byte {}".format([ord(ii) for ii in read_byte]))
        print("Read len: {}".format(len(read_byte)))
        drop_byte = read_byte[3:]
        print("Drop Byte len {} : {}".format(len(drop_byte), [ord(ii) for ii in drop_byte]))
        return drop_byte



if __name__ == '__main__':
    if sys.argv[1] == 'send':
        stack_manager = Stack_Sender()
        stack_manager.sender_main()
    elif sys.argv[1] ==  'recv':
        stack_manager = Stack_Receiver()




