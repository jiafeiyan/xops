# -*- coding: UTF-8 -*-
import logging
import sys
import datetime


class log:
    def __init__(self):
        pass

    # ERROR
    # WARNING
    # INFO
    # DEBUG
    @staticmethod
    def get_logger(category, configs=None):
        # 默认设置
        file_path = None
        console_level = logging.INFO
        file_level = logging.INFO

        # 读取配置
        if configs is not None and "Log" in configs:
            file_path = configs['Log']['file_path']
            console_level = configs['Log']['console_level']
            file_level = configs['Log']['file_level']

        logger = logging.getLogger(category)
        # 设置全局日志级别
        logger.setLevel(logging.DEBUG)

        # 自定义输出格式
        formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: '
                                      '%(message)s')

        # 创建一个handler，用于输出到console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 创建一个handler，用于写入日志文件
        if file_path != "" and file_path is not None:
            nowTime = datetime.datetime.now().strftime("%Y_%m_%d")
            file_Path = "%s%s%s%s" % (file_path, "logger_", nowTime, ".txt")
            file_handler = logging.FileHandler(file_Path, mode='a')
            file_handler.setLevel(file_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger
