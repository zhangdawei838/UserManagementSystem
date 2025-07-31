# -*- coding: utf-8 -*-
# @Time    : 2025/7/31 15:13
# @Author  : zhangdawei
# @Version : Python 3.13
# @File    : log-mk.py
# @Software: PyCharm

import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# 创建logger对象
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# 控制台处理器 (控制台通常能较好处理编码，但也可尝试设置)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
# 控制台编码处理较复杂，通常依赖终端设置，这里先保持原样
console_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# 文件处理器（带大小轮替）- 明确指定 encoding='utf-8'
file_handler = RotatingFileHandler(
    'app.log',
    maxBytes=1024*1024,
    backupCount=5,
    encoding='utf-8'  # 👈 关键：指定编码为 UTF-8
)
file_handler.setLevel(logging.ERROR)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# 时间轮替文件处理器 - 明确指定 encoding='utf-8'
time_rotating_handler = TimedRotatingFileHandler(
    'time_app.log',
    when='midnight',
    interval=1,
    backupCount=7,
    encoding='utf-8'  # 👈 关键：指定编码为 UTF-8
)
time_rotating_handler.setLevel(logging.INFO)
time_rotating_handler.setFormatter(file_formatter)

# 添加处理器到logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.addHandler(time_rotating_handler)

# 测试日志输出
logger.debug('这是一个调试信息')
logger.info('这是一个普通信息')
logger.warning('这是一个警告信息')
logger.error('这是一个错误信息')
logger.critical('这是一个严重错误信息')


































