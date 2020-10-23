# _*_ coding=utf-8 _*_ 
from __future__ import print_function
import os
import sys
sys.path.append('./lib')
from  dwt_lib import *
import matplotlib.pyplot as plt
from PIL import *
from fountain_lib import Fountain, Glass, fillAmt
from spiht_main import test_main
from time import sleep

LIB_PATH = os.path.dirname(__file__)
DOC_PATH = os.path.join(LIB_PATH, './doc')

FILENAME = 'lena.png'
FOUNTAIN_TEXT = 'fountain.txt'

glasses = {}    
def main():
    img = load_img(FILENAME)
    coeff = extract_rgb_coeff(img)
    img_new = recontract_img_from_dwt_coef(coeff)

    img_plot = plt.imshow(img_new)
    plt.show()
    # img_new.save('leana_new.png')

def test_fountain():
    """ 测试喷泉吗的简单demo， 从文件中读取数据作为喷泉吗编解码使用的数据"""
    glass_id = 233
    m = open(os.path.join(DOC_PATH, FOUNTAIN_TEXT), 'r').read()
    my_fountain = Fountain(m)
    my_glass = Glass(my_fountain.num_chunks)
    while my_glass.getString() != m:
        #  fillAmt(my_fountain, my_glass, 10)
        #  my_glass.addDroplet(my_fountain.droplet())
        a_drop = my_glass.droplet_from_Bytes(my_fountain.droplet().toBytes())
        my_glass.addDroplet(a_drop)
        sleep(2)
        #  print 'add 10 drop'
        print('+++++++++++++++++++++++++++++')
        print(my_glass.getString())
    print('done')

def plan_A():

    pass


if __name__ == '__main__':
    test_fountain()
    #  spiht_test()

