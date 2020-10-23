# img_dwt


## 操作指南
- 安装环境
    - 安装 anaconda2 
    - 安装 anaconda2 里 python 调用 MATLAB 的接口
    - 其他的python 库均可使用 pip install XXX 搞掂
- 图片发送步骤
    - 启动信道： cd XX/tornadoChannel && python tornadoChannel.py
    - 启动stack 节点：
        - cd XX/stack
        - 检查各层协议配置情况moduleconfig.h，物理层需要是仿真信道， MAC是fountain_aloha
        - 检查不同节点的节点的配置文件configA.yaml等，需要用几个节点检查几个
            - 关闭测试模式
            - 检查静态路由配置情况
            - MAC层的超时重发时间间隔
            - 等等
        - 运行节点：./RoastFish configA.yaml等， 需要用几个节点就运行几个节点
    - 启动图像发送部分应用层
        - cd XX/img_dwt/lib
        - 运行发送端程序 ~/anaconda2/bin/ipython stack_manager.py send
        - 运行接收端程序 ~/anaconda2/bin/ipython stack_manager.py recv
- 看日志和图像接收效果

to do:
- [ ] 一跳到5跳本方案的实验数据
    - [ ] 实验
    - [ ] 性能分析
- [ ] 对比方案
    - [ ] BMP 收发图片原始文件
    - [ ] JPG + RS 码收发图像 : 码率选择RS(255, 223)
        - [ ] 横向 RS 编码：肯定会增加传输的数据量
        - [ ] 纵向 RS 编码：会有点麻烦
- [ ] QPSK 和 MFSK 的比较

#实验数据
- 1
	-  data size :  8132
	send drop num :  352 drop size :  50
	send data size :  17600
	scale :  0.462045454545
- 2 
	- data size :  8132
	send drop num :  300 drop size :  50
	send data size :  15000
	scale :  0.542133333333



喷泉码，小波变换，SPIHT


论文结构
- 摘要
- 第一章，简介
- 第二章，背景介绍
    - 小波变换，spiht
    - 喷泉码
    - 不平等差错保护
- 第三章，别人的做法
- 第四章，自己的工作
    - 提出的方案
    - 协议栈开发
    - 软著
    - best demo award
- 第五章，仿真，结论

to do：
- [ ] 完整地完成自己的方案(deadline : 2月24)
    - [ ] 标准喷泉码改为扩展窗喷泉码
    - [ ] 图片处理部分和喷泉码部分整合
- [ ] 寻找角度对比性能优势
- [ ] 写第一章和第二章综述

PPT结构
- 喷泉码
	- LT 码
- 图像渐进传输
	- 小波变换
	- SPIHT

topic : 基于喷泉码的不平等差错保护的跨层设计

关键词：喷泉码，小波变换，SPIHT，渐进传输，跨层，图片，UEP(不平等的差错保护)

涉及到的算法：喷泉码，小波变换，SPIHT
涉及到的概念：渐进传输，跨层交互，图片传输，UEP(不平等差错保护)

idea:
- [ ] APP layer : 
    - 算法
        - 小波变换 + SPIHT
        - 喷泉码

to do:
- [x] 安装x-mind，画思维导图汇报设计方案
- [ ] 实现加权喷泉码
- [x] 实现理想弧波分布函数和鲁棒弧波分布函数
- [x] 了解加权喷泉码 (weighted approach) 和 扩展窗喷泉码(Expanding Window Fountain, EWF)，最后看喷泉码实现的UEP在渐进传输中的应用，针对水声场景进行一些参数优化
- [ ] 一天或半天去尝试下 [轮子](https://github.com/juancgalan/VideoBWT/blob/master/python/src/create_spiht_batch.py)
- [x] 将编码输出的二进制文件使用喷泉码发送
- [x] 适应不同大小的非正方形的图片
    - 头部信息增加图片长宽，小波类型，小波变换模式，
