# -*- coding: UTF-8 -*-

from utils import parse_args
from utils import load
from utils import mysql
from datatrans import trans_stockinfo
from datatrans import trans_futureinfo
from initialization import initScript

if __name__ == '__main__':
    args = parse_args()

    # 读取参数文件
    conf = load(args.conf)

    # 建立mysql数据库连接
    mysql_instance = mysql(configs=conf)
    conf["db_instance"] = mysql_instance

    # 初始化脚本数据
    initScript(conf)

    # 启动stock脚本
    trans_stockinfo(conf)
    # 启动future脚本
    trans_futureinfo(conf)
