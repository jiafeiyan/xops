# -*- coding: UTF-8 -*-

import tushare as ts
import datetime
import os
import pandas as pd

from pandas import DataFrame
from utils import log
from utils import parse_conf_args
from utils import path
from utils import Configuration
from utils import mysql

class stock_market:
    def __init__(self, context, configs):
        self.brokerSystemID = configs.get("brokerSystemID")
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="stock_market", configs=log_conf)
        if log_conf is None:
            self.logger.warning("stock_market未配置Log日志")
        # 初始化数据库连接
        self.mysqlDB = mysql(configs=context.get("mysql")[configs.get("mysqlId")])
        # 初始化生成柜台CSV文件路径
        output = path.convert(context.get("csv")[configs.get("csv")]['stock_exp'])
        self.csv_path = output
        # 获取行情信息并且生成csv文件
        self.__get_stock_market()

    def __get_stock_market(self):
        # 查询数据库存放的股票代码
        sql = """SELECT InstrumentID, t1.SettlementGroupID
                FROM siminfo.t_Instrument t1,siminfo.t_BrokerSystemSettlementGroup t2,siminfo.t_BrokerSystem t3
                WHERE t1.SettlementGroupID = t2.SettlementGroupID
                AND t2.BrokerSystemID = t3.BrokerSystemID
                AND t3.BrokerSystemID = %s"""
        stock_list = []
        stock_df = []
        for stock in self.mysqlDB.select(sql, (self.brokerSystemID,)):
            stock_list.append(str(stock[0]))
            stock_df.append([str(stock[0]), str(stock[1])])
        stock_df = DataFrame(stock_df, columns=['code', 'SettlementGroupID'])
        # 获取所有行情信息
        stock_market_list = ts.get_today_all()
        # 匹配数据库存在的行情
        filter_stock = stock_market_list[stock_market_list['code'].isin(stock_list)]
        # 筛选字段
        filter_stock = filter_stock.loc[:, ['code', 'trade', 'open', 'high', 'low', 'settlement', 'volume', 'amount']]
        # 合并两个DataFrame，左连接
        merge = pd.merge(filter_stock, stock_df, on='code', how='left')

        # 如果不存在目录则先创建
        if not os.path.exists(str(self.csv_path)):
            os.makedirs(str(self.csv_path))
        now = datetime.datetime.now().strftime("%Y%m%d")
        merge.to_csv(self.csv_path + os.path.sep + "stock_exp" + now + ".csv", index=False, sep=",")
        self.logger.info("生成 stock_exp" + now + ".csv 完成")

if __name__ == '__main__':
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql", "log", "csv"])
    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)
    # 启动etf脚本
    stock_market(context=context, configs=conf)