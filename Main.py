# -*- coding: UTF-8 -*-

import argparse
import json
from pprint import pprint

from utils import oracle
from utils import mysql


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

    my = mysql(configs=conf)

    M = [
        ('3', '2', '3', '4', '5'),
        ('4', '2', '3', '4', '5'),
        ('5', '2', '3', '4', '5')
    ]
    my.executemany("Insert Into t_Account Values(%s, %s, %s, %s, %s)", M)

    fc = my.select("select * from t_Account")
    pprint(fc)

    # ora = oracle(configs=conf)

    # test select
    # fc = ora.select("Select * from t_user Where userid = :id", {"id": 1})
    # print(fc)

    # test insert
    # ora.execute("Insert Into t_User Values(:id, :username, :pwd)", {"id": 5, "username": "ee", "pwd": "hhh"})

    # test executemany
    # M = [
    #     {"id": 5, "username": "ee", "pwd": "hhh"},
    #     {"id": 5, "username": "ee", "pwd": "hhh"},
    #     {"id": 5, "username": "ee", "pwd": "hhh"}
    # ]
    # print len(M)
    # ora.executemany("Insert Into t_User Values(:id, :username, :pwd)", M)
