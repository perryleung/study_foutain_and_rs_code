# _*_ coding=utf-8 _*_ 
from __future__ import print_function
import sys, os
sys.path.append('./lib')
from send_recv import Sender, Receiver
from send_recv import EW_Sender, EW_Receiver
from simulation_anay import anay_dir
LEAN_IMG = './doc/lena.png'
WHALE_IMG = './doc/whale_512.bmp'
TWINS_IMG = './doc/twins_256.jpg'
UNKNOW_IMG = './doc/undwer_128.jpg'


def send_recv_demo(instruct):
    if instruct == 'send':
        send = Sender(UNKNOW_IMG, fountain_chunk_size=80)
        send.send_drops_use_socket()
    elif instruct =='recv'    :
        recv = Receiver()

def ew_send_recv_demo(instruct):
    img_file = WHALE_IMG
    if instruct == 'send':
        send = EW_Sender(img_file, fountain_chunk_size=1500, seed=18)
        send.send_drops_use_socket()
    elif instruct =='recv'    :
        recv = EW_Receiver()
        anay_dir(recv.test_dir, img_file)



if __name__ == '__main__':
    ew_send_recv_demo(sys.argv[1])
    # send_recv_demo(sys.argv[1])

