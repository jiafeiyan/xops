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


class etf_to_csv:
    def __init__(self, context, configs):
        # 初始化settlementGroupID
        self.settlementGroupID = configs.get("settlementGroupID")
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="future_to_csv", configs=log_conf)
        if log_conf is None:
            self.logger.warning("etf_to_csv未配置Log日志")
        # 初始化数据库连接
        self.mysqlDB = mysql(configs=context.get("mysql")[configs.get("mysqlId")])
        # 初始化生成柜台CSV文件路径
        self.csv_path = context.get("csv")[configs.get("csv")]['counter'] + os.path.sep + "stock_etf"
        self.__to_csv()

    def __to_csv(self):
        mysqlDB = self.mysqlDB
        self.__data_to_csv("BUProxy", mysqlDB)
        self.__data_to_csv("BusinessUnit", mysqlDB)
        self.__data_to_csv("ExchangeTradingDay", mysqlDB)
        self.__data_to_csv("Investor", mysqlDB)
        self.__data_to_csv("InvestorLimitAmount", mysqlDB)
        self.__data_to_csv("SSEBusinessUnitAccount", mysqlDB)

    def __data_to_csv(self, csv_name, mysqlDB):
        table_sqls = dict(
            BUProxy=dict(columns=("UserID", "InvestorID", "BusinessUnitID"),
                         sql="""SELECT InvestorID AS UserID,InvestorID AS InvestorID,InvestorID AS BusinessUnitID
                                        FROM siminfo.t_Investor"""),
            BusinessUnit=dict(columns=("InvestorID", "BusinessUnitID", "BusinessUnitName"),
                              sql="""SELECT InvestorID,InvestorID AS BusinessUnitID,
                                      CONCAT('BU', InvestorID) AS BusinessUnitName FROM siminfo.t_Investor"""),
            ExchangeTradingDay=dict(columns=("ExchangeID", "TradingDay"),
                                    sql="""SELECT t1.ExchangeID, t.TradingDay
                                               FROM siminfo.t_TradeSystemTradingDay t, siminfo.t_SettlementGroup t1,
                                                    t_TradeSystemSettlementGroup t2
                                               WHERE t.TradeSystemID = t2.TradeSystemID
                                               AND t2.SettlementGroupID = t1.SettlementGroupID
                                               AND t1.SettlementGroupID=%s""",
                                    params=(self.settlementGroupID,)),
            Investor=dict(columns=("InvestorID", "DepartmentID", "InvestorType", "InvestorName", "IdCardType",
                                   "IdCardNo", "ContractNo", "OpenDate", "CloseDate", "Status", "InnerBranchID",
                                   "InvestorLevel", "Remark"),
                          sql="""SELECT InvestorID,'0001' AS DepartmentID,'0' AS InvestorType,InvestorName,
                                        '1' AS IdCardType,OpenID AS IdCardNo,'' AS ContractNo,'' AS OpenDate,
                                        '' AS CloseDate,'1' AS STATUS,'2023' AS InnerBranchID,'1' AS InvestorLevel,
                                        '' AS Remark
                                    FROM siminfo.t_Investor"""),
            InvestorLimitAmount=dict(columns=("InvestorID", "LongAmountLimit", "LongAmountFrozen"),
                                     sql="""SELECT InvestorID,'10000000000' AS LongAmountLimit,'0' AS LongAmountFrozen
                                            FROM siminfo.t_Investor"""),
            SSEBusinessUnitAccount=dict(columns=("UserID", "InvestorID", "BusinessUnitID", "ExchangeID",
                                                 "MarketID", "ShareholderID", "ShareholderIDType", "ProductID",
                                                 "AccountID", "CurrencyID"),
                                        sql="""SELECT t3.UserID,t.InvestorID AS InvestorID,
                                                    t.InvestorID AS BusinessUnitID,t1.ExchangeID AS ExchangeID,
                                                    t2.MarketID AS MarketID,t.ClientID AS ShareholderID,
                                                    '3' as ShareholderIDType,'d' AS ProductID,t.InvestorID AS AccountID,
                                                    t1.Currency AS CurrencyID
                                                FROM siminfo.t_InvestorClient t,siminfo.t_SettlementGroup t1,
                                                    siminfo.t_Market t2,siminfo.t_User t3
                                                WHERE t.SettlementGroupID = t1.SettlementGroupID
                                                AND t1.SettlementGroupID = t2.SettlementGroupID
                                                AND t3.SettlementGroupID = t.SettlementGroupID
                                                AND t1.SettlementGroupID = %s""",
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
    etf_to_csv(context=context, configs=conf)
