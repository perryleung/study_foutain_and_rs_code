import numpy as np
from math import log

def soliton(K):
#''' 理想弧波函数 '''
    d = [ii + 1 for ii in range(K)] # a list with 1 ~ K 
    d_f = [1.0 / K if ii == 1 else 1.0 / (ii * (ii - 1)) for ii in d]
    while 1:
        # i = np.random.choice(d, 1, False, d_f)[0]
        yield np.random.choice(d, 1, False, d_f)[0]

def robust_soliton(K, c = 0.03, delta = 0.05):
#''' 鲁棒理想弧波函数 '''
    d = [ii + 1 for ii in range(K)]
    soliton_d_f = [1.0 / K if ii == 1 else 1.0 / (ii * (ii - 1)) for ii in d]
    S = c * log(K / delta) * (K ** 0.5)
    interval_0 = [ii + 1 for ii in list(range(int(round(K / S)) - 1))]
    interval_1 = [int(round(K / S))]
    tau = [S / (K * dd) if dd in interval_0 
            else S / float(K) * log(S / delta) if dd in interval_1
            else 0 for dd in d]
    Z = sum([soliton_d_f[ii] + tau[ii] for ii in range(K)])
    u_d_f = [(soliton_d_f[ii] + tau[ii]) / Z for ii in range(K)]

    while True :
        # i = np.random.choice(d, 1, False, u_d_f)[0]
        yield np.random.choice(d, 1, False, u_d_f)[0]

def first_degree_distribution_func():
#'''Liu Yachen, 5.4'''
    d = [1, 2, 3, 4, 5, 8, 9, 19, 65, 66]
    d_f = [0.0266, 0.5021, 0.0805, 0.1388, 0.0847, 0.046, 0.0644, 0.0326, 0.0205, 0.0038]
    while True:
        i = np.random.choice(d, 1, False, d_f)[0]
        yield i

def second_degree_distribution_func():
#'''Shokrollahi, 5.78'''
    d = [1, 2, 3, 4, 5, 8, 9, 19, 65, 66]
    d_f = [0.007969, 0.49357, 0.16622, 0.072646, 0.082558, 0.056058, 0.037229, 0.05559, 0.025023, 0.003137]
    while True:
        i = np.random.choice(d, 1, False, d_f)[0]
        yield i

def mrds_func(K, b = 0.7, n = 3, c = 0.05, delta = 0.05,a = 0.6):
#'''Liu Cong, 5.8703'''
    d_1 = [1, 2, 3, 4, 5, 8, 9, 19, 65, 66]
    d = [ii + 1 for ii in range(K)]
    #d_1_f = [0.149598, 0.49357, 0.0071721, 0.00653814, 0.0743022, 0.0504522, 0.0335061, 0.050031, 0.0225207, 0.078858]
    d_1_f = [0.149598, 0.49357, 0.0071721, 0.00653814, 0.0743022, 0.0504522, 0.0335061, 0.050031, 0.0225207, 0.11230956]
    soliton_d_f = [((1.0-b*(1.0-1.0/(K-n+2)))/(n-1)) if ii >= 1 and ii <= (n-1) else b / (ii-n+1) for ii in d]
    S = c * log(K / delta) * (K ** 0.5)
    interval_0 = [ii + 1 for ii in list(range(int(round(K / S)) - 1))]
    interval_1 = [int(round(K / S))]
    tau = [S / (K * dd) if dd in interval_0 
            else S / float(K) * log(S / delta) if dd in interval_1
            else 0 for dd in d]
    Z = sum([soliton_d_f[ii] + tau[ii] for ii in range(K)])
    u_d_f = [(soliton_d_f[ii] + tau[ii]) * a / Z for ii in range(K)]
    d_1_f_tmp = [ii * (1 - a) for ii in d_1_f]
    tmp = 0
    for ii in d_1:
        u_d_f[ii-1] = u_d_f[ii-1] + d_1_f_tmp[tmp]
        tmp = tmp + 1
    while True:
        i = np.random.choice(d, 1, False, u_d_f)[0]
        yield i

def binary_exp_func(k):
#''' 二进制指数度分布函数 '''
    d = [ii + 1 for ii in range(k)] 
    d_f = [1.0 / 2**(k-1) if ii == k else 1.0 / (2 ** ii) for ii in d]
    while True:
        # i = np.random.choice(d, 1, False, d_f)[0]
        yield np.random.choice(d, 1, False, d_f)[0]

def open_distrubution_func(i, a, k):
#开关度分布函数
#i：LT码编码包ID
#a：开关系数
    while True:
        if i <= a * k:
            yield binary_exp_func(k)
        else:
            yield robust_soliton(k)

def uniform_distribution_func(k):
    d = [ii + 1 for ii in range(k)]  # 1 ~ k
    d_f = [1.0 / k for ii in d]
    while True:
        yield np.random.choice(d, 1, False, d_f)[0]

def poisson_func(k):
    d = [1, 2, 3, 4, 5, 8, 9, 19, 65, 66]
    tmp = 1.0 / (k * log(k))
    d_f = [0.003269+65*tmp, 0.49357-17*tmp, 0.16622-33*tmp, 0.072646-15*tmp, 0.082558-tmp, 0.056028-9*tmp, 0.037229+8*tmp, 0.05559, 0.029723-tmp, 0.003167+3*tmp]
    while True:
        yield np.random.choice(d, 1, False, d_f)[0]