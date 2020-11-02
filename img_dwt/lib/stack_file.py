# _*_ coding=utf-8 _*_ 
import os, sys
import struct
import time
from math import ceil
import socket, select
import shutil
import logging
import argparse


LIB_PATH = os.path.dirname(__file__)
DOC_PATH = os.path.join(LIB_PATH, '../doc')
SIM_PATH = os.path.join(LIB_PATH, '../simulation')

sys.path.append(LIB_PATH)
from rs_image_lib import rs_encode_image, rs_decode_image

WHALE_IMG_128 = os.path.join(DOC_PATH, 'whale_128.bmp')
WHALE_128_JPG = os.path.join(DOC_PATH, 'whale_128.jpg')
FISH_128_JGP = os.path.join(DOC_PATH, "undwer_128.jpg")

PORT_LIKE = 100
NORNAL = ord('0')
SIGNIFICANT = ord('1')

SEND_ID = 1
RECV_ID = 2

BMP_TYPE = 0
JPG_TYPE = 1
RS_TYPE  = 2

HOST = '127.0.0.1'
'''
# 应用层头部
---------------------------------------------------------------------------------------------------------------
| 端口 | 关键1/普通0 | 目的节点ID | 类型BMP/JPG/RS | 数据部分大小 | 总数据包个数 | 数据包编号 |     数据部分  |
+------+-------------+------------+----------------+--------------+--------------+------------+---------------+
| 1字节|    1字节    |    1字节   |      1字节     |     1字节    |     2字节    |    2字节   | chunk_size字节|
---------------------------------------------------------------------------------------------------------------
'''

class Stack_Send_File():
    def __init__(self,
            file_path = WHALE_128_JPG, 
            chunk_size = 63,
            stack_port = 9079 + SEND_ID,
            packet_interval = 10,
            RS = False,
            ):
        self.file_path = file_path
        self.RS = RS
        self.chunk_size = chunk_size
        self.stack_port = stack_port
        self.packet_interval = packet_interval
        self.stack_fd = self.socket_builder()
        self.file_contain = self.read_file()
        self.file_size = len(self.file_contain)
        logging.info("INFO file size:{},\t chunk_size:{},\t packet_interval:{}\n file name:{}".format(
            self.file_size, self.chunk_size, self.packet_interval, self.file_path))

    def socket_builder(self):
        stack_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        stack_socket.connect((HOST, self.stack_port))
        logging.info("connect to {} ...".format(self.stack_port))
        return stack_socket

    def read_file(self):
        if self.RS :
            self.file_path = rs_encode_image(self.file_path, self.chunk_size)
        with open(self.file_path, 'rb') as file_fd:
            file_contain = file_fd.read()
        return file_contain

    def set_send_type(self):
        if self.RS :
            self.type_ = RS_TYPE
        elif ".jpg" in self.file_path:
            self.type_ = JPG_TYPE
        elif ".bmp" in self.file_path:
            self.type_ = BMP_TYPE
        else:
            logging.info("file type not support !!")
            return

    def send_main(self):
        byte_to_send = len(self.file_contain)
        send_tap = 0
        send_serial = 0
        NUM_PACKET = ceil(self.file_size / self.chunk_size)
        self.set_send_type()
        app_header = [
                PORT_LIKE,#0
                SIGNIFICANT,#1
                RECV_ID,#2
                self.type_,#3
                self.chunk_size,#4
                ]
        app_header = ''.join([struct.pack("B", ii) for ii in app_header])
        app_header += struct.pack("H", int(NUM_PACKET)) #5, 6
        while byte_to_send > 0:
            time.sleep(self.packet_interval)
            packet_to_send = app_header + \
                    struct.pack("H", send_serial) + \
                    self.file_contain[send_tap : min((send_tap + self.chunk_size), self.file_size)]#防溢出
            self.stack_fd.send(packet_to_send)
            # logging.info("send packet len {} : {}".format(len(packet_to_send), [ord(ii) for ii in packet_to_send]))
            logging.info("send {}\tall  {}".format(send_serial, NUM_PACKET))
            send_serial += 1
            send_tap += self.chunk_size
            byte_to_send -= self.chunk_size



class Stack_Recv_File():
    def __init__(self,
            stack_port = 9079 + RECV_ID,
            ):
        self.stack_port = stack_port
        self.stack_fd = self.socket_builder()
        self.testFile = time.asctime().replace(' ', '_').replace(':', '_')
        self.test_dir = os.path.join(
                SIM_PATH,
                "file_recv_dir",
                self.testFile
                )
        if not os.path.exists(self.test_dir):
            os.mkdir(self.test_dir)
        self.img_fd , self.img_name = self.img_fd_builder()
        self.drop_interval = 60
        self.recv_by_now = 0
        self.recv_packet = []

    def socket_builder(self):
        socket_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_recv.connect((HOST, self.stack_port))
        logging.info("connect to port {}".format(self.stack_port))
        return socket_recv

    def img_fd_builder(self):
        img_name = os.path.join(
                self.test_dir,
                self.testFile
                )
        img_fd = open(img_name, "wb")
        return img_fd, img_name


    def recv_main(self):
        img_time = 0
        while True:
            self.stack_fd.setblocking(0) # a socket without blocking, error shows if it occurs
            ready = select.select([self.stack_fd], [], [], self.drop_interval)
            if ready[0]:    # 仅作为判断
                read_byte = self.stack_fd.recv(999)     # 接收足够多的字节数，以保证所有被发送的数据能被接收到
                chunk_size = ord(read_byte[4])          # 获取第五个字节，chunk_size，数据部分大小
                packet_byte = self.packet_from_readByte(read_byte)
                if not packet_byte == None:
                    self.recv_by_now += 1
                    # logging.info("recv packet {} : {}".format(len(packet_byte),[ord(ii) for ii in packet_byte]))
                    send_serial = struct.unpack("H", packet_byte[7:9])[0] # 第7、8字节，数据包编号，H=unsignedshort，2bytes
                    packet_offset = chunk_size * send_serial    # 通过偏移量一个个包的数据叠加上去
                    print("********  packet_offset: %d", packet_offset) 
                    packet_nums = struct.unpack("H", packet_byte[5:7])[0] # 滴5、6字节，发送数据包总数，int类型
                    logging.info("packet serial:{}\t all packet num:{:d} recv by now: {}".format(
                        send_serial, packet_nums, self.recv_by_now))
                    logging.info('packet_offset {}'.format(packet_offset))
                    # 重置文件偏移量
                    self.img_fd.seek(0, 0)
                    self.img_fd.seek(packet_offset, 1)
                    self.img_fd.write(packet_byte[9:])      # 写入从第9个字节到末尾的所有数据
                    self.recv_packet.append(send_serial)    # 收到的数据包编号列表
                    # 开始判断是否接收到足够的包来解码，如果足够则开始以下代码
                    if self.recv_by_now >= (packet_nums - 7):   # RS in this sentance, int type
		            # if self.recv_by_now > packet_nums:	# not RS in this sentance
                        # time.sleep(10) # 防止中途有丢包收不到
                        self.img_fd.close() # 关闭文件对象
                        if ord(packet_byte[3]) == BMP_TYPE:
                            os.rename(self.img_name, self.img_name + ".bmp")
                            logging.info("recv done , img name: {}".format(self.img_name + ".bmp"))
                        elif ord(packet_byte[3]) == JPG_TYPE:
                            os.rename(self.img_name, self.img_name + ".jpg")
                            logging.info("recv done , img name: {}".format(self.img_name + ".jpg"))
                        elif ord(packet_byte[3]) == RS_TYPE:
                            img_time = img_time + 1
                            logging.info("recv done , img name: {}".format(self.img_name + ".jpg"))
                            suffix = ".jpg.rs"
                            img_name_time = self.img_name + "_" + str(img_time) +  suffix
                            shutil.copy(self.img_name, img_name_time)
                            img_name_timeRe = rs_decode_image(img_name_time, self.recv_packet)
                            logging.info("RS decode done , img name: {}".format(img_name_timeRe))
                            self.img_fd = open(self.img_name, "ab")
                        else:
                            pass
                        # break
                    logging.info("recv packet {} num : {}".format(self.recv_packet, len(self.recv_packet)))
                else:
                    logging.info("recv other port like packet and discard it")

    def packet_from_readByte(self, read_byte):
        byte_to_deal = len(read_byte)
        deal_tap = 0
        while byte_to_deal > 0:
            if not struct.unpack("B", read_byte[deal_tap])[0] == PORT_LIKE:
                byte_to_deal -= 46
            else:
                packet_size = struct.unpack("B", read_byte[deal_tap + 4])[0] # app_header
                return read_byte[deal_tap:packet_size + 5 + 2 + 2] #should be 5+2+2+packet_size
        return None    




if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO, 
            format="%(asctime)s %(filename)s:%(lineno)s %(levelname)s-%(message)s",)
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", required=True, type=str, help="send or recv", choices=['send', 'recv'])
    parser.add_argument("--RS", required=False, default=False, type=bool, help="using RS or not ,default not", choices=[True, False])
    args = parser.parse_args()
    '''

    if  sys.argv[1] == 'send':
        stack_send_file = Stack_Send_File(file_path=WHALE_IMG_128, RS=False)
        stack_send_file.send_main()
    elif sys.argv[1] ==  'recv':
        stack_recv_file = Stack_Recv_File()
        stack_recv_file.recv_main()

 
        




