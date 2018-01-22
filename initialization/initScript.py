# -*- coding: UTF-8 -*-
"""
初始化数据库脚本
t_Exchange
t_Product
t_ProductGroup
t_Market
t_MarketProduct
t_MarketProductGroup
t_SettlementGroup
t_TradeSystem
t_TradeSystemSettlementGroup
t_BusinessConfig
t_ClientProductRight
t_PartProductRight
t_PartProductRole
t_BrokerSystem
t_BrokerSystemSettlementGroup
t_Participant
t_Account
t_TradingAccount
t_ClearingTradingPart
t_TradeSystemBrokerSystem
"""

import json
import os

from utils import log
from utils import parse_args
from utils import load
from utils import mysql

class initScript:
    def __init__(self, configs):
        self.logger = log.get_logger(category="initScript", configs=configs)
        self.configs = configs
        self.__load()

    def __load(self):
        self.logger.info("============== loading init data ==============")
        mysqlDB = self.configs['db_instance']
        path = self.configs['Path']['initialize']
        if os.path.exists(path):
            for fileName in os.listdir(path):
                fileName = fileName[:fileName.rfind('.')]
                self.__generate_table(str(fileName), mysqlDB, path)

    # 通用生成sql语句并执行
    def __generate_table(self, tableName, mysqlDB, path):
        # 加载json数据文件
        path = "%s%s%s%s" % (path, os.path.sep, tableName, ".json")
        if not os.path.exists(path):
            self.logger.error("文件" + tableName + ".json不存在")
            return
        f = open(path)
        jsonData = json.load(f)
        self.logger.info("%s%s%s%s%s" % ("配置文件初始化数据 ", tableName, " ==> 共", len(jsonData), "条"))
        if not len(jsonData) > 0:
            self.logger.error(tableName + "没有数据")
        template_sql = 'INSERT INTO ' + tableName + ' VALUES ('
        for _ in jsonData[0]:
            template_sql = template_sql + "%s,"
        template_sql = template_sql[0:-1] + ")"
        sql_params = []
        for data in jsonData:
            sql_params.append(data)
        # 插入配置数据之前，先清空表
        mysqlDB.execute("DELETE FROM " + tableName)
        # 插入数据
        mysqlDB.executemany(template_sql, sql_params)


if __name__ == '__main__':
    args = parse_args()

    # 读取参数文件
    conf = load(args.conf)

    # 建立mysql数据库连接
    mysql_instance = mysql(configs=conf)
    conf["db_instance"] = mysql_instance

    # 初始化脚本数据
    initScript(conf)
