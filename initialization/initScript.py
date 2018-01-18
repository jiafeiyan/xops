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
from utils.logger.log import log

log = log.get_logger('initScript')


def initScript(mysql, path):
    log.info("============== loading init data ==============")
    __generate_table('t_Exchange', mysql, path)
    __generate_table('t_Product', mysql, path)
    __generate_table('t_ProductGroup', mysql, path)
    __generate_table('t_Market', mysql, path)
    __generate_table('t_MarketProduct', mysql, path)
    __generate_table('t_MarketProductGroup', mysql, path)
    __generate_table('t_SettlementGroup', mysql, path)
    __generate_table('t_TradeSystem', mysql, path)
    __generate_table('t_TradeSystemSettlementGroup', mysql, path)
    __generate_table('t_BusinessConfig', mysql, path)
    __generate_table('t_ClientProductRight', mysql, path)
    __generate_table('t_PartProductRight', mysql, path)
    __generate_table('t_PartProductRole', mysql, path)


# 通用生成sql语句并执行
def __generate_table(tableName, mysql, path):
    # 加载json数据文件
    path = "%s%s%s%s" % (path, os.path.sep, tableName, ".json")
    if not os.path.exists(path):
        log.error("文件" + tableName + ".json不存在")
        return
    f = open(path)
    jsonData = json.load(f)
    log.info("%s%s%s%s%s" % ("配置文件初始化数据 ", tableName, " ==> 共", len(jsonData), "条"))
    if not len(jsonData) > 0:
        log.error(tableName + "没有数据")
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
