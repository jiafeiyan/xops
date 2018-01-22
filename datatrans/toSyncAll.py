# -*- coding: UTF-8 -*-

from utils import log
from utils import parse_args
from utils import load
from utils import mysql

"""
将siminfo数据同步到sync
t_Account                     t_Account
t_BrokerSystem
t_BrokerSystemSettlementGroup
t_BusinessConfig              t_BusinessConfig
t_ClearingTradingPart         t_ClearingTradingPart
t_ClientProductRight          t_ClientProductRight
t_Exchange                    t_Exchange
t_Instrument                  t_Instrument
t_InstrumentProperty
t_MarginRate
t_MarginRateDetail
t_Market                      t_Market
t_MarketData                  t_MarketData
t_MarketProduct               t_MarketProduct
t_MarketProductGroup          t_MarketProductGroup
t_PartProductRight            t_PartProductRight
t_PartProductRole             t_PartProductRole
t_Participant                 t_Participant
t_Product
t_ProductGroup
t_SecurityProfit
t_SettlementGroup             t_SettlementGroup
t_TradeSystem
t_TradeSystemBrokerSystem     t_TradeSystemBrokerSystem
t_TradeSystemSettlementGroup
t_TradingAccount              t_TradingAccount
t_TradingSegmentAttr
"""

class toSyncAll:
    def __init__(self, tradeSystem, configs):
        self.logger = log.get_logger(category="toSyncAll", configs=configs)
        self.configs = configs
        self.tradeSystemID = tradeSystem
        self.__convert_sync()

    def __convert_sync(self):
        mysqlDB = self.configs['db_instance']

        # 同步数据
        # self.__t_Account(mysqlDB)
        # self.__t_BusinessConfig(mysqlDB)
        # self.__t_ClearingTradingPart(mysqlDB)
        # self.__t_ClientProductRight(mysqlDB)
        # self.__t_Exchange(mysqlDB)
        self.__t_Instrument(mysqlDB)

    def __t_Account(self, mysqlDB):
        table_name = "t_Account"
        sql = """INSERT INTO sync.""" + table_name + """ SELECT %s, 
                          t.SettlementGroupID, t.AccountID, t.ParticipantID, t.Currency
                          FROM siminfo.""" + table_name + """ t 
                          WHERE NOT EXISTS ( SELECT 1 FROM sync.""" + table_name + """ t1 
                          WHERE t.SettlementGroupID = t1.SettlementGroupID 
                          AND t.AccountID = t1.AccountID)"""
        mysqlDB.execute(sql, (self.tradeSystemID,))

    def __t_BusinessConfig(self, mysqlDB):
        table_name = "t_BusinessConfig"
        sql = """INSERT INTO sync.""" + table_name + """ SELECT %s, 
                        t.SettlementGroupID, t.FunctionCode, t.OperationType, t.Description
                        FROM siminfo.""" + table_name + """ t 
                        WHERE NOT EXISTS ( SELECT 1 FROM sync.""" + table_name + """ t1 
                        WHERE t.SettlementGroupID = t1.SettlementGroupID 
                        AND t.FunctionCode = t1.FunctionCode)"""
        mysqlDB.execute(sql, (self.tradeSystemID,))

    def __t_ClearingTradingPart(self, mysqlDB):
        table_name = "t_ClearingTradingPart"
        sql = """INSERT INTO sync.""" + table_name + """ SELECT %s, 
                        t.ClearingPartID, t.ParticipantID
                        FROM siminfo.""" + table_name + """ t 
                        WHERE NOT EXISTS ( SELECT 1 FROM sync.""" + table_name + """ t1 
                        WHERE t.ClearingPartID = t1.ClearingPartID 
                        AND t.ParticipantID = t1.ParticipantID)"""
        mysqlDB.execute(sql, (self.tradeSystemID,))

    def __t_ClientProductRight(self, mysqlDB):
        table_name = "t_ClientProductRight"
        sql = """INSERT INTO sync.""" + table_name + """ SELECT %s, 
                       t.SettlementGroupID, t.ProductID, t.ClientID, t.TradingRight
                       FROM siminfo.""" + table_name + """ t 
                       WHERE NOT EXISTS ( SELECT 1 FROM sync.""" + table_name + """ t1 
                       WHERE t.SettlementGroupID = t1.SettlementGroupID 
                       AND t.ProductID = t1.ProductID
                       AND t.ClientID = t1.ClientID
                       AND t.TradingRight = t1.TradingRight)"""
        mysqlDB.execute(sql, (self.tradeSystemID,))

    def __t_Exchange(self, mysqlDB):
        table_name = "t_Exchange"
        sql = """INSERT INTO sync.""" + table_name + """ SELECT %s, 
                          t.ExchangeID, t.ExchangeName 
                          FROM siminfo.""" + table_name + """ t 
                          WHERE NOT EXISTS ( SELECT 1 FROM sync.""" + table_name + """ t1 
                          WHERE t.ExchangeID = t1.ExchangeID)"""
        mysqlDB.execute(sql, (self.tradeSystemID,))

    def __t_Instrument(self, mysqlDB):
        table_name = "t_Instrument"
        sql = """INSERT INTO sync.""" + table_name + """ SELECT %s, 
                      t.ExchangeID, t.ExchangeName 
                      FROM siminfo.""" + table_name + """ t 
                      WHERE NOT EXISTS ( SELECT 1 FROM sync.""" + table_name + """ t1 
                      WHERE t.ExchangeID = t1.ExchangeID)"""
        mysqlDB.execute(sql, (self.tradeSystemID,))


if __name__ == '__main__':
    args = parse_args('-tradeSystemID')

    if not args.tradeSystemID:
        print "缺少参数 -tradeSystemID"
        exit()

    # 交易系统代码
    tradeSystemID = args.tradeSystemID
    # 读取参数文件
    conf = load(args.conf)
    # 建立mysql数据库连接
    mysql_instance = mysql(configs=conf)
    conf["db_instance"] = mysql_instance

    # 初始化脚本数据
    toSyncAll(tradeSystemID, conf)
