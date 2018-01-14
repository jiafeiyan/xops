# -*- coding: UTF-8 -*-
import logging
import sys


class log:
    def __init__(self):
        pass

    # ERROR
    # WARNING
    # INFO
    # DEBUG
    @staticmethod
    def get_logger(category, verbose=logging.INFO):
        logger = logging.getLogger(category)
        logger.setLevel(verbose)

        # 创建一个handler，用于输出到console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(verbose)

        # 创建一个handler，用于写入日志文件
        logfile = './logger.txt'
        file_handler = logging.FileHandler(logfile, mode='w')
        file_handler.setLevel(logging.DEBUG)

        # 自定义输出格式
        formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: '
                                                      '%(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # 添加handler
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger


if __name__ == '__main__':
    m = log.get_logger("123")
    m.info("abc")
