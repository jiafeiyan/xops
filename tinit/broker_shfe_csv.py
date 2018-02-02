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

class broker_shfe_csv:
    def __init__(self, context, configs):
        # 初始化settlementGroupID
        self.settlementGroupID = configs.get("settlementGroupID")
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="future_to_csv", configs=log_conf)
        if log_conf is None:
            self.logger.warning("broker_shfe_csv未配置Log日志")
        # 初始化数据库连接
        self.mysqlDB = mysql(configs=context.get("mysql")[configs.get("mysqlId")])
        # 初始化生成柜台CSV文件路径
        output = path.convert(context.get("csv")[configs.get("csv")]['broker'])
        self.csv_path = os.path.join(output, str(configs.get("csvRoute")), str(configs.get("settlementGroupID")))
        self.__to_csv()

    def __to_csv(self):
        mysqlDB = self.mysqlDB
        self.__data_to_csv("ShfeInstrument", mysqlDB)
        self.__data_to_csv("InvestorTradingUser", mysqlDB)
        self.__data_to_csv("MaxMarginProductGroup", mysqlDB)
        self.__data_to_csv("PartBroker", mysqlDB)
        self.__data_to_csv("Trader", mysqlDB)
        self.__data_to_csv("TraderTopic", mysqlDB)
        self.__data_to_csv("TradingCodeMap", mysqlDB)
        self.__data_to_csv("TradingUser", mysqlDB)

    def __data_to_csv(self, csv_name, mysqlDB):
        table_sqls = dict(
            ShfeInstrument=dict(columns=("InstrumentID", "ExchangeID", "InstrumentName", "ExchangeInstID", "ProductID",
                                         "ProductClass", "DeliveryYear", "DeliveryMonth", "MaxMarketOrderVolume",
                                         "MinMarketOrderVolume", "MaxLimitOrderVolume", "MinLimitOrderVolume",
                                         "VolumeMultiple", "PriceTick", "CreateDate", "OpenDate", "ExpireDate",
                                         "StartDelivDate", "EndDelivDate", "InstLifePhase", "IsTrading", "PositionMode",
                                         "PositionDateMode", "LongMarginRatio", "ShortMarginRatio",
                                         "MaxMarginSideAlgorithm", "UnderlyingInstrID", "StrikePrice", "OptionsType",
                                         "UnderlyingMultiple", "CombinationType"),
                                sql="""SELECT t.InstrumentID,t2.ExchangeID,t.InstrumentName,
                                            t.InstrumentID as ExchangeInstID,t.ProductID,t.ProductClass,t.DeliveryYear,
                                            t.DeliveryMonth,t1.MaxMarketOrderVolume,t1.MinMarketOrderVolume,
                                            t1.MaxLimitOrderVolume,t1.MinLimitOrderVolume,t.VolumeMultiple,t1.PriceTick,
                                            t1.CreateDate,t1.OpenDate,t1.ExpireDate,t1.StartDelivDate,t1.EndDelivDate,
                                            t1.InstLifePhase,'1' as IsTrading,'1' as PositionMode,
                                            '1' as PositionDateMode,t3.LongMarginRatio,t3.ShortMarginRatio,
                                            '' as MaxMarginSideAlgorithm,t.UnderlyingInstrID,t.StrikePrice,
                                            t.OptionsType,t.UnderlyingMultiple,'' as CombinationType
                                        FROM t_Instrument t,t_InstrumentProperty t1,t_SettlementGroup t2,
                                            t_MarginRateDetail t3
                                        WHERE t.SettlementGroupID = t1.SettlementGroupID
                                        AND t.SettlementGroupID = t2.SettlementGroupID
                                        AND t.SettlementGroupID = t3.SettlementGroupID
                                        AND t.InstrumentID = t3.InstrumentID
                                        AND t.InstrumentID = t1.InstrumentID
                                        AND t.SettlementGroupID = %s""",
                                params=(self.settlementGroupID,)),
            InvestorTradingUser=dict(columns=("BrokerID", "InvestorID", "InvestUnitID", "UserID"),
                                     sql="""SELECT '0001' AS BrokerID,t.InvestorID AS InvestorID,
                                                    t.InvestorID AS InvestUnitID,t.InvestorID AS UserID
                                                FROM siminfo.t_InvestorClient t
                                                WHERE t.SettlementGroupID = %s""",
                                     params=(self.settlementGroupID,)),
            MaxMarginProductGroup=dict(columns=("ExchangeID", "ProductID", "MaxMarginProductGroupId"),
                                       sql="""SELECT t1.ExchangeID AS ExchangeID,t.ProductID AS ProductID,
                                                      t.ProductGroupID AS MaxMarginProductGroupId
                                                FROM siminfo.t_Product t,siminfo.t_SettlementGroup t1
                                                WHERE t.SettlementGroupID = t1.SettlementGroupID
                                                and t.SettlementGroupID = %s""",
                                       params=(self.settlementGroupID,)),
            PartBroker=dict(columns=("BrokerID", "ExchangeID", "ParticipantID", "IsActive"),
                            sql="""SELECT '0001' AS BrokerID,t2.ExchangeID AS ExchangeID,
                                          t1.ParticipantID AS ParticipantID,'1' AS IsActive
                                    FROM siminfo.t_Participant t1,siminfo.t_SettlementGroup t2
                                    WHERE t1.SettlementGroupID = t2.SettlementGroupID
                                    AND t1.SettlementGroupID = %s""",
                            params=(self.settlementGroupID,)),
            Trader=dict(columns=("BrokerID", "ExchangeID", "ParticipantID", "TraderID", "TraderClass",
                                 "TraderProperty", "Password", "OrderLocalID"),
                        sql="""SELECT '0001' AS BrokerID,t2.ExchangeID AS ExchangeID,
                                            t1.ParticipantID AS ParticipantID,'000101' AS TraderID,'1' AS TraderClass,
                                            '1' AS TraderProperty,'111111' AS PASSWORD,'' AS OrderLocalID
                                        FROM siminfo.t_Participant t1,siminfo.t_SettlementGroup t2
                                        WHERE t1.SettlementGroupID = t2.SettlementGroupID
                                        AND t1.SettlementGroupID = %s""",
                        params=(self.settlementGroupID,)),
            TraderTopic=dict(columns=("BrokerID", "ParticipantID", "ExchangeID", "TraderID", "TraderClass",
                                      "TopicID", "SequenceNo"),
                             sql="""SELECT '0001' AS BrokerID,t.ParticipantID AS ParticipantID,
                                    t2.ExchangeID AS ExchangeID,'000101' AS TraderID,'1' AS TraderClass,
                                    t.TopicID AS TopicID,'0' AS SequenceNo
                                    FROM siminfo.t_PartTopicSubscribe t,siminfo.t_Participant t1,
                                         siminfo.t_SettlementGroup t2
                                    WHERE t.ParticipantID = t1.ParticipantID
                                    AND t.SettlementGroupID = t1.SettlementGroupID
                                    AND t.SettlementGroupID = t2.SettlementGroupID
                                    AND t.SettlementGroupID = %s""",
                             params=(self.settlementGroupID,)),
            TradingCodeMap=dict(columns=("BrokerID", "InvestorID", "InvestUnitID", "ExchangeID", "CLIENTID",
                                         "ClientIDMode", "IsActive"),
                                sql="""SELECT '0001' AS BrokerID,t.InvestorID AS InvestorID,
                                            t.InvestorID AS InvestUnitID,t1.ExchangeID AS ExchangeID,
                                            t.InvestorID AS CLIENTID,'1' AS ClientIDMode,'1' AS IsActive
                                        FROM siminfo.t_InvestorClient t,siminfo.t_SettlementGroup t1
                                        WHERE t.SettlementGroupID = t1.SettlementGroupID AND t.SettlementGroupID=%s""",
                                params=(self.settlementGroupID,)),
            TradingUser=dict(columns=("BrokerID", "UserID", "Password", "DRIdentityID", "UserType"),
                             sql="""SELECT '0001' AS BrokerID,t.InvestorID AS UserID,t.`Password` AS PASSWORD,
                                          '1' AS DRIdentityID,'0' AS UserType
                                    FROM t_Investor t,t_InvestorClient t1
                                    WHERE t.InvestorID = t1.InvestorID AND t1.SettlementGroupID = %s""",
                             params=(self.settlementGroupID,)),
        )
        # 查询siminfo数据库数据内容
        csv_data = mysqlDB.select(table_sqls[csv_name]["sql"], table_sqls[csv_name].get("params"))
        # 生成csv文件
        self.__produce_csv(csv_name, table_sqls[csv_name], csv_data)

    # 生成csv文件
    def __produce_csv(self, csv_name, columns, csv_data):
        self.logger.info("%s%s%s" % ("开始生成 ", csv_name, ".csv"))
        _path = "%s%s%s%s" % (str(self.csv_path), os.path.sep, csv_name, '.csv')
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
    base_dir, config_names, config_files = parse_conf_args(__file__, config_names=["mysql", "log", "csv"])
    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)
    # 启动脚本
    broker_shfe_csv(context=context, configs=conf)
