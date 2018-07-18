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


class broker_sse_csv:
    def __init__(self, context, configs):
        # 初始化settlementGroupID
        self.settlementGroupID = configs.get("settlementGroupID")
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="broker_sse_csv", configs=log_conf)
        if log_conf is None:
            self.logger.warning("broker_sse_csv未配置Log日志")
        # 初始化数据库连接
        self.mysqlDB = mysql(configs=context.get("mysql")[configs.get("mysqlId")])
        # 初始化生成柜台CSV文件路径
        output = path.convert(context.get("csv")[configs.get("csv")]['broker'])
        self.csv_path = os.path.join(output, str(configs.get("csvRoute")), str(configs.get("settlementGroupID")))
        self.__to_csv()

    def __to_csv(self):
        mysqlDB = self.mysqlDB
        self.__data_to_csv("SSEMarketData", mysqlDB)
        # SecurityStatus=0，TotalEquity=''，CirculationEquity=''
        self.__data_to_csv("SSESecurity", mysqlDB)
        self.__data_to_csv("SSEBusinessUnitAccount", mysqlDB)
        self.__data_to_csv("SSEPosition", mysqlDB)
        self.__data_to_csv("SSEShareholderAccount", mysqlDB)
        self.__data_to_csv("SSEInvestorTradingFee", mysqlDB)

    def __data_to_csv(self, csv_name, mysqlDB):
        table_sqls = dict(
            SSEMarketData=dict(columns=["TradingDay", "SecurityID", "ExchangeID", "SecurityName", "PreClosePrice",
                                        "OpenPrice", "Volume", "Turnover", "TradingCount", "LastPrice", "HighestPrice",
                                        "LowestPrice", "BidPrice1", "AskPrice1", "UpperLimitPrice", "LowerLimitPrice",
                                        "PERatio1", "PERatio2", "PriceUpDown1", "PriceUpDown2", "OpenInterest",
                                        "BidVolume1", "AskVolume1", "BidPrice2", "BidVolume2", "AskPrice2",
                                        "AskVolume2", "BidPrice3", "BidVolume3", "AskPrice3", "AskVolume3",
                                        "BidPrice4", "BidVolume4", "AskPrice4", "AskVolume4", "BidPrice5", "BidVolume5",
                                        "AskPrice5", "AskVolume5", "UpdateTime", "UpdateMillisec", "ClosePrice",
                                        "MDSecurityStat"],
                               sql="""SELECT t.TradingDay AS TradingDay,t.InstrumentID AS SecurityID,
                                                '1' AS ExchangeID,t2.InstrumentName AS SecurityName,
                                                t.PreSettlementPrice AS PreClosePrice,t.OpenPrice AS OpenPrice,
                                                '0' AS Volume,'0' AS Turnover,'0' AS TradingCount,
                                                t.LastPrice AS LastPrice,t.HighestPrice AS HighestPrice,
                                                t.LowestPrice AS LowestPrice,'0' AS BidPrice1,'0' AS AskPrice1,
                                                t.UpperLimitPrice AS UpperLimitPrice,t.LowerLimitPrice AS LowerLimitPrice,
                                                '0' AS PERatio1,'0' AS PERatio2,'0' AS PriceUpDown1,'0' AS PriceUpDown2,
                                                t.OpenInterest AS OpenInterest,'0' AS BidVolume1,'0' AS AskVolume1,
                                                '0' AS BidPrice2,'0' AS BidVolume2,'0' AS AskPrice2,'0' AS AskVolume2,
                                                '0' AS BidPrice3,'0' AS BidVolume3,'0' AS AskPrice3,'0' AS AskVolume3,
                                                '0' AS BidPrice4,'0' AS BidVolume4,'0' AS AskPrice4,'0' AS AskVolume4,
                                                '0' AS BidPrice5,'0' AS BidVolume5,'0' AS AskPrice5,'0' AS AskVolume5,
                                                '00:00:00' AS UpdateTime,'0' AS UpdateMillisec,
                                                '0' as ClosePrice, '0' as MDSecurityStat
                                            FROM siminfo.t_MarketData t,siminfo.t_Instrument t2
                                            WHERE t.SettlementGroupID = t2.SettlementGroupID
                                            AND t.InstrumentID = t2.InstrumentID
                                            AND t.SettlementGroupID = %s""",
                               params=(self.settlementGroupID,)),
            SSESecurity=dict(columns=("SecurityID", "ExchangeID", "SecurityName", "UnderlyingSecurityID", "MarketID",
                                      "ProductID", "SecurityType", "CurrencyID", "OrderUnit", "BuyTradingUnit",
                                      "SellTradingUnit", "MaxMarketOrderBuyVolume", "MinMarketOrderBuyVolume",
                                      "MaxLimitOrderBuyVolume", "MinLimitOrderBuyVolume", "MaxMarketOrderSellVolume",
                                      "MinMarketOrderSellVolume", "MaxLimitOrderSellVolume", "MinLimitOrderSellVolume",
                                      "VolumeMultiple", "PriceTick", "OpenDate", "CloseDate", "PositionType",
                                      "ParValue", "SecurityStatus", "BondInterest", "ConversionRate", "TotalEquity",
                                      "CirculationEquity", "IsSupportPur", "IsSupportRed", "IsSupportTrade",
                                      "IsCancelOrder", "IsCollateral", "QualificationClass"),
                             sql="""SELECT t.InstrumentID AS SecurityID,'1' AS ExchangeID,
                                           t.InstrumentName AS SecurityName,t.InstrumentID AS UnderlyingSecurityID,
                                           '1' AS MarketID,'1' AS ProductID,'a' AS SecurityType,
                                     t1.Currency AS CurrencyID,'1' AS OrderUnit,'100' AS BuyTradingUnit,
                                     '1' AS SellTradingUnit,'1000000' AS MaxMarketOrderBuyVolume,
                                     '1' AS MinMarketOrderBuyVolume,'1000000' AS MaxLimitOrderBuyVolume,
                                     '1' AS MinLimitOrderBuyVolume,'1000000' AS MaxMarketOrderSellVolume,
                                     '1' AS MinMarketOrderSellVolume,'1000000' AS MaxLimitOrderSellVolume,
                                     '1' AS MinLimitOrderSellVolume,'1' AS VolumeMultiple,t4.PriceTick AS PriceTick,
                                     t4.OpenDate AS OpenDate,'' AS CloseDate,'1' AS PositionType,'1' AS ParValue,
                                     '0' AS SecurityStatus,'0' AS BondInterest,'0' AS ConversionRate,
                                     t.TotalEquity AS TotalEquity,t.CirculationEquity AS CirculationEquity,
                                     '0' AS IsSupportPur,'0' AS IsSupportRed,'1' AS IsSupportTrade,
                                     '1' AS IsCancelOrder,'1' AS IsCollateral,'' AS QualificationClass
                                    FROM siminfo.t_Instrument t,siminfo.t_SettlementGroup t1,siminfo.t_InstrumentProperty t4
                                    WHERE t.SettlementGroupID = t1.SettlementGroupID
                                    AND t.InstrumentID = t4.InstrumentID
                                    AND t.SettlementGroupID = t4.SettlementGroupID
                                    AND t.SettlementGroupID = %s""",
                             params=(self.settlementGroupID,)),
            SSEBusinessUnitAccount=dict(columns=("InvestorID", "BusinessUnitID", "ExchangeID", "MarketID",
                                                 "ShareholderID", "TradingCodeClass", "ProductID", "AccountID",
                                                 "CurrencyID", "UserID"),
                                        sql="""SELECT t.InvestorID AS InvestorID,t.InvestorID AS BusinessUnitID,
                                                    '1' AS ExchangeID,'1' AS MarketID,t.ClientID AS ShareholderID,
                                                    'a' AS TradingCodeClass,'0' AS ProductID,t.InvestorID AS AccountID,
                                                    'CNY' AS CurrencyID,t.InvestorID AS UserID
                                                FROM siminfo.t_InvestorClient t WHERE t.SettlementGroupID = %s
                                                UNION ALL 
                                                SELECT t.InvestorID AS InvestorID,t.InvestorID AS BusinessUnitID,
                                                    '1' AS ExchangeID,'1' AS MarketID,t.ClientID AS ShareholderID,
                                                    'a' AS TradingCodeClass,'0' AS ProductID,t.InvestorID AS AccountID,
                                                    'CNY' AS CurrencyID,'broker' AS UserID
                                                FROM siminfo.t_InvestorClient t WHERE t.SettlementGroupID = %s
                                                UNION ALL 
                                                SELECT t.InvestorID AS InvestorID,t.InvestorID AS BusinessUnitID,
                                                    '1' AS ExchangeID,'1' AS MarketID,t.ClientID AS ShareholderID,
                                                    'a' AS TradingCodeClass,'0' AS ProductID,t.InvestorID AS AccountID,
                                                    'CNY' AS CurrencyID,'broker1' AS UserID
                                                FROM siminfo.t_InvestorClient t WHERE t.SettlementGroupID = %s
                                                UNION ALL 
                                                SELECT t.InvestorID AS InvestorID,t.InvestorID AS BusinessUnitID,
                                                    '1' AS ExchangeID,'1' AS MarketID,t.ClientID AS ShareholderID,
                                                    'a' AS TradingCodeClass,'0' AS ProductID,t.InvestorID AS AccountID,
                                                    'CNY' AS CurrencyID,'admin' AS UserID
                                                FROM siminfo.t_InvestorClient t WHERE t.SettlementGroupID = %s
                                                UNION ALL 
                                                SELECT t.InvestorID AS InvestorID,t.InvestorID AS BusinessUnitID,
                                                    '1' AS ExchangeID,'1' AS MarketID,t.ClientID AS ShareholderID,
                                                    'a' AS TradingCodeClass,'0' AS ProductID,t.InvestorID AS AccountID,
                                                    'CNY' AS CurrencyID,'admin1' AS UserID
                                                FROM siminfo.t_InvestorClient t WHERE t.SettlementGroupID = %s""",
                                        params=(self.settlementGroupID, self.settlementGroupID, self.settlementGroupID,
                                                self.settlementGroupID, self.settlementGroupID)),
            SSEPosition=dict(columns=("InvestorID", "BusinessUnitID", "MarketID", "ShareholderID", "TradingDay",
                                      "ExchangeID", "SecurityID", "HistoryPos", "HistoryPosFrozen", "TodayBSPos",
                                      "TodayBSPosFrozen", "TodayPRPos", "TodayPRPosFrozen", "TodaySMPos",
                                      "TodaySMPosFrozen", "HistoryPosCost", "TotalPosCost", "MarginBuyPos",
                                      "ShortSellPos", "TodayShortSellPos", "PrePosition", "AvailablePosition",
                                      "CurrentPosition"),
                             sql="""SELECT t1.InvestorID AS InvestorID,t1.InvestorID AS BusinessUnitID,
                                            '1' AS MarketID,t.ClientID AS ShareholderID,'' AS TradingDay,
                                            '1' AS ExchangeID,t.InstrumentID AS SecurityID,t.YdPosition AS HistoryPos,
                                            '0' AS HistoryPosFrozen,'0' AS TodayBSPos,'0' AS TodayBSPosFrozen,
                                            '0' AS TodayPRPos,'0' AS TodayPRPosFrozen,'0' AS TodaySMPos,
                                            '0' AS TodaySMPosFrozen,t.YdPositionCost AS HistoryPosCost,
                                            t.YdPositionCost AS TotalPosCost,'0' AS MarginBuyPos,'0' AS ShortSellPos,
                                            '0' AS TodayShortSellPos,t.YdPosition AS PrePosition,
                                            t.YdPosition AS AvailablePosition,t.YdPosition AS CurrentPosition
                                        FROM siminfo.t_ClientPosition t,siminfo.t_InvestorClient t1
                                        WHERE t.ClientID = t1.ClientID
                                        AND t.SettlementGroupID = t1.SettlementGroupID
                                        AND t.SettlementGroupID = %s""",
                             params=(self.settlementGroupID,)),
            SSEShareholderAccount=dict(columns=("ExchangeID", "ShareholderID", "MarketID", "TradingCodeClass",
                                                "InvestorID", "TradingCodeEx", "PbuID", "BranchID",
                                                "bProperControl", "TradingRightTemplateID"),
                                       sql="""SELECT '1' AS ExchangeID,t.ClientID AS ShareholderID,'1' AS MarketID,
                                                        'a' AS TradingCodeClass,t.InvestorID AS InvestorID,
                                                        '' AS TradingCodeEx,'28637' AS PbuID,'04005' AS BranchID,
                                                        '0' AS bProperControl,'default' AS TradingRightTemplateID
                                                FROM siminfo.t_InvestorClient t
                                                WHERE t.SettlementGroupID = %s""",
                                       params=(self.settlementGroupID,)),
            SSEInvestorTradingFee=dict(columns=("InvestorID", "ExchangeID", "ProductID", "SecurityType", "SecurityID",
                                                "BizClass", "BrokerageType", "RatioByAmt", "RatioByPar", "FeePerOrder",
                                                "FeeMin", "FeeMax", "FeeByVolume", "DepartmentID", "RangeMode"),
                                       sql="""SELECT '00000000' AS InvestorID,'1' AS ExchangeID,'0' AS ProductID,
                                                '0' AS SecurityType,'00000000' AS SecurityID,'0' AS BizClass,
                                                '0' AS BrokerageType,t.OpenFeeRatio AS RatioByAmt,'0' AS RatioByPar,
                                                '0' AS FeePerOrder,t.MinOpenFee AS FeeMin,t.MaxOpenFee AS FeeMax,
                                                '0' AS FeeByVolume,'00000000' AS DepartmentID, '0' as RangeMode
                                            FROM siminfo.t_TransFeeRateDetail t
                                            WHERE t.SettlementGroupID = %s
                                            UNION ALL 
                                            SELECT '00000000' AS InvestorID,'1' AS ExchangeID,'0' AS ProductID,
                                                '0' AS SecurityType,'00000000' AS SecurityID,'1' AS BizClass,
                                                '0' AS BrokerageType,t.OpenFeeRatio AS RatioByAmt,'0' AS RatioByPar,
                                                '0' AS FeePerOrder,t.MinOpenFee AS FeeMin,t.MaxOpenFee AS FeeMax,
                                                '0' AS FeeByVolume,'00000000' AS DepartmentID,'0' as RangeMode
                                            FROM siminfo.t_TransFeeRateDetail t
                                            WHERE t.SettlementGroupID = %s""",
                                       params=(self.settlementGroupID, self.settlementGroupID,)),
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
    broker_sse_csv(context=context, configs=conf)
