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
        self.__t_Account(mysqlDB)
        self.__t_BusinessConfig(mysqlDB)
        self.__t_ClearingTradingPart(mysqlDB)
        self.__t_ClientProductRight(mysqlDB)
        self.__t_Exchange(mysqlDB)
        self.__t_Instrument(mysqlDB)
        self.__t_Market(mysqlDB)
        self.__t_MarketData(mysqlDB)
        self.__t_MarketProduct(mysqlDB)
        self.__t_MarketProductGroup(mysqlDB)
        self.__t_PartProductRight(mysqlDB)
        self.__t_PartProductRole(mysqlDB)
        self.__t_Participant(mysqlDB)
        self.__t_SettlementGroup(mysqlDB)
        self.__t_TradeSystemBrokerSystem(mysqlDB)
        self.__t_TradingAccount(mysqlDB)

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
                      t.SettlementGroupID,t.ProductID,t.ProductGroupID,t.UnderlyingInstrID,
                      t.ProductClass,t.PositionType,t.StrikePrice,t.OptionsType,t.VolumeMultiple,
                      t.UnderlyingMultiple,t.InstrumentID,t.InstrumentName,
                      t.DeliveryYear,t.DeliveryMonth,t.AdvanceMonth,%s
                      FROM siminfo.""" + table_name + """ t 
                      WHERE NOT EXISTS ( SELECT 1 FROM sync.""" + table_name + """ t1 
                      WHERE t.SettlementGroupID = t1.SettlementGroupID
                      AND t.InstrumentID = t1.InstrumentID)"""
        mysqlDB.execute(sql, (self.tradeSystemID, 1))

    def __t_Market(self, mysqlDB):
        table_name = "t_Market"
        sql = """INSERT INTO sync.""" + table_name + """ SELECT %s, 
                              t.SettlementGroupID, t.MarketID, t.MarketName
                              FROM siminfo.""" + table_name + """ t 
                              WHERE NOT EXISTS ( SELECT 1 FROM sync.""" + table_name + """ t1 
                              WHERE t.SettlementGroupID = t1.SettlementGroupID 
                              AND t.MarketID = t1.MarketID)"""
        mysqlDB.execute(sql, (self.tradeSystemID,))

    def __t_MarketData(self, mysqlDB):
        table_name = "t_MarketData"
        sql = """INSERT INTO sync.""" + table_name + """ SELECT %s, 
                              t.SettlementGroupID,t.LastPrice,t.PreSettlementPrice,t.PreClosePrice,t.PreOpenInterest,
                              t.OpenPrice,t.HighestPrice,t.LowestPrice,t.Volume,t.Turnover,t.OpenInterest,t.ClosePrice,
                              t.SettlementPrice,t.UpperLimitPrice,t.LowerLimitPrice,t.PreDelta,t.CurrDelta,
                              t.UpdateTime,t.UpdateMillisec,t.InstrumentID
                              FROM siminfo.""" + table_name + """ t 
                              WHERE NOT EXISTS ( SELECT 1 FROM sync.""" + table_name + """ t1 
                              WHERE t.SettlementGroupID = t1.SettlementGroupID 
                              AND t.InstrumentID = t1.InstrumentID)"""
        mysqlDB.execute(sql, (self.tradeSystemID,))

    def __t_MarketProduct(self, mysqlDB):
        table_name = "t_MarketProduct"
        sql = """INSERT INTO sync.""" + table_name + """ SELECT %s, 
                              t.SettlementGroupID,t.MarketID,t.ProductID
                              FROM siminfo.""" + table_name + """ t 
                              WHERE NOT EXISTS ( SELECT 1 FROM sync.""" + table_name + """ t1 
                              WHERE t.SettlementGroupID = t1.SettlementGroupID 
                              AND t.MarketID = t1.MarketID
                              AND t.ProductID = t1.ProductID)"""
        mysqlDB.execute(sql, (self.tradeSystemID,))

    def __t_MarketProductGroup(self, mysqlDB):
        table_name = "t_MarketProductGroup"
        sql = """INSERT INTO sync.""" + table_name + """ SELECT %s, 
                              t.SettlementGroupID,t.MarketID,t.ProductGroupID
                              FROM siminfo.""" + table_name + """ t 
                              WHERE NOT EXISTS ( SELECT 1 FROM sync.""" + table_name + """ t1 
                              WHERE t.SettlementGroupID = t1.SettlementGroupID 
                              AND t.MarketID = t1.MarketID
                              AND t.ProductGroupID = t1.ProductGroupID)"""
        mysqlDB.execute(sql, (self.tradeSystemID,))

    def __t_PartProductRight(self, mysqlDB):
        table_name = "t_PartProductRight"
        sql = """INSERT INTO sync.""" + table_name + """ SELECT %s, 
                              t.SettlementGroupID,t.ProductID,t.ParticipantID,t.TradingRight
                              FROM siminfo.""" + table_name + """ t 
                              WHERE NOT EXISTS ( SELECT 1 FROM sync.""" + table_name + """ t1 
                              WHERE t.SettlementGroupID = t1.SettlementGroupID 
                              AND t.ProductID = t1.ProductID
                              AND t.ParticipantID = t1.ParticipantID)"""
        mysqlDB.execute(sql, (self.tradeSystemID,))

    def __t_PartProductRole(self, mysqlDB):
            table_name = "t_PartProductRole"
            sql = """INSERT INTO sync.""" + table_name + """ SELECT %s, 
                                  t.SettlementGroupID,t.ParticipantID,t.ProductID,t.TradingRole
                                  FROM siminfo.""" + table_name + """ t 
                                  WHERE NOT EXISTS ( SELECT 1 FROM sync.""" + table_name + """ t1 
                                  WHERE t.SettlementGroupID = t1.SettlementGroupID 
                                  AND t.ParticipantID = t1.ParticipantID
                                  AND t.ProductID = t1.ProductID
                                  AND t.TradingRole = t1.TradingRole)"""
            mysqlDB.execute(sql, (self.tradeSystemID,))

    def __t_Participant(self, mysqlDB):
            table_name = "t_Participant"
            sql = """INSERT INTO sync.""" + table_name + """ SELECT %s, 
                                  t.SettlementGroupID,t.ParticipantID,t.ParticipantName,t.ParticipantAbbr,
                                  t.MemberType,t.IsActive
                                  FROM siminfo.""" + table_name + """ t 
                                  WHERE NOT EXISTS ( SELECT 1 FROM sync.""" + table_name + """ t1 
                                  WHERE t.SettlementGroupID = t1.SettlementGroupID 
                                  AND t.ParticipantID = t1.ParticipantID)"""
            mysqlDB.execute(sql, (self.tradeSystemID,))

    def __t_SettlementGroup(self, mysqlDB):
                table_name = "t_SettlementGroup"
                sql = """INSERT INTO sync.""" + table_name + """ SELECT %s, 
                                      t.SettlementGroupID,t.SettlementGroupName,t.ExchangeID,
                                      t.SettlementGroupType,t.Currency
                                      FROM siminfo.""" + table_name + """ t 
                                      WHERE NOT EXISTS ( SELECT 1 FROM sync.""" + table_name + """ t1 
                                      WHERE t.SettlementGroupID = t1.SettlementGroupID)"""
                mysqlDB.execute(sql, (self.tradeSystemID,))

    def __t_TradeSystemBrokerSystem(self, mysqlDB):
                table_name = "t_TradeSystemBrokerSystem"
                sql = """INSERT INTO sync.""" + table_name + """ SELECT t.TradeSystemID,t.BrokerSystemID
                                      FROM siminfo.""" + table_name + """ t 
                                      WHERE NOT EXISTS ( SELECT 1 FROM sync.""" + table_name + """ t1 
                                      WHERE t.TradeSystemID = t1.TradeSystemID
                                      AND t.BrokerSystemID = t1.BrokerSystemID)"""
                mysqlDB.execute(sql)

    def __t_TradingAccount(self, mysqlDB):
                table_name = "t_TradingAccount"
                sql = """INSERT INTO sync.""" + table_name + """ SELECT %s, 
                                      SettlementGroupID,PreBalance,CurrMargin,CloseProfit,Premium,Deposit,Withdraw,
                                      Balance,Available,AccountID,FrozenMargin,FrozenPremium
                                      FROM siminfo.""" + table_name + """ t 
                                      WHERE NOT EXISTS ( SELECT 1 FROM sync.""" + table_name + """ t1 
                                      WHERE t.SettlementGroupID = t1.SettlementGroupID
                                      AND t.AccountID = t1.AccountID)"""
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