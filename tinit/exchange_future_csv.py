# -*- coding: UTF-8 -*-

"""
生成CSV文件
t_Account.csv
t_BaseReserveAccount.csv
t_BusinessConfig.csv
t_ClearingTradingPart.csv
t_ClientProductRight.csv
t_CurrInstrumentProperty.csv
t_CurrMarginRate.csv
t_CurrMarginRateDetail.csv
t_CurrTradingSegmentAttr.csv
t_Instrument.csv
t_Market.csv
t_MarketProduct.csv
t_MarketProductGroup.csv
t_Participant.csv
t_PartProductRight.csv
t_PartProductRole.csv
t_PartRoleAccount.csv
t_SettlementGroup.csv
t_TradingAccount.csv
t_Client.csv
t_ClientPosition.csv
t_CurrPriceBanding.csv
t_InstrumentGroup.csv
t_MarketData.csv
t_MarketDataTopic.csv
t_MdPubStatus.csv
t_PartClient.csv
t_PartPosition.csv
t_PartTopicSubscribe.csv
t_User.csv
t_UserFunctionRight.csv
t_UserIP.csv
"""

import csv
import os

from utils import log
from utils import parse_conf_args
from utils import path
from utils import Configuration
from utils import mysql
from utils import csv_tool


class exchange_future_csv:
    def __init__(self, context, configs):
        tradeSystemID = configs.get("tradeSystemID")
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="exchange_future_csv", configs=log_conf)
        if log_conf is None:
            self.logger.warning("exchange_future_csv未配置Log日志")
        # 初始化数据库连接
        self.mysqlDB = mysql(configs=context.get("mysql")[configs.get("mysqlId")])
        # 初始化tradeSystemID
        self.tradeSystemID = tradeSystemID
        # 初始化生成CSV文件路径
        output = path.convert(context.get("csv")[configs.get("csv")]['exchange'])
        self.csv_path = os.path.join(output, str(configs.get("tradeSystemID")))
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
        # self.__data_to_csv("t_SettlementGroup", mysqlDB)
        # siminfo.time and SettlementID = 1
        self.__data_to_csv("t_TradingAccount", mysqlDB)
        self.__data_to_csv("t_Client", mysqlDB)
        self.__data_to_csv("t_ClientPosition", mysqlDB)
        self.__data_to_csv("t_CurrPriceBanding", mysqlDB)
        # siminfo.time and SettlementID = 1
        self.__data_to_csv("t_InstrumentGroup", mysqlDB)
        # siminfo.time and SettlementID = 1
        self.__data_to_csv("t_MarketData", mysqlDB)
        self.__data_to_csv("t_MarketDataTopic", mysqlDB)
        self.__data_to_csv("t_MdPubStatus", mysqlDB)
        self.__data_to_csv("t_PartClient", mysqlDB)
        self.__data_to_csv("t_PartPosition", mysqlDB)
        self.__data_to_csv("t_PartTopicSubscribe", mysqlDB)
        self.__data_to_csv("t_User", mysqlDB)
        self.__data_to_csv("t_UserFunctionRight", mysqlDB)
        self.__data_to_csv("t_UserIP", mysqlDB)
        # self.__data_to_csv("t_InstrumentTradingRight", mysqlDB)

        # ================shfe.txt====================
        self.__generate_marketdata("shfe", mysqlDB)
        # ================dce.txt=====================
        self.__generate_marketdata("dce", mysqlDB)
        # ================czce.txt====================
        self.__generate_marketdata("czce", mysqlDB)
        # ================cffex.txt===================
        self.__generate_marketdata("cffex", mysqlDB)
        # ================ine.txt===================
        self.__generate_marketdata("ine", mysqlDB)
        # ================sge.txt===================
        self.__generate_marketdata("sge", mysqlDB)

    def __data_to_csv(self, table_name, mysqlDB):
        table_sqls = dict(
            t_Account=dict(columns=("SettlementGroupID", "AccountID", "ParticipantID", "Currency"),
                           sql="""SELECT 'SG01' AS SettlementGroupID,AccountID,ParticipantID,Currency
                                  FROM sync.t_Account WHERE TradeSystemID=%s""",
                           quoting=True),
            t_BaseReserveAccount=dict(
                columns=("TradingDay", "SettlementGroupID", "SettlementID", "ParticipantID", "AccountID", "Reserve"),
                sql="""SELECT t1.TradingDay,'SG01' AS SettlementGroupID,'1' AS SettlementID,ParticipantID,AccountID,Reserve
                        FROM sync.t_BaseReserveAccount t,siminfo.t_TradeSystemTradingDay t1,
                             siminfo.t_TradeSystemSettlementGroup t2
                        WHERE t.SettlementGroupID = t2.SettlementGroupID
                        AND t1.TradeSystemID = t2.TradeSystemID 
                        AND t.TradeSystemID=%s""",
                quoting=True),
            t_BusinessConfig=dict(columns=("SettlementGroupID", "FunctionCode", "OperationType", "Description"),
                                  sql="""SELECT 'SG01' AS SettlementGroupID,FunctionCode,OperationType,Description
                                         FROM sync.t_BusinessConfig WHERE TradeSystemID=%s""",
                                  quoting=True),
            t_ClearingTradingPart=dict(columns=("ClearingPartID", "ParticipantID"),
                                       sql="""SELECT ClearingPartID,ParticipantID
                                              FROM sync.t_ClearingTradingPart WHERE TradeSystemID=%s""",
                                       quoting=True),
            t_ClientProductRight=dict(columns=("SettlementGroupID", "ProductID", "ClientID", "TradingRight"),
                                      sql="""SELECT 'SG01' AS SettlementGroupID,ProductID,ClientID,TradingRight
                                                         FROM sync.t_ClientProductRight WHERE TradeSystemID=%s""",
                                      quoting=True),
            t_CurrInstrumentProperty=dict(columns=("SettlementGroupID", "CreateDate", "OpenDate", "ExpireDate",
                                                   "StartDelivDate", "EndDelivDate", "BasisPrice",
                                                   "MaxMarketOrderVolume",
                                                   "MinMarketOrderVolume", "MaxLimitOrderVolume", "MinLimitOrderVolume",
                                                   "PriceTick", "AllowDelivPersonOpen", "InstrumentID",
                                                   "InstLifePhase", "IsFirstTradingDay"),
                                          sql="""SELECT 'SG01' AS SettlementGroupID,CreateDate,OpenDate,ExpireDate,StartDelivDate,
                                              EndDelivDate,BasisPrice,MaxMarketOrderVolume,MinMarketOrderVolume,
                                              MaxLimitOrderVolume,MinLimitOrderVolume,PriceTick,AllowDelivPersonOpen,
                                              InstrumentID,InstLifePhase,'1' AS IsFirstTradingDay
                                             FROM sync.t_CurrInstrumentProperty WHERE TradeSystemID = %s """),
            t_CurrMarginRate=dict(columns=("SettlementGroupID", "MarginCalcID", "InstrumentID", "ParticipantID"),
                                  sql="""SELECT 'SG01' AS SettlementGroupID,MarginCalcID,InstrumentID,ParticipantID
                                         FROM sync.t_CurrMarginRate WHERE TradeSystemID=%s"""),
            t_CurrMarginRateDetail=dict(columns=("SettlementGroupID", "TradingRole", "HedgeFlag", "ValueMode",
                                                 "LongMarginRatio", "ShortMarginRatio", "InstrumentID",
                                                 "ParticipantID", "ClientID"),
                                        sql="""SELECT 'SG01' AS SettlementGroupID,TradingRole,HedgeFlag,ValueMode,LongMarginRatio,
                                                  ShortMarginRatio,InstrumentID,ParticipantID,ClientID
                                                FROM sync.t_CurrMarginRateDetail WHERE TradeSystemID=%s"""),
            t_CurrTradingSegmentAttr=dict(columns=("SettlementGroupID", "TradingSegmentSN", "TradingSegmentName",
                                                   "StartTime", "InstrumentStatus", "DayOffset", "InstrumentID"),
                                          sql="""SELECT 'SG01' AS SettlementGroupID,TradingSegmentSN,TradingSegmentName,
                                                        StartTime,InstrumentStatus,DayOffset,InstrumentID
                                                FROM sync.t_CurrTradingSegmentAttr WHERE TradeSystemID=%s
                                                ORDER BY InstrumentID,TradingSegmentSN"""),
            t_Instrument=dict(columns=("SettlementGroupID", "ProductID", "ProductGroupID", "UnderlyingInstrID",
                                       "ProductClass", "PositionType", "StrikePrice", "OptionsType", "VolumeMultiple",
                                       "UnderlyingMultiple", "InstrumentID", "InstrumentName", "DeliveryYear",
                                       "DeliveryMonth", "AdvanceMonth", "IsTrading"),
                              sql="""SELECT 'SG01' AS SettlementGroupID,ProductID,ProductGroupID,UnderlyingInstrID,ProductClass,
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
            t_Participant=dict(columns=("ParticipantID", "ParticipantName", "ParticipantAbbr", "MemberType",
                                        "IsActive"),
                               sql="""SELECT ParticipantID,ParticipantName,ParticipantAbbr,MemberType,IsActive
                                                  FROM sync.t_Participant WHERE TradeSystemID=%s""",
                               quoting=True),
            t_PartProductRight=dict(columns=("SettlementGroupID", "ProductID", "ParticipantID", "TradingRight"),
                                    sql="""SELECT 'SG01' AS SettlementGroupID,ProductID,ParticipantID,TradingRight
                                                          FROM sync.t_PartProductRight WHERE TradeSystemID=%s""",
                                    quoting=True),
            t_PartProductRole=dict(columns=("SettlementGroupID", "ParticipantID", "ProductID", "TradingRole"),
                                   sql="""SELECT 'SG01' AS SettlementGroupID,ParticipantID,ProductID,TradingRole
                                                          FROM sync.t_PartProductRole WHERE TradeSystemID=%s""",
                                   quoting=True),
            t_PartRoleAccount=dict(columns=("TradingDay", "SettlementGroupID", "SettlementID",
                                            "ParticipantID", "TradingRole", "AccountID"),
                                   sql="""SELECT t1.TradingDay,'SG01' AS SettlementGroupID,'1' AS SettlementID,
                                                  ParticipantID,TradingRole,AccountID
                                          FROM sync.t_PartRoleAccount t,siminfo.t_TradeSystemTradingDay t1,
                                               siminfo.t_TradeSystemSettlementGroup t2
                                          WHERE t.SettlementGroupID = t2.SettlementGroupID
                                          AND t1.TradeSystemID = t2.TradeSystemID 
                                          AND t.TradeSystemID=%s""",
                                   quoting=True),
            t_SettlementGroup=dict(columns=("SettlementGroupID", "SettlementGroupName", "ExchangeID", "Currency"),
                                   sql="""SELECT 'SG01' AS SettlementGroupID,SettlementGroupName,ExchangeID,Currency
                                          FROM sync.t_SettlementGroup WHERE TradeSystemID=%s""",
                                   quoting=True),
            t_TradingAccount=dict(columns=("TradingDay", "SettlementGroupID", "SettlementID", "PreBalance",
                                           "CurrMargin", "CloseProfit", "Premium", "Deposit", "Withdraw", "Balance",
                                           "Available", "AccountID", "FrozenMargin", "FrozenPremium"),
                                  sql="""SELECT t1.TradingDay,'SG01' AS SettlementGroupID,'1' AS SettlementID,
                                                PreBalance,CurrMargin,CloseProfit,Premium,Deposit,Withdraw,
                                                Balance,Available,AccountID,FrozenMargin,FrozenPremium
                                                FROM sync.t_TradingAccount t,siminfo.t_TradeSystemTradingDay t1,
                                                     siminfo.t_TradeSystemSettlementGroup t2
                                                WHERE t.SettlementGroupID = t2.SettlementGroupID
                                                AND t1.TradeSystemID = t2.TradeSystemID 
                                                AND t.TradeSystemID=%s""",
                                  quoting=True),
            t_Client=dict(columns=("ClientID", "ClientName", "IdentifiedCardType", "IdentifiedCardNo",
                                   "TradingRole", "ClientType", "IsActive", "HedgeFlag"),
                          sql="""SELECT ClientID,ClientName,IdentifiedCardType,IdentifiedCardNo,
                                        TradingRole,ClientType,IsActive,HedgeFlag
                                  FROM sync.t_Client WHERE TradeSystemID=%s""",
                          quoting=True),
            t_ClientPosition=dict(columns=("TradingDay", "SettlementGroupID", "SettlementID", "HedgeFlag",
                                           "PosiDirection", "YdPosition", "Position", "LongFrozen", "ShortFrozen",
                                           "YdLongFrozen", "YdShortFrozen", "BuyTradeVolume", "SellTradeVolume",
                                           "PositionCost", "YdPositionCost", "UseMargin", "FrozenMargin",
                                           "LongFrozenMargin", "ShortFrozenMargin", "FrozenPremium", "InstrumentID",
                                           "ParticipantID", "ClientID"),
                                  sql="""SELECT TradingDay,'SG01' AS SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,
                                            YdPosition,Position,LongFrozen,ShortFrozen,YdLongFrozen,YdShortFrozen,
                                            BuyTradeVolume,SellTradeVolume,PositionCost,YdPositionCost,UseMargin,
                                            FrozenMargin,LongFrozenMargin,ShortFrozenMargin,FrozenPremium,InstrumentID,
                                            ParticipantID,ClientID
                                          FROM sync.t_ClientPosition WHERE TradeSystemID=%s"""),
            t_CurrPriceBanding=dict(columns=("SettlementGroupID", "PriceLimitType", "ValueMode", "RoundingMode",
                                             "UpperValue", "LowerValue", "InstrumentID", "TradingSegmentSN"),
                                    sql="""SELECT 'SG01' AS SettlementGroupID,PriceLimitType,ValueMode,RoundingMode,
                                                  UpperValue,LowerValue,InstrumentID,TradingSegmentSN
                                              FROM sync.t_CurrPriceBanding WHERE TradeSystemID=%s"""),
            t_InstrumentGroup=dict(columns=("TradingDay", "SettlementGroupID", "SettlementID",
                                            "InstrumentID", "InstrumentGroupID"),
                                   sql="""SELECT t1.TradingDay,'SG01' AS SettlementGroupID,'1' AS SettlementID,
                                                          InstrumentID,InstrumentGroupID
                                                  FROM sync.t_InstrumentGroup t,siminfo.t_TradeSystemTradingDay t1,
                                                       siminfo.t_TradeSystemSettlementGroup t2
                                                  WHERE t.SettlementGroupID = t2.SettlementGroupID
                                                  AND t1.TradeSystemID = t2.TradeSystemID 
                                                  AND t.TradeSystemID=%s"""),
            t_MarketData=dict(columns=("TradingDay", "SettlementGroupID", "SettlementID", "LastPrice",
                                       "PreSettlementPrice", "PreClosePrice", "PreOpenInterest", "OpenPrice",
                                       "HighestPrice", "LowestPrice", "Volume", "Turnover", "OpenInterest",
                                       "ClosePrice", "SettlementPrice", "UpperLimitPrice", "LowerLimitPrice",
                                       "PreDelta", "CurrDelta", "UpdateTime", "UpdateMillisec", "InstrumentID",
                                       "OTCLastPrice", "OTCVolume", "OTCInterestChange",),
                              sql="""SELECT t1.TradingDay,'SG01' AS SettlementGroupID,'1' AS SettlementID,
                                            LastPrice,PreSettlementPrice,PreClosePrice,PreOpenInterest,'' as OpenPrice,
                                            '' as HighestPrice,'' as LowestPrice,'0' AS Volume,'0' AS Turnover,OpenInterest,'0' as ClosePrice,
                                            SettlementPrice,UpperLimitPrice,LowerLimitPrice,PreDelta,CurrDelta,
                                            '00:00:00' as UpdateTime,'0' as UpdateMillisec,InstrumentID,
                                            '' AS OTCLastPrice,'' AS OTCVolume,'' AS OTCInterestChange
                                      FROM sync.t_MarketData t,siminfo.t_TradeSystemTradingDay t1,
                                           siminfo.t_TradeSystemSettlementGroup t2
                                      WHERE t.SettlementGroupID = t2.SettlementGroupID
                                      AND t1.TradeSystemID = t2.TradeSystemID 
                                      AND t.TradeSystemID=%s"""),
            t_MarketDataTopic=dict(columns=("TopicID", "TopicName", "MarketID", "SnapShotFeq", "MarketDataDepth",
                                            "DelaySeconds", "MarketDataMode"),
                                   sql="""SELECT TopicID,TopicName,MarketID,SnapShotFeq,
                                                 MarketDataDepth,DelaySeconds,MarketDataMode
                                          FROM sync.t_MarketDataTopic WHERE TradeSystemID=%s""",
                                   quoting=True),
            t_MdPubStatus=dict(columns=("ProductID", "InstrumentStatus", "MdPubStatus"),
                               sql="""SELECT ProductID,InstrumentStatus,MdPubStatus
                                                      FROM sync.t_MdPubStatus WHERE TradeSystemID=%s""",
                               quoting=True),
            t_PartClient=dict(columns=("ClientID", "ParticipantID"),
                              sql="""SELECT ClientID,ParticipantID FROM sync.t_PartClient WHERE TradeSystemID=%s""",
                              quoting=True),
            t_PartPosition=dict(columns=("TradingDay", "SettlementGroupID", "SettlementID", "HedgeFlag",
                                         "PosiDirection", "YdPosition", "Position", "LongFrozen", "ShortFrozen",
                                         "YdLongFrozen", "YdShortFrozen", "InstrumentID", "ParticipantID",
                                         "TradingRole"),
                                sql="""SELECT TradingDay,'SG01' AS SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,
                                              YdPosition,Position,LongFrozen,ShortFrozen,YdLongFrozen,YdShortFrozen,
                                              InstrumentID,ParticipantID,TradingRole
                                      FROM sync.t_PartPosition WHERE TradeSystemID=%s"""),
            t_PartTopicSubscribe=dict(columns=("ParticipantID", "ParticipantType", "TopicID"),
                                      sql="""SELECT DISTINCT ParticipantID,ParticipantType,TopicID
                                              FROM sync.t_PartTopicSubscribe WHERE TradeSystemID=%s""",
                                      quoting=True),
            t_User=dict(columns=("ParticipantID", "UserID", "UserType", "Password", "IsActive"),
                        sql="""SELECT DISTINCT ParticipantID,UserID,UserType,Password,IsActive
                              FROM sync.t_User WHERE TradeSystemID=%s""",
                        quoting=True),
            t_UserFunctionRight=dict(columns=("UserID", "FunctionCode"),
                                     sql="""SELECT DISTINCT UserID,FunctionCode
                                            FROM sync.t_UserFunctionRight WHERE TradeSystemID=%s""",
                                     quoting=True),
            t_UserIP=dict(columns=("UserID", "IPAddress", "IPMask"),
                          sql="""SELECT DISTINCT UserID,IPAddress,IPMask
                                  FROM sync.t_UserIP WHERE TradeSystemID=%s""",
                          quoting=True),
            t_InstrumentTradingRight=dict(columns=("InstrumentID", "InvestorRange", "BrokerID", "InvestorID",
                                                   "TradingRight"),
                                          sql="""SELECT InstrumentID,'1' AS InvestorRange,'10010' AS BrokerID,
                                                        '00000000' AS InvestorID,'0' AS TradingRight 
                                                    FROM sync.t_Instrument 
                                                    WHERE TradeSystemID = %s""",
                                          quoting=True),
        )
        # 查询sync数据库数据内容
        csv_data = mysqlDB.select(table_sqls[table_name]["sql"], (self.tradeSystemID,))
        # 生成csv文件
        self.__produce_csv(table_name, table_sqls[table_name], csv_data)

    def __generate_marketdata(self, exchange, mysqlDB):
        sql = """SELECT t.InstrumentID 
                  FROM sync.t_instrument t,
                       sync.t_settlementgroup t1 
                  WHERE t.SettlementGroupID = t1.SettlementGroupID 
                  AND t1.ExchangeID = UPPER(%s)"""
        # 查询股票数据
        txt_data = mysqlDB.select(sql, (exchange,))
        self.__produce_txt(exchange, txt_data)

    # 生成csv文件
    def __produce_csv(self, table_name, columns, csv_data):
        self.logger.info("%s%s%s" % ("开始生成 ", table_name, ".csv"))
        _path = "%s%s%s%s" % (str(self.csv_path), os.path.sep, table_name, '.csv')
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
        self.logger.info("%s%s%s" % ("生成 ", table_name, ".csv 文件完成"))

    # 生成txt文件
    def __produce_txt(self, file_name, txt_data):
        self.logger.info("%s%s%s" % ("开始生成", file_name, ".txt"))
        _csv_path = "%s%s%s" % (str(self.csv_path), os.path.sep, "md")
        _path = "%s%s%s%s%s%s" % (str(self.csv_path), os.path.sep, "md", os.path.sep, file_name, '.txt')
        # 如果不存在目录则先创建
        if not os.path.exists(_csv_path):
            os.makedirs(_csv_path)
        with open(_path, 'wb') as txt_file:
            for ins in txt_data:
                ins = str(ins[0])
                txt_file.write(ins + '\n')
        self.logger.info("%s%s%s" % ("生成 ", file_name, ".txt 文件完成"))

if __name__ == '__main__':
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql", "log", "csv"])
    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)
    # 启动脚本
    exchange_future_csv(context=context, configs=conf)
