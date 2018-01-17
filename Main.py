# -*- coding: UTF-8 -*-

import argparse
import json

from utils import mysql
from datatrans import trans_start
from initialization import initScript


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-conf')
    return parser.parse_args()


# 获取config配置文件
def getConfig(filename):
    f = open(filename)
    config = json.load(f)
    return config


if __name__ == '__main__':
    args = parse_args()
    if not args.conf:
        print ("缺少参数 -conf")
        exit()

    conf = getConfig(args.conf)
    mysql = mysql(configs=conf)

    initScript.initScript(mysql=mysql, path=conf["Init"]["path"])
    # trans_start.init(mysql=mysql)
