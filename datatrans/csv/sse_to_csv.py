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


class sse_to_csv:
    def __init__(self, context, configs):
        # 初始化settlementGroupID
        self.settlementGroupID = configs.get("settlementGroupID")
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="future_to_csv", configs=log_conf)
        if log_conf is None:
            self.logger.warning("sse_to_csv未配置Log日志")
        # 初始化数据库连接
        self.mysqlDB = mysql(configs=context.get("mysql")[configs.get("mysqlId")])
        # 初始化生成柜台CSV文件路径
        self.csv_path = context.get("csv")[configs.get("csv")]['counter'] + os.path.sep + "stock_sse"
        self.__to_csv()

    def __to_csv(self):
        mysqlDB = self.mysqlDB
        self.__data_to_csv("BusinessUnit", mysqlDB)
        self.__data_to_csv("BUProxy", mysqlDB)
        self.__data_to_csv("ExchangeTradingDay", mysqlDB)
        self.__data_to_csv("Investor", mysqlDB)
        self.__data_to_csv("SSEMarketData", mysqlDB)
        self.__data_to_csv("SSEBusinessUnitAccount", mysqlDB)
        self.__data_to_csv("SSEPosition", mysqlDB)
        self.__data_to_csv("SSEShareholderAccount", mysqlDB)
        self.__data_to_csv("TradingAccount", mysqlDB)
        self.__data_to_csv("TradingAgreement", mysqlDB)
        self.__data_to_csv("User", mysqlDB)

    def __data_to_csv(self, csv_name, mysqlDB):
        table_sqls = dict(
            BUProxy=dict(columns=("UserID", "InvestorID", "BusinessUnitID"),
                         sql="""SELECT InvestorID AS UserID,InvestorID AS InvestorID,InvestorID AS BusinessUnitID
                                        FROM siminfo.t_Investor"""),
            BusinessUnit=dict(columns=("InvestorID", "BusinessUnitID", "BusinessUnitName"),
                              sql="""SELECT InvestorID,InvestorID AS BusinessUnitID,'Bu1' AS BusinessUnitName
                                        FROM siminfo.t_Investor"""),
            ExchangeTradingDay=dict(columns=("ExchangeID", "TradingDay"),
                                    sql="""SELECT t1.ExchangeID, t.TradingDay
                                           FROM siminfo.t_TradeSystemTradingDay t, siminfo.t_SettlementGroup t1,
                                                t_TradeSystemSettlementGroup t2
                                           WHERE t.TradeSystemID = t2.TradeSystemID
                                           AND t2.SettlementGroupID = t1.SettlementGroupID
                                           AND t1.SettlementGroupID=%s""",
                                    params=(self.settlementGroupID,)),
            Investor=dict(columns=("InvestorID", "DepartmentID", "InvestorType", "InvestorName", "IdCardType",
                                   "IdCardNo", "ContractNo", "BirthDate", "Gender", "Professional", "Country",
                                   "TaxNo", "LicenseNo", "RegisteredCapital", "RegisteredCurrency", "Mobile",
                                   "RiskLevel", "Remark", "OpenDate", "CloseDate", "Status", "Contacter", "Fax",
                                   "Telephone", "Email", "Address", "ZipCode", "InnerBranchID", "Operways"),
                          sql="""SELECT InvestorID,'0001' AS DepartmentID,'0' AS InvestorType,InvestorName,
                                '1' AS IdCardType,OpenID AS IdCardNo,'' AS ContractNo,'' AS BirthDate,'' AS Gender,
                                '' AS Professional,'' AS Country,'' AS TaxNo,'' AS LicenseNo,'0' AS RegisteredCapital,
                                '' AS RegisteredCurrency,'' AS Mobile,'' AS RiskLevel,'' AS Remark,'' AS OpenDate,
                                '' AS CloseDate,'1' AS STATUS,'' AS Contacter,'' AS Fax,'' AS Telephone,'' AS Email,
                                '' AS Address,'' AS ZipCode,'' AS InnerBranchID,'' AS Operways
                                FROM siminfo.t_Investor"""),
            SSEMarketData=dict(columns=("TradingDay", "SecurityID", "ExchangeID", "SecurityName", "PreClosePrice",
                                        "OpenPrice", "Volume", "Turnover", "TradingCount", "LastPrice", "HighestPrice",
                                        "LowestPrice", "BidPrice1", "AskPrice1", "UpperLimitPrice", "LowerLimitPrice",
                                        "PERatio1", "PERatio2", "PriceUpDown1", "PriceUpDown2", "OpenInterest",
                                        "BidVolume1", "AskVolume1", "BidPrice2", "BidVolume2", "AskPrice2",
                                        "AskVolume2", "BidPrice3", "BidVolume3", "AskPrice3", "AskVolume3",
                                        "BidPrice4", "BidVolume4", "AskPrice4", "AskVolume4", "BidPrice5", "BidVolume5",
                                        "AskPrice5", "AskVolume5", "UpdateTime", "UpdateMillisec"),
                               sql="""SELECT t.TradingDay AS TradingDay,t.InstrumentID AS SecurityID,
                                                t1.ExchangeID AS ExchangeID,t2.InstrumentName AS SecurityName,
                                                t.PreClosePrice AS PreClosePrice,t.OpenPrice AS OpenPrice,
                                                t.Volume AS Volume,t.Turnover AS Turnover,"0" AS TradingCount,
                                                t.LastPrice AS LastPrice,t.HighestPrice AS HighestPrice,
                                                t.LowestPrice AS LowestPrice,'0' AS BidPrice1,'0' AS AskPrice1,
                                                t.UpperLimitPrice AS UpperLimitPrice,t.LowerLimitPrice AS LowerLimitPrice,
                                                '0' AS PERatio1,'0' AS PERatio2,'0' AS PriceUpDown1,'0' AS PriceUpDown2,
                                                t.OpenInterest AS OpenInterest,'0' AS BidVolume1,'0' AS AskVolume1,
                                                '0' AS BidPrice2,'0' AS BidVolume2,'0' AS AskPrice2,'0' AS AskVolume2,
                                                '0' AS BidPrice3,'0' AS BidVolume3,'0' AS AskPrice3,'0' AS AskVolume3,
                                                '0' AS BidPrice4,'0' AS BidVolume4,'0' AS AskPrice4,'0' AS AskVolume4,
                                                '0' AS BidPrice5,'0' AS BidVolume5,'0' AS AskPrice5,'0' AS AskVolume5,
                                                t.UpdateTime AS UpdateTime,t.UpdateMillisec AS UpdateMillisec
                                            FROM siminfo.t_MarketData t,siminfo.t_SettlementGroup t1,
                                                  siminfo.t_Instrument t2
                                            WHERE t.SettlementGroupID = t1.SettlementGroupID
                                            AND t.SettlementGroupID = t2.SettlementGroupID
                                            AND t.InstrumentID = t2.InstrumentID
                                            AND t.SettlementGroupID = %s""",
                               params=(self.settlementGroupID,)),
            SSEBusinessUnitAccount=dict(columns=("InvestorID", "BusinessUnitID", "ExchangeID", "MarketID",
                                                 "ShareholderID", "TradingCodeClass", "ProductID", "AccountID",
                                                 "CurrencyID", "UserID"),
                                        sql="""SELECT t.InvestorID AS InvestorID,t.InvestorID AS BusinessUnitID,
                                                    t1.ExchangeID AS ExchangeID,t2.MarketID AS MarketID,
                                                    t.ClientID AS ShareholderID,'a' AS TradingCodeClass,
                                                    '0' AS ProductID,t.InvestorID AS AccountID,
                                                    'CNY' AS CurrencyID,t3.UserID
                                                FROM siminfo.t_InvestorClient t,siminfo.t_SettlementGroup t1,
                                                    siminfo.t_Market t2,siminfo.t_User t3
                                                WHERE t.SettlementGroupID = t1.SettlementGroupID
                                                AND t1.SettlementGroupID = t2.SettlementGroupID
                                                AND t3.SettlementGroupID = t.SettlementGroupID
                                                AND t1.SettlementGroupID = %s""",
                                        params=(self.settlementGroupID,)),
            SSEPosition=dict(columns=("InvestorID", "BusinessUnitID", "MarketID", "ShareholderID", "TradingDay",
                                      "ExchangeID", "SecurityID", "HistoryPos", "HistoryPosFrozen", "TodayBSPos",
                                      "TodayBSPosFrozen", "TodayPRPos", "TodayPRPosFrozen", "TodaySMPos",
                                      "TodaySMPosFrozen", "HistoryPosCost", "TotalPosCost", "MarginBuyPos",
                                      "ShortSellPos", "TodayShortSellPos", "PrePosition", "AvailablePosition",
                                      "CurrentPosition"),
                             sql="""SELECT t1.InvestorID AS InvestorID,t1.InvestorID AS BusinessUnitID,
                                        t2.MarketID AS MarketID,t.ClientID AS ShareholderID,'' AS TradingDay,
                                        t3.ExchangeID AS ExchangeID,t.InstrumentID AS SecurityID,'1000000' AS HistoryPos,
                                        '0' AS HistoryPosFrozen,'0' AS TodayBSPos,'0' AS TodayBSPosFrozen,
                                        '0' AS TodayPRPos,'0' AS TodayPRPosFrozen,'0' AS TodaySMPos,
                                        '0' AS TodaySMPosFrozen,'0' AS HistoryPosCost,'0' AS TotalPosCost,
                                        '0' AS MarginBuyPos,'0' AS ShortSellPos,'0' AS TodayShortSellPos,
                                        '1000000' AS PrePosition,'1000000' AS AvailablePosition,
                                        '1000000' AS CurrentPosition
                                    FROM siminfo.t_ClientPosition t,siminfo.t_InvestorClient t1,
                                         siminfo.t_Market t2,siminfo.t_SettlementGroup t3
                                    WHERE t.ClientID = t1.ClientID
                                    AND t3.SettlementGroupID = t2.SettlementGroupID
                                    AND t2.SettlementGroupID = %s""",
                             params=(self.settlementGroupID,)),
            SSEShareholderAccount=dict(columns=("ExchangeID", "ShareholderID", "MarketID", "InvestorID",
                                                "TradingCodeClass", "TradingCodeEx", "PbuID",
                                                "BranchID", "bProperControl"),
                                       sql="""SELECT t1.ExchangeID AS ExchangeID,t.ClientID AS ShareholderID,
                                                    t2.MarketID AS MarketID,t.InvestorID AS InvestorID,
                                                    'a' AS TradingCodeClass,'' AS TradingCodeEx,'232600' AS PbuID,
                                                    'D9' AS BranchID,'0' AS bProperControl
                                                FROM siminfo.t_InvestorClient t,siminfo.t_SettlementGroup t1,
                                                    siminfo.t_Market t2
                                                WHERE t.SettlementGroupID = t1.SettlementGroupID
                                                AND t.SettlementGroupID = t2.SettlementGroupID
                                                and t.SettlementGroupID = %s""",
                                       params=(self.settlementGroupID,)),
            TradingAccount=dict(columns=("AccountID", "CurrencyID", "AccountType", "PreDeposit", "UsefulMoney",
                                         "FetchLimit", "Deposit", "Withdraw", "FrozenMargin", "FrozenCash",
                                         "FrozenCommission", "CurrMargin", "Commission", "RoyaltyIn", "RoyaltyOut",
                                         "AccountOwner", "DepartmentID"),
                                sql="""SELECT InvestorID AS AccountID,'CNY' AS CurrencyID,'1' AS AccountType,
                                            Available AS PreDeposit,Available AS UsefulMoney,Available AS FetchLimit,
                                            '0' AS Deposit,'0' AS Withdraw,'0' AS FrozenMargin,'0' AS FrozenCash,
                                            '0' AS FrozenCommission,'0' AS CurrMargin,'0' AS Commission,
                                            '0' AS RoyaltyIn,'0' AS RoyaltyOut,InvestorID AS AccountOwner,
                                            '0001' AS DepartmentID 
                                            FROM siminfo.t_InvestorFund t,siminfo.t_BrokerSystemSettlementGroup t1
                                            WHERE t.BrokerSystemID = t1.BrokerSystemID
                                            AND t1.SettlementGroupID = %s""",
                                params=(self.settlementGroupID,)),
            TradingAgreement=dict(columns=("InvestorID", "TradingAgreementType", "EffectDay", "ExpireDay"),
                                  sql="""SELECT InvestorID,'0' AS TradingAgreementType,
                                          '20170101' AS EffectDay,'20500101' AS ExpireDay
                                         FROM siminfo.t_Investor"""),
            User=dict(columns=("UserID", "UserName", "UserType", "DepartmentID", "UserPassword", "LoginLimit",
                               "PasswordFailLimit", "Status", "Contacter", "Fax", "Telephone", "Email", "Address",
                               "ZipCode", "OpenDate", "CloseDate"),
                      sql="""SELECT InvestorID AS UserID,InvestorName AS UserName,'2' AS UserType,
                              '0001' AS DepartmentID,PASSWORD AS UserPassword,'3' AS LoginLimit,
                              '3' AS PasswordFailLimit,'1' AS STATUS,'' AS Contacter,'' AS Fax,'' AS Telephone,
                              '' AS Email,'' AS Address,'' AS ZipCode,'' AS OpenDate,'' AS CloseDate
                              FROM siminfo.t_Investor"""),
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
    sse_to_csv(context=context, configs=conf)
