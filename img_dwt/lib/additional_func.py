import numpy as np
def first_degree_distribution_func():
        #Liu Yachen, 5.4
        d = [1, 2, 3, 4, 5, 8, 9, 19, 65, 66]
        d_f = [0.0266, 0.5021, 0.0805, 0.1388, 0.0847, 0.046, 0.0644, 0.0326, 0.0205, 0.0038]
        while True:
            i = np.random.choice(d, 1, False, d_f)[0]
            yield i

def second_degree_distribution_func():
        #Shokrollahi, 5.78
        d = [1, 2, 3, 4, 5, 8, 9, 19, 65, 66]
        d_f = [0.007969, 0.49357, 0.16622, 0.072646, 0.082558, 0.056058, 0.037299, 0.05559, 0.025023, 0.003135]
        while True:
            i = np.random.choice(d, 1, False, d_f)[0]
            yield i

def third_degree_distribution_func():
        #Liu Cong, 5.8703
        d = [1, 2, 3, 4, 5, 8, 9, 19, 65, 66]
        d_f = [0.0266, 0.5021, 0.0805, 0.1388, 0.0847, 0.046, 0.0644, 0.0326, 0.0205, 0.0038]
        while True:
            i = np.random.choice(d, 1, False, d_f)[0]
            yield i