from rs_image_lib import rs_encode_image
import os, sys


LIB_PATH = os.path.dirname(__file__)
DOC_PATH = os.path.join(LIB_PATH, '../doc')
WHALE_128_JPG = os.path.join(DOC_PATH, "whale_128.jpg")

if __name__ == "__main__":
    print(rs_encode_image(WHALE_128_JPG, 66)) 
