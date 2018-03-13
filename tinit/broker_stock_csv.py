# -*- coding: UTF-8 -*-

"""
生成CSV文件
"""

import csv
import os

from utils import log
from utils import parse_conf_args
from utils import path
from utils import Configuration
from utils import mysql
from utils import csv_tool

class broker_stock_csv:
    def __init__(self, context, configs):
        # 初始化settlementGroupID
        self.brokerSystemID = configs.get("brokerSystemID")
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="sse_to_csv", configs=log_conf)
        if log_conf is None:
            self.logger.warning("broker_stock_csv未配置Log日志")
        # 初始化数据库连接
        self.mysqlDB = mysql(configs=context.get("mysql")[configs.get("mysqlId")])
        # 初始化生成柜台CSV文件路径
        output = path.convert(context.get("csv")[configs.get("csv")]['broker'])
        self.csv_path = os.path.join(output, str(configs.get("csvRoute")))
        self.__to_csv()

    def __to_csv(self):
        mysqlDB = self.mysqlDB
        self.__data_to_csv("BusinessUnit", mysqlDB)
        self.__data_to_csv("BUProxy", mysqlDB)
        self.__data_to_csv("ExchangeTradingDay", mysqlDB)
        self.__data_to_csv("Investor", mysqlDB)
        self.__data_to_csv("TradingAccount", mysqlDB)
        self.__data_to_csv("TradingAgreement", mysqlDB)
        self.__data_to_csv("User", mysqlDB)

    def __data_to_csv(self, csv_name, mysqlDB):
        table_sqls = dict(
            BUProxy=dict(columns=("UserID", "InvestorID", "BusinessUnitID"),
                         sql="""SELECT t.InvestorID AS UserID,t.InvestorID AS InvestorID,t.InvestorID AS BusinessUnitID
                                FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1,
                                     siminfo.t_BrokerSystemSettlementGroup t2
                                WHERE t.InvestorID = t1.InvestorID
                                AND t1.SettlementGroupID = t2.SettlementGroupID AND t2.BrokerSystemID = %s
                                UNION ALL
                                SELECT 'broker' AS UserID,t.InvestorID AS InvestorID,t.InvestorID AS BusinessUnitID
                                FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1,
                                     siminfo.t_BrokerSystemSettlementGroup t2
                                WHERE t.InvestorID = t1.InvestorID
                                AND t1.SettlementGroupID = t2.SettlementGroupID AND t2.BrokerSystemID = %s
                                UNION ALL
                                SELECT 'broker1' AS UserID,t.InvestorID AS InvestorID,t.InvestorID AS BusinessUnitID
                                FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1,
                                     siminfo.t_BrokerSystemSettlementGroup t2
                                WHERE t.InvestorID = t1.InvestorID
                                AND t1.SettlementGroupID = t2.SettlementGroupID AND t2.BrokerSystemID = %s
                                UNION ALL
                                SELECT 'admin' AS UserID,t.InvestorID AS InvestorID,t.InvestorID AS BusinessUnitID
                                FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1,
                                     siminfo.t_BrokerSystemSettlementGroup t2
                                WHERE t.InvestorID = t1.InvestorID
                                AND t1.SettlementGroupID = t2.SettlementGroupID AND t2.BrokerSystemID = %s
                                UNION ALL
                                SELECT 'admin1' AS UserID,t.InvestorID AS InvestorID,t.InvestorID AS BusinessUnitID
                                FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1,
                                     siminfo.t_BrokerSystemSettlementGroup t2
                                WHERE t.InvestorID = t1.InvestorID
                                AND t1.SettlementGroupID = t2.SettlementGroupID AND t2.BrokerSystemID = %s""",
                         params=(self.brokerSystemID, self.brokerSystemID, self.brokerSystemID,
                                 self.brokerSystemID, self.brokerSystemID)),
            BusinessUnit=dict(columns=("InvestorID", "BusinessUnitID", "BusinessUnitName"),
                              sql="""SELECT t.InvestorID,t.InvestorID AS BusinessUnitID,'Bu1' AS BusinessUnitName
                                    FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1,
                                         siminfo.t_BrokerSystemSettlementGroup t2
                                    WHERE t.InvestorID = t1.InvestorID
                                    AND t1.SettlementGroupID = t2.SettlementGroupID
                                    AND t2.BrokerSystemID = %s""",
                              params=(self.brokerSystemID,)),
            ExchangeTradingDay=dict(columns=("ExchangeID", "TradingDay"),
                                    sql="""SELECT DISTINCT 0 AS ExchangeID,t.TradingDay
                                        FROM t_TradeSystemTradingDay t,t_TradeSystemSettlementGroup t1,
                                            t_BrokerSystemSettlementGroup t2
                                        where t.TradeSystemID = t1.TradeSystemID
                                            AND t1.SettlementGroupID = t2.SettlementGroupID
                                        AND t2.BrokerSystemID = %s
                                        UNION ALL
                                            SELECT CASE
                                            WHEN t2.ExchangeID LIKE 'SSE' THEN '1'
                                            WHEN t2.ExchangeID LIKE 'SZSE' THEN '2'
                                            END AS ExchangeID,t.TradingDay
                                        FROM siminfo.t_TradeSystemTradingDay t,siminfo.t_TradeSystemSettlementGroup t1,
                                            siminfo.t_SettlementGroup t2,siminfo.t_BrokerSystemSettlementGroup t3
                                        WHERE t.TradeSystemID = t1.TradeSystemID
                                        AND t1.SettlementGroupID = t2.SettlementGroupID
                                        AND t2.SettlementGroupID = t3.SettlementGroupID
                                        AND t3.BrokerSystemID = %s""",
                                    params=(self.brokerSystemID,self.brokerSystemID)),
            Investor=dict(columns=("InvestorID", "DepartmentID", "InvestorType", "InvestorName", "IdCardType",
                                   "IdCardNo", "ContractNo", "BirthDate", "Gender", "Professional", "Country",
                                   "TaxNo", "LicenseNo", "RegisteredCapital", "RegisteredCurrency", "Mobile",
                                   "RiskLevel", "Remark", "OpenDate", "CloseDate", "Status", "Contacter", "Fax",
                                   "Telephone", "Email", "Address", "ZipCode", "InnerBranchID", "Operways"),
                          sql="""SELECT DISTINCT t.InvestorID,'0001' AS DepartmentID,'0' AS InvestorType,
                                        t.InvestorName,'1' AS IdCardType,t.OpenID AS IdCardNo,'' AS ContractNo,
                                        '' AS BirthDate,'' AS Gender,'' AS Professional,'' AS Country,'' AS TaxNo,
                                        '' AS LicenseNo,'0' AS RegisteredCapital,'' AS RegisteredCurrency,'' AS Mobile,
                                        '' AS RiskLevel,'' AS Remark,'' AS OpenDate,'' AS CloseDate,'1' AS STATUS,
                                        '' AS Contacter,'' AS Fax,'' AS Telephone,'' AS Email,'' AS Address,
                                        '' AS ZipCode,'' AS InnerBranchID,'' AS Operways
                                    FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1,
                                         siminfo.t_BrokerSystemSettlementGroup t2
                                    WHERE t.InvestorID = t1.InvestorID
                                    AND t1.SettlementGroupID = t2.SettlementGroupID
                                    AND t2.BrokerSystemID = %s""",
                          params=(self.brokerSystemID,)),
            TradingAccount=dict(columns=("AccountID", "CurrencyID", "AccountType", "PreDeposit", "UsefulMoney",
                                         "FetchLimit", "Deposit", "Withdraw", "FrozenMargin", "FrozenCash",
                                         "FrozenCommission", "CurrMargin", "Commission", "RoyaltyIn", "RoyaltyOut",
                                         "AccountOwner", "DepartmentID"),
                                sql="""SELECT t.InvestorID AS AccountID,'CNY' AS CurrencyID,'1' AS AccountType,
                                            t.Available AS PreDeposit,t.Available AS UsefulMoney,
                                            t.Available AS FetchLimit,t.Deposit AS Deposit,t.Withdraw AS Withdraw,
                                            '0' AS FrozenMargin,'0' AS FrozenCash,'0' AS FrozenCommission,
                                            '0' AS CurrMargin,'0' AS Commission,'0' AS RoyaltyIn,'0' AS RoyaltyOut,
                                            t.InvestorID AS AccountOwner,'0001' AS DepartmentID
                                        FROM siminfo.t_InvestorFund t WHERE t.BrokerSystemID = %s""",
                                params=(self.brokerSystemID,)),
            TradingAgreement=dict(columns=("InvestorID", "TradingAgreementType", "EffectDay", "ExpireDay"),
                                  sql="""SELECT DISTINCT t.InvestorID,'0' AS TradingAgreementType,
                                                '20170101' AS EffectDay,'20500101' AS ExpireDay
                                            FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1,
                                                siminfo.t_BrokerSystemSettlementGroup t2
                                            WHERE t.InvestorID = t1.InvestorID
                                            AND t1.SettlementGroupID = t2.SettlementGroupID
                                            AND t2.BrokerSystemID = %s""",
                                  params=(self.brokerSystemID,)),
            User=dict(columns=("UserID", "UserName", "UserType", "DepartmentID", "UserPassword", "LoginLimit",
                               "PasswordFailLimit", "Status", "Contacter", "Fax", "Telephone", "Email", "Address",
                               "ZipCode", "OpenDate", "CloseDate"),
                      sql="""SELECT DISTINCT t.InvestorID AS UserID,t.InvestorName AS UserName,'2' AS UserType,
                                    '0001' AS DepartmentID,t. PASSWORD AS UserPassword,'3' AS LoginLimit,
                                    '3' AS PasswordFailLimit,'1' AS STATUS,'' AS Contacter,'' AS Fax,'' AS Telephone,
                                    '' AS Email,'' AS Address,'' AS ZipCode,'' AS OpenDate,'' AS CloseDate
                                FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1,
                                     siminfo.t_BrokerSystemSettlementGroup t2
                                WHERE t.InvestorID = t1.InvestorID
                                AND t1.SettlementGroupID = t2.SettlementGroupID
                                AND t2.BrokerSystemID = %s
                            UNION ALL
                            SELECT 'broker' AS UserID,'操作员broker' AS UserName,'1' AS UserType,
                                    '0000' AS DepartmentID,'123456' AS UserPassword,'3' AS LoginLimit,
                                    '3' AS PasswordFailLimit,'1' AS STATUS,'' AS Contacter,'' AS Fax,'' AS Telephone,
                                    '' AS Email,'' AS Address,'' AS ZipCode,'' AS OpenDate,'' AS CloseDate
                            UNION ALL
                            SELECT 'broker1' AS UserID,'操作员broker1' AS UserName,'1' AS UserType,
                                    '0000' AS DepartmentID,'123456' AS UserPassword,'3' AS LoginLimit,
                                    '3' AS PasswordFailLimit,'1' AS STATUS,'' AS Contacter,'' AS Fax,'' AS Telephone,
                                    '' AS Email,'' AS Address,'' AS ZipCode,'' AS OpenDate,'' AS CloseDate
                            UNION ALL
                            SELECT 'admin' AS UserID,'管理员admin' AS UserName,'1' AS UserType,
                                    '0000' AS DepartmentID,'123456' AS UserPassword,'3' AS LoginLimit,
                                    '3' AS PasswordFailLimit,'1' AS STATUS,'' AS Contacter,'' AS Fax,'' AS Telephone,
                                    '' AS Email,'' AS Address,'' AS ZipCode,'' AS OpenDate,'' AS CloseDate
                            UNION ALL
                            SELECT 'admin1' AS UserID,'管理员admin1' AS UserName,'1' AS UserType,
                                    '0000' AS DepartmentID,'123456' AS UserPassword,'3' AS LoginLimit,
                                    '3' AS PasswordFailLimit,'1' AS STATUS,'' AS Contacter,'' AS Fax,'' AS Telephone,
                                    '' AS Email,'' AS Address,'' AS ZipCode,'' AS OpenDate,'' AS CloseDate""",
                      params=(self.brokerSystemID,)),
        )
        # 查询siminfo数据库数据内容
        csv_data = mysqlDB.select(table_sqls[csv_name]["sql"], table_sqls[csv_name].get("params"))
        # 生成csv文件
        self.__produce_csv(csv_name, table_sqls[csv_name], csv_data)

    # 生成csv文件
    def __produce_csv(self, csv_name, columns, csv_data):
        self.logger.info("%s%s%s" % ("开始生成 ", csv_name, ".csv"))
        _path = self.csv_path + os.path.sep + csv_name + '.csv'
        # 如果不存在目录则先创建
        if not os.path.exists(str(self.csv_path)):
            os.makedirs(str(self.csv_path))
        with open(_path, 'wb') as csvfile:
            if "quoting" in columns and columns['quoting']:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            else:
                writer = csv.writer(csvfile)
            writer.writerow(csv_tool.covert_to_gbk(columns['columns']))
            writer.writerows(csv_tool.covert_to_gbk(csv_data))
        self.logger.info("%s%s%s" % ("生成 ", csv_name, ".csv 文件完成"))


if __name__ == '__main__':
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql", "log", "csv"])
    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)
    # 启动脚本
    broker_stock_csv(context=context, configs=conf)
