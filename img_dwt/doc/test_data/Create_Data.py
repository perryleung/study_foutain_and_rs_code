import sys, os
LIB_PATH = os.path.dirname(__file__)

def create(name, msg):
    full_path = name + '.txt'
    file = open(full_path, 'w')
    file.write(msg)
    file.close()

if __name__ == "__main__":
    for i in range(84):
        msg = str('a' * (i+66))
        create(str(66+i),msg)
    pass