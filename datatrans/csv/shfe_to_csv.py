# -*- coding: UTF-8 -*-

"""
生成CSV文件
"""

import csv
import os

from utils import log
from utils import parse_conf_args
from utils import Configuration
from utils import mysql


class shfe_to_csv:
    def __init__(self, context, configs):
        # 初始化settlementGroupID
        self.settlementGroupID = configs.get("settlementGroupID")
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="future_to_csv", configs=log_conf)
        if log_conf is None:
            self.logger.warning("shfe_to_csv未配置Log日志")
        # 初始化数据库连接
        self.mysqlDB = mysql(configs=context.get("mysql")[configs.get("mysqlId")])
        # 初始化生成柜台CSV文件路径
        self.csv_path = context.get("csv")[configs.get("csv")]['counter'] + os.path.sep + "future_shfe"
        self.__to_csv()

    def __to_csv(self):
        mysqlDB = self.mysqlDB
        self.__data_to_csv("TradingCodeMap", mysqlDB)
        self.__data_to_csv("TradingUser", mysqlDB)

    def __data_to_csv(self, csv_name, mysqlDB):
        table_sqls = dict(
            TradingCodeMap=dict(),
            TradingUser=dict(columns=("BrokerID", "UserID", "Password", "DRIdentityID", "UserType"),
                             sql="""select t1.BrokerSystemID as BrokerID,t.InvestorID as UserID,
                                            t.`Password` as Password,'1' as DRIdentityID,'0' as UserType
                                    from t_Investor t, t_BrokerSystemSettlementGroup t1
                                    where t1.SettlementGroupID = %s""",
                             params=(self.settlementGroupID,)),
        )
        # 查询siminfo数据库数据内容
        csv_data = mysqlDB.select(table_sqls[csv_name]["sql"], table_sqls[csv_name].get("params"))
        # 生成csv文件
        self.__produce_csv(csv_name, table_sqls[csv_name], csv_data)

    # 生成csv文件
    def __produce_csv(self, csv_name, columns, csv_data):
        self.logger.info("%s%s%s" % ("开始生成 ", csv_name, ".csv"))
        path = "%s%s%s%s" % (str(self.csv_path), os.path.sep, csv_name, '.csv')
        # 如果不存在目录则先创建
        if not os.path.exists(str(self.csv_path)):
            os.makedirs(str(self.csv_path))
        with open(path, 'wb') as csvfile:
            if "quoting" in columns and columns['quoting']:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            else:
                writer = csv.writer(csvfile)
            writer.writerow(columns['columns'])
            writer.writerows(csv_data)
        self.logger.info("%s%s%s" % ("生成 ", csv_name, ".csv 文件完成"))


if __name__ == '__main__':
    base_dir, config_names, config_files = parse_conf_args(__file__, config_names=["mysql", "csv"])
    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)
    # 启动脚本
    shfe_to_csv(context=context, configs=conf)
