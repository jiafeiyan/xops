# -*- coding: UTF-8 -*-
"""
初始化数据库脚本
t_ProductProperty
t_Exchange --
t_InstrumentProperty --
t_Market --
t_MarketProduct --
t_MarketProductGroup --
t_Product --
t_ProductGroup --
t_TradeSystem --
t_TradeSystemSettlementGroup --
t_BusinessConfig --
t_ClientProductRight --
t_PartProductRight --
t_PartProductRole --
"""

import json
import os

from utils import log
from utils import parse_args
from utils import load
from utils import mysql

class initScript:
    def __init__(self, configs):
        if "Log" in configs:
            self.logger = log.get_logger(category="initScript",
                                         file_Path=configs["Log"]["file_path"],
                                         console_level=configs["Log"]["console_level"],
                                         file_level=configs["Log"]["file_level"])
        else:
            self.logger = log.get_logger(category="initScript")
        self.configs = configs
        self.__load()

    def __load(self):
        self.logger.info("============== loading init data ==============")
        mysql = self.configs['db_instance']
        path = self.configs['Path']['initialize']
        self.__generate_table('t_Exchange', mysql, path)
        self.__generate_table('t_Product', mysql, path)
        self.__generate_table('t_ProductGroup', mysql, path)
        self.__generate_table('t_Market', mysql, path)
        self.__generate_table('t_MarketProduct', mysql, path)
        self.__generate_table('t_MarketProductGroup', mysql, path)
        self.__generate_table('t_SettlementGroup', mysql, path)
        self.__generate_table('t_TradeSystem', mysql, path)
        self.__generate_table('t_TradeSystemSettlementGroup', mysql, path)
        self.__generate_table('t_BusinessConfig', mysql, path)
        self.__generate_table('t_ClientProductRight', mysql, path)
        self.__generate_table('t_PartProductRight', mysql, path)
        self.__generate_table('t_PartProductRole', mysql, path)

    # 通用生成sql语句并执行
    def __generate_table(self, tableName, mysql, path):
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
        mysql.execute("DELETE FROM " + tableName)
        # 插入数据
        mysql.executemany(template_sql, sql_params)


if __name__ == '__main__':
    args = parse_args()

    # 读取参数文件
    conf = load(args.conf)

    # 建立mysql数据库连接
    mysql_instance = mysql(configs=conf)
    conf["db_instance"] = mysql_instance

    # 初始化脚本数据
    initScript(conf)
