# -*- coding: UTF-8 -*-

"""
将siminfo数据同步到sync
t_Account                     t_Account
t_BaseReserveAccount          t_BaseReserveAccount
t_BrokerSystem
t_BrokerSystemSettlementGroup
t_BusinessConfig              t_BusinessConfig
t_ClearingTradingPart         t_ClearingTradingPart
t_ClientProductRight          t_ClientProductRight
t_Exchange                    t_Exchange
t_Instrument                  t_Instrument
t_InstrumentProperty          t_CurrInstrumentProperty
t_MarginRate                  t_CurrMarginRate
t_MarginRateDetail            t_CurrMarginRateDetail
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
t_TradingSegmentAttr          t_CurrTradingSegmentAttr
"""

from utils import log
from utils import parse_conf_args
from utils import Configuration
from utils import mysql


class toSyncAll:
    def __init__(self, context, configs):
        tradeSystemID = configs.get("tradeSystemID")
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="toSyncAll", configs=log_conf)
        if log_conf is None:
            self.logger.warning("toSyncAll未配置Log日志")
        # 初始化数据库连接
        self.mysqlDB = mysql(configs=context.get("mysql")[configs.get("mysqlId")])
        # 初始化tradeSystemID
        self.tradeSystemID = tradeSystemID
        self.__convert_sync()

    def __convert_sync(self):
        mysqlDB = self.mysqlDB

        # 同步数据(存在数据先删除)
        self.__t_Account(mysqlDB)
        self.__t_BaseReserveAccount(mysqlDB)
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
        self.__t_PartRoleAccount(mysqlDB)
        self.__t_Participant(mysqlDB)
        self.__t_SettlementGroup(mysqlDB)
        self.__t_TradeSystemBrokerSystem(mysqlDB)
        self.__t_TradingAccount(mysqlDB)

        self.__t_CurrInstrumentProperty(mysqlDB)
        self.__t_CurrMarginRate(mysqlDB)
        self.__t_CurrMarginRateDetail(mysqlDB)
        self.__t_CurrTradingSegmentAttr(mysqlDB)

    def __t_Account(self, mysqlDB):
        table_name = "t_Account"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t2.TradeSystemID,
                          t.SettlementGroupID, t.AccountID, t.ParticipantID, t.Currency
                          FROM siminfo.""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                          WHERE t.SettlementGroupID = t2.SettlementGroupID
                          AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_BaseReserveAccount(self, mysqlDB):
        table_name = "t_BaseReserveAccount"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t2.TradeSystemID,
                           t.SettlementGroupID, t.ParticipantID, t.AccountID, t.Reserve
                           FROM siminfo.""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                           WHERE t.SettlementGroupID = t2.SettlementGroupID 
                           AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_BusinessConfig(self, mysqlDB):
        table_name = "t_BusinessConfig"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t2.TradeSystemID,
                        t.SettlementGroupID, t.FunctionCode, t.OperationType, t.Description
                        FROM siminfo.""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                        WHERE t.SettlementGroupID = t2.SettlementGroupID 
                        AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_ClearingTradingPart(self, mysqlDB):
        table_name = "t_ClearingTradingPart"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t2.TradeSystemID,
                        t.ClearingPartID, t.ParticipantID
                        FROM siminfo.""" + table_name + """ t,siminfo.t_Participant t3,siminfo.t_TradeSystemSettlementGroup t2
                        WHERE t.ParticipantID = t3.ParticipantID AND t3.SettlementGroupID = t2.SettlementGroupID 
                        AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_ClientProductRight(self, mysqlDB):
        table_name = "t_ClientProductRight"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t2.TradeSystemID, 
                       t.SettlementGroupID, t.ProductID, t.ClientID, t.TradingRight
                       FROM siminfo.""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                       WHERE t.SettlementGroupID = t2.SettlementGroupID 
                       AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_Exchange(self, mysqlDB):
        table_name = "t_Exchange"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t2.TradeSystemID, 
                          t.ExchangeID, t.ExchangeName 
                          FROM siminfo.""" + table_name + """ t, siminfo.t_SettlementGroup t3,siminfo.t_TradeSystemSettlementGroup t2
                          WHERE t.ExchangeID = t3.ExchangeID AND t3.SettlementGroupID = t2.SettlementGroupID
                          AND t2.TradeSystemID=%s
                          GROUP BY t2.TradeSystemID,t.ExchangeID,t.ExchangeName"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_Instrument(self, mysqlDB):
        table_name = "t_Instrument"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t2.TradeSystemID,
                      t.SettlementGroupID,t.ProductID,t.ProductGroupID,t.UnderlyingInstrID,
                      t.ProductClass,t.PositionType,t.StrikePrice,t.OptionsType,t.VolumeMultiple,
                      t.UnderlyingMultiple,t.InstrumentID,t.InstrumentName,
                      t.DeliveryYear,t.DeliveryMonth,t.AdvanceMonth,%s
                      FROM siminfo.""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                      WHERE t.SettlementGroupID = t2.SettlementGroupID 
                      AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(1, self.tradeSystemID))]
        mysqlDB.executetransaction(trans)

    def __t_Market(self, mysqlDB):
        table_name = "t_Market"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t2.TradeSystemID, 
                              t.SettlementGroupID, t.MarketID, t.MarketName
                              FROM siminfo.""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                              WHERE t.SettlementGroupID = t2.SettlementGroupID 
                              AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_MarketData(self, mysqlDB):
        table_name = "t_MarketData"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t2.TradeSystemID, 
                              t.SettlementGroupID,t.LastPrice,t.PreSettlementPrice,t.PreClosePrice,t.PreOpenInterest,
                              t.OpenPrice,t.HighestPrice,t.LowestPrice,t.Volume,t.Turnover,t.OpenInterest,t.ClosePrice,
                              t.SettlementPrice,t.UpperLimitPrice,t.LowerLimitPrice,t.PreDelta,t.CurrDelta,
                              t.UpdateTime,t.UpdateMillisec,t.InstrumentID
                              FROM siminfo.""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                              WHERE t.SettlementGroupID = t2.SettlementGroupID 
                              AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_MarketProduct(self, mysqlDB):
        table_name = "t_MarketProduct"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t2.TradeSystemID,
                              t.SettlementGroupID,t.MarketID,t.ProductID
                              FROM siminfo.""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                              WHERE t.SettlementGroupID = t2.SettlementGroupID
                              AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_MarketProductGroup(self, mysqlDB):
        table_name = "t_MarketProductGroup"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t2.TradeSystemID,
                              t.SettlementGroupID,t.MarketID,t.ProductGroupID
                              FROM siminfo.""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                              WHERE t.SettlementGroupID = t2.SettlementGroupID 
                              AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_PartProductRight(self, mysqlDB):
        table_name = "t_PartProductRight"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t2.TradeSystemID,
                              t.SettlementGroupID,t.ProductID,t.ParticipantID,t.TradingRight
                              FROM siminfo.""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                              WHERE t.SettlementGroupID = t2.SettlementGroupID 
                              AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_PartProductRole(self, mysqlDB):
        table_name = "t_PartProductRole"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t2.TradeSystemID,
                              t.SettlementGroupID,t.ParticipantID,t.ProductID,t.TradingRole
                              FROM siminfo.""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                              WHERE t.SettlementGroupID = t2.SettlementGroupID 
                              AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_PartRoleAccount(self, mysqlDB):
        table_name = "t_PartRoleAccount"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t2.TradeSystemID,
                              t.SettlementGroupID,t.ParticipantID,t.TradingRole,t.AccountID
                              FROM siminfo.""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                              WHERE t.SettlementGroupID = t2.SettlementGroupID 
                              AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_Participant(self, mysqlDB):
        table_name = "t_Participant"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t2.TradeSystemID,
                              t.SettlementGroupID,t.ParticipantID,t.ParticipantName,t.ParticipantAbbr,
                              t.MemberType,t.IsActive
                              FROM siminfo.""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                              WHERE t.SettlementGroupID = t2.SettlementGroupID 
                              AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_SettlementGroup(self, mysqlDB):
        table_name = "t_SettlementGroup"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t2.TradeSystemID,
                              t.SettlementGroupID,t.SettlementGroupName,t.ExchangeID,
                              t.SettlementGroupType,t.Currency
                              FROM siminfo.""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                              WHERE t.SettlementGroupID = t2.SettlementGroupID
                              AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_TradeSystemBrokerSystem(self, mysqlDB):
        table_name = "t_TradeSystemBrokerSystem"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t.TradeSystemID,t.BrokerSystemID
                              FROM siminfo.""" + table_name + """ t
                              WHERE  t.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_TradingAccount(self, mysqlDB):
        table_name = "t_TradingAccount"
        self.logger.info("删除" + table_name + "下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync." + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步" + table_name + " ==>> sync")
        sql = """INSERT INTO sync.""" + table_name + """ SELECT t2.TradeSystemID,
                              t.SettlementGroupID,PreBalance,CurrMargin,CloseProfit,Premium,Deposit,Withdraw,
                              Balance,Available,AccountID,FrozenMargin,FrozenPremium
                              FROM siminfo.""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                              WHERE t.SettlementGroupID = t2.SettlementGroupID 
                              AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_CurrInstrumentProperty(self, mysqlDB):
        table_name = "InstrumentProperty"
        self.logger.info("删除sync.t_CurrInstrumentProperty下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync.t_Curr" + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步siminfo.t_InstrumentProperty ==>> sync.t_CurrInstrumentProperty")
        sql = """INSERT INTO sync.t_Curr""" + table_name + """ SELECT t2.TradeSystemID,
                              t.SettlementGroupID,CreateDate,OpenDate,ExpireDate,StartDelivDate,EndDelivDate,
                                BasisPrice,MaxMarketOrderVolume,MinMarketOrderVolume,MaxLimitOrderVolume,
                                MinLimitOrderVolume,PriceTick,AllowDelivPersonOpen,InstrumentID,InstLifePhase,%s
                              FROM siminfo.t_""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                              WHERE t.SettlementGroupID = t2.SettlementGroupID 
                              AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(1, self.tradeSystemID))]
        mysqlDB.executetransaction(trans)

    def __t_CurrMarginRate(self, mysqlDB):
        table_name = "MarginRate"
        self.logger.info("删除sync.t_CurrMarginRate下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync.t_Curr" + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步siminfo.t_MarginRate ==>> sync.t_CurrMarginRate")
        sql = """INSERT INTO sync.t_Curr""" + table_name + """ SELECT t2.TradeSystemID,
                              t.SettlementGroupID,MarginCalcID,InstrumentID,ParticipantID
                              FROM siminfo.t_""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                              WHERE t.SettlementGroupID = t2.SettlementGroupID 
                              AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_CurrMarginRateDetail(self, mysqlDB):
        table_name = "MarginRateDetail"
        self.logger.info("删除sync.t_CurrMarginRateDetail下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync.t_Curr" + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步siminfo.t_MarginRateDetail ==>> sync.t_CurrMarginRateDetail")
        sql = """INSERT INTO sync.t_Curr""" + table_name + """ SELECT t2.TradeSystemID,
                             t.SettlementGroupID,TradingRole,HedgeFlag,ValueMode,LongMarginRatio,
                             ShortMarginRatio,InstrumentID,ParticipantID,ClientID
                             FROM siminfo.t_""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                             WHERE t.SettlementGroupID = t2.SettlementGroupID 
                             AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)

    def __t_CurrTradingSegmentAttr(self, mysqlDB):
        table_name = "TradingSegmentAttr"
        self.logger.info("删除sync.t_CurrTradingSegmentAttr下TradeSystemID为" + str(self.tradeSystemID) + "的数据")
        delete = "DELETE FROM sync.t_Curr" + table_name + " WHERE TradeSystemID=%s"
        self.logger.info("同步siminfo.t_TradingSegmentAttr ==>> sync.t_CurrTradingSegmentAttr")
        sql = """INSERT INTO sync.t_Curr""" + table_name + """ SELECT t2.TradeSystemID, 
                             t.SettlementGroupID,TradingSegmentSN,TradingSegmentName,
                             StartTime,InstrumentStatus,InstrumentID
                             FROM siminfo.t_""" + table_name + """ t, siminfo.t_TradeSystemSettlementGroup t2
                             WHERE t.SettlementGroupID = t2.SettlementGroupID
                             AND t2.TradeSystemID=%s"""
        trans = [dict(sql=delete, params=(self.tradeSystemID,)),
                 dict(sql=sql, params=(self.tradeSystemID,))]
        mysqlDB.executetransaction(trans)


if __name__ == '__main__':
    base_dir, config_names, config_files = parse_conf_args(__file__, config_names=["mysql","log"])
    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)
    # 初始化脚本数据
    toSyncAll(context=context, configs=conf)
