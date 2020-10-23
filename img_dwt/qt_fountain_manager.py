# _*_ coding=utf-8 _*_ 
from __future__ import print_function
import sys, os
BASE_DIR = os.path.dirname(__file__)
LIB_PATH = os.path.join(BASE_DIR, 'lib')
sys.path.append(LIB_PATH)
from send_recv import Sender, Receiver
from send_recv import EW_Sender, EW_Receiver


def qt_fountain_manager_send(instr):
    '''与qt界面的发送接口,通过socket传输数据'''
    img_path, interval, w1_size, w1_pro, port, packet_size= instr.split(',')
    chunk_size = int(packet_size) - 6 - int(packet_size) % 3
    sender = Sender(img_path,
            fountain_chunk_size=chunk_size,
            drop_interval=float(interval),
            port=int(port),
            w1_size=float(w1_size),
            w1_pro=float(w1_pro),
            fountain_type='ew',
            )
    sender.send_drops_use_socket()

def qt_fountain_manager_recv(instr):
    '''与qt界面的接收接口,通过socket传输数据'''
    recv_er = EW_Receiver()

if __name__ == "__main__":
    if sys.argv[1] == 'send':
        qt_fountain_manager_send(sys.argv[2])
    else:
        qt_fountain_manager_recv(sys.argv[2])
