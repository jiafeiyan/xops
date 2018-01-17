# -*- coding: UTF-8 -*-
"""
初始化数据库脚本
t_Exchange --
t_InstrumentGroup
t_InstrumentProperty --
t_Market
t_MarketProduct
t_MarketProductGroup
t_Product --
t_ProductGroup --
t_ProductProperty
"""

import json
import os
from utils.logger.log import log

log = log.get_logger('initScript')

def initScript(mysql, path):
    log.info("============== loading init data ==============")
    __t_Exchange(path=path, mysql=mysql)
    __t_Product(path=path, mysql=mysql)
    __t_ProductGroup(path=path, mysql=mysql)
    __t_Market(path=path, mysql=mysql)

# 初始化 t_Exchange
def __t_Exchange(path, mysql):
    __generate_table('t_Exchange', mysql, path)

# 初始化 t_Product
def __t_Product(path, mysql):
    __generate_table('t_Product', mysql, path)

# 初始化 t_ProductGroup
def __t_ProductGroup(path, mysql):
    __generate_table('t_ProductGroup', mysql, path)

# 初始化 t_Market
def __t_Market(path, mysql):
    __generate_table('t_Market', mysql, path)

# 通用生成sql语句并执行
def __generate_table(tableName, mysql, path):
    # 加载json数据文件
    path = "%s%s%s%s" % (path, os.path.sep, tableName, ".json")
    if not os.path.exists(path):
        log.error("文件" + tableName + ".json不存在")
        return
    f = open(path)
    jsonData = json.load(f)
    log.info("%s%s%s%s%s" % ("初始化数据 ", tableName, " ==> 共", len(jsonData), "条"))
    if not len(jsonData) > 0:
        log.error(tableName + "没有数据")
    template_sql = 'INSERT INTO ' + tableName + ' VALUES ('
    for _ in jsonData[0]:
        template_sql = template_sql + "%s,"
    template_sql = template_sql[0:-1] + ")"
    sql_params = []
    for data in jsonData:
        sql_params.append(data)
    mysql.executemany(template_sql, sql_params)
