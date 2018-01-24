# -*- coding: UTF-8 -*-

"""
生成CSV文件
t_Account
t_BaseReserveAccount
t_BusinessConfig
t_ClearingTradingPart
t_ClientProductRight
t_InstrumentProperty
"""

import csv
import os

from utils import log
from utils import parse_conf_args
from utils import Configuration
from utils import mysql


class future_to_csv:
    def __init__(self, context, configs):
        tradeSystemID = configs.get("tradeSystemID")
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="future_to_csv", configs=log_conf)
        if log_conf is None:
            self.logger.warning(__file__ + "未配置Log日志")
        # 初始化数据库连接
        self.mysqlDB = mysql(configs=context.get("mysql")[configs.get("mysqlId")])
        # 初始化tradeSystemID
        self.tradeSystemID = tradeSystemID
        # 初始化生成CSV文件路径
        self.csv_path = context.get("csv")[configs.get("csv")]['path']
        self.__to_csv()

    def __to_csv(self):
        mysqlDB = self.mysqlDB
        self.__data_to_csv("t_Account", mysqlDB)
        # siminfo.time and SettlementID = 1
        self.__data_to_csv("t_BaseReserveAccount", mysqlDB)
        self.__data_to_csv("t_BusinessConfig", mysqlDB)
        self.__data_to_csv("t_ClearingTradingPart", mysqlDB)
        self.__data_to_csv("t_ClientProductRight", mysqlDB)
        # IsFirstTradingDay = 1
        self.__data_to_csv("t_CurrInstrumentProperty", mysqlDB)
        self.__data_to_csv("t_CurrMarginRate", mysqlDB)
        self.__data_to_csv("t_CurrMarginRateDetail", mysqlDB)
        self.__data_to_csv("t_CurrTradingSegmentAttr", mysqlDB)
        self.__data_to_csv("t_Instrument", mysqlDB)
        self.__data_to_csv("t_Market", mysqlDB)
        self.__data_to_csv("t_MarketProduct", mysqlDB)
        self.__data_to_csv("t_MarketProductGroup", mysqlDB)
        self.__data_to_csv("t_Participant", mysqlDB)
        self.__data_to_csv("t_PartProductRight", mysqlDB)
        self.__data_to_csv("t_PartProductRole", mysqlDB)
        # siminfo.time and SettlementID = 1
        self.__data_to_csv("t_PartRoleAccount", mysqlDB)
        self.__data_to_csv("t_SettlementGroup", mysqlDB)
        # siminfo.time and SettlementID = 1
        self.__data_to_csv("t_TradingAccount", mysqlDB)

    def __data_to_csv(self, table_name, mysqlDB):
        table_sqls = dict(
            t_Account=dict(columns=("SettlementGroupID", "AccountID", "ParticipantID", "Currency"),
                           sql="""SELECT SettlementGroupID,AccountID,ParticipantID,Currency 
                                  FROM sync.t_Account WHERE TradeSystemID=%s""",
                           quoting=True),
            t_BaseReserveAccount=dict(
                columns=("TradingDay", "SettlementGroupID", "SettlementID", "ParticipantID", "AccountID", "Reserve"),
                sql="""SELECT t1.TradingDay,t.SettlementGroupID,'1' AS SettlementID,ParticipantID,AccountID,Reserve
                        FROM sync.t_BaseReserveAccount t,siminfo.t_TradeSystemTradingDay t1,
                             siminfo.t_TradeSystemSettlementGroup t2
                        WHERE t.SettlementGroupID = t2.SettlementGroupID
                        AND t1.TradeSystemID = t2.TradeSystemID 
                        AND t.TradeSystemID=%s""",
                quoting=True),
            t_BusinessConfig=dict(columns=("SettlementGroupID", "FunctionCode", "OperationType", "Description"),
                                  sql="""SELECT SettlementGroupID,FunctionCode,OperationType,Description
                                         FROM sync.t_BusinessConfig WHERE TradeSystemID=%s""",
                                  quoting=True),
            t_ClearingTradingPart=dict(columns=("ClearingPartID", "ParticipantID"),
                                       sql="""SELECT ClearingPartID,ParticipantID
                                              FROM sync.t_ClearingTradingPart WHERE TradeSystemID=%s""",
                                       quoting=True),
            t_ClientProductRight=dict(columns=("SettlementGroupID", "ProductID", "ClientID", "TradingRight"),
                                      sql="""SELECT SettlementGroupID,ProductID,ClientID,TradingRight
                                             FROM sync.t_ClientProductRight WHERE TradeSystemID=%s""",
                                      quoting=True),
            t_CurrInstrumentProperty=dict(columns=("SettlementGroupID", "CreateDate", "OpenDate", "ExpireDate",
                                                   "StartDelivDate", "EndDelivDate", "BasisPrice",
                                                   "MaxMarketOrderVolume",
                                                   "MinMarketOrderVolume", "MaxLimitOrderVolume", "MinLimitOrderVolume",
                                                   "PriceTick", "AllowDelivPersonOpen", "InstrumentID",
                                                   "InstLifePhase", "IsFirstTradingDay"),
                                          sql="""SELECT SettlementGroupID,CreateDate,OpenDate,ExpireDate,StartDelivDate,
                                              EndDelivDate,BasisPrice,MaxMarketOrderVolume,MinMarketOrderVolume,
                                              MaxLimitOrderVolume,MinLimitOrderVolume,PriceTick,AllowDelivPersonOpen,
                                              InstrumentID,InstLifePhase,'1' AS IsFirstTradingDay
                                             FROM sync.t_CurrInstrumentProperty WHERE TradeSystemID = %s """),
            t_CurrMarginRate=dict(columns=("SettlementGroupID", "MarginCalcID", "InstrumentID", "ParticipantID"),
                                  sql="""SELECT SettlementGroupID,MarginCalcID,InstrumentID,ParticipantID
                                         FROM sync.t_CurrMarginRate WHERE TradeSystemID=%s"""),
            t_CurrMarginRateDetail=dict(columns=("SettlementGroupID", "TradingRole", "HedgeFlag", "ValueMode",
                                                 "LongMarginRatio", "ShortMarginRatio", "InstrumentID",
                                                 "ParticipantID", "ClientID"),
                                        sql="""SELECT SettlementGroupID,TradingRole,HedgeFlag,ValueMode,LongMarginRatio,
                                                  ShortMarginRatio,InstrumentID,ParticipantID,ClientID
                                                FROM sync.t_CurrMarginRateDetail WHERE TradeSystemID=%s"""),
            t_CurrTradingSegmentAttr=dict(columns=("SettlementGroupID", "TradingSegmentSN", "TradingSegmentName",
                                                   "StartTime", "InstrumentStatus", "InstrumentID"),
                                          sql="""SELECT SettlementGroupID,TradingSegmentSN,TradingSegmentName,
                                                        StartTime,InstrumentStatus,InstrumentID
                                                FROM sync.t_CurrTradingSegmentAttr WHERE TradeSystemID=%s
                                                ORDER BY InstrumentID,TradingSegmentSN"""),
            t_Instrument=dict(columns=("SettlementGroupID", "ProductID", "ProductGroupID", "UnderlyingInstrID",
                                       "ProductClass", "PositionType", "StrikePrice", "OptionsType", "VolumeMultiple",
                                       "UnderlyingMultiple", "InstrumentID", "InstrumentName", "DeliveryYear",
                                       "DeliveryMonth", "AdvanceMonth", "IsTrading"),
                              sql="""SELECT SettlementGroupID,ProductID,ProductGroupID,UnderlyingInstrID,ProductClass,
                                            PositionType,StrikePrice,OptionsType,VolumeMultiple,UnderlyingMultiple,
                                            InstrumentID,InstrumentName,DeliveryYear,DeliveryMonth,
                                            AdvanceMonth,IsTrading
                                      FROM sync.t_Instrument WHERE TradeSystemID=%s"""),
            t_Market=dict(columns=("MarketID", "MarketName"),
                          sql="""SELECT MarketID,MarketName FROM sync.t_Market WHERE TradeSystemID=%s""",
                          quoting=True),
            t_MarketProduct=dict(columns=("MarketID", "ProductID"),
                                 sql="""SELECT MarketID,ProductID FROM sync.t_MarketProduct WHERE TradeSystemID=%s""",
                                 quoting=True),
            t_MarketProductGroup=dict(columns=("MarketID", "ProductGroupID"),
                                      sql="""SELECT MarketID,ProductGroupID FROM sync.t_MarketProductGroup WHERE TradeSystemID=%s""",
                                      quoting=True),
            t_Participant=dict(
                columns=("ParticipantID", "ParticipantName", "ParticipantAbbr", "MemberType", "IsActive"),
                sql="""SELECT ParticipantID,ParticipantName,ParticipantAbbr,MemberType,IsActive
                                      FROM sync.t_Participant WHERE TradeSystemID=%s""",
                quoting=True),
            t_PartProductRight=dict(columns=("SettlementGroupID", "ProductID", "ParticipantID", "TradingRight"),
                                    sql="""SELECT SettlementGroupID,ProductID,ParticipantID,TradingRight
                                              FROM sync.t_PartProductRight WHERE TradeSystemID=%s""",
                                    quoting=True),
            t_PartProductRole=dict(columns=("SettlementGroupID", "ParticipantID", "ProductID", "TradingRole"),
                                   sql="""SELECT SettlementGroupID,ParticipantID,ProductID,TradingRole
                                              FROM sync.t_PartProductRole WHERE TradeSystemID=%s""",
                                   quoting=True),
            t_PartRoleAccount=dict(columns=("TradingDay", "SettlementGroupID", "SettlementID",
                                            "ParticipantID", "TradingRole", "AccountID"),
                                   sql="""SELECT t1.TradingDay,t.SettlementGroupID,'1' AS SettlementID,
                                                  ParticipantID,TradingRole,AccountID
                                          FROM sync.t_PartRoleAccount t,siminfo.t_TradeSystemTradingDay t1,
                                               siminfo.t_TradeSystemSettlementGroup t2
                                          WHERE t.SettlementGroupID = t2.SettlementGroupID
                                          AND t1.TradeSystemID = t2.TradeSystemID 
                                          AND t.TradeSystemID=%s""",
                                   quoting=True),
            t_SettlementGroup=dict(columns=("SettlementGroupID", "SettlementGroupName", "ExchangeID", "Currency"),
                                   sql="""SELECT SettlementGroupID,SettlementGroupName,ExchangeID,Currency
                                          FROM sync.t_SettlementGroup WHERE TradeSystemID=%s""",
                                   quoting=True),
            t_TradingAccount=dict(columns=("TradingDay", "SettlementGroupID", "SettlementID", "PreBalance",
                                           "CurrMargin", "CloseProfit", "Premium", "Deposit", "Withdraw", "Balance",
                                           "Available", "AccountID", "FrozenMargin", "FrozenPremium"),
                                  sql="""SELECT t1.TradingDay,t.SettlementGroupID,'1' AS SettlementID,
                                                PreBalance,CurrMargin,CloseProfit,Premium,Deposit,Withdraw,
                                                Balance,Available,AccountID,FrozenMargin,FrozenPremium
                                                FROM sync.t_TradingAccount t,siminfo.t_TradeSystemTradingDay t1,
                                                     siminfo.t_TradeSystemSettlementGroup t2
                                                WHERE t.SettlementGroupID = t2.SettlementGroupID
                                                AND t1.TradeSystemID = t2.TradeSystemID 
                                                AND t.TradeSystemID=%s""",
                                  quoting=True),

        )
        # 查询sync数据库数据内容
        csv_data = mysqlDB.select(table_sqls[table_name]["sql"], (self.tradeSystemID,))
        # 生成csv文件
        self.__produce_csv(table_name, table_sqls[table_name], csv_data)

    # 生成csv文件
    def __produce_csv(self, table_name, columns, csv_data):
        self.logger.info("%s%s%s" % ("开始生成 ", table_name, ".csv"))
        path = "%s%s%s%s" % (str(self.csv_path), os.path.sep, table_name, '.csv')
        if not os.path.exists(str(self.csv_path)):
            os.makedirs(str(self.csv_path))
        with open(path, 'wb') as csvfile:
            if "quoting" in columns and columns['quoting']:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            else:
                writer = csv.writer(csvfile)
            writer.writerow(columns['columns'])
            writer.writerows(csv_data)
        self.logger.info("%s%s%s" % ("生成 ", table_name, ".csv 文件完成"))


if __name__ == '__main__':
    base_dir, config_names, config_files = parse_conf_args(__file__, config_names=["mysql", "log", "csv"])
    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)
    # 启动脚本
    future_to_csv(context=context, configs=conf)
