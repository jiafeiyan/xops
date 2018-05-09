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


class exchange_future_csv:
    def __init__(self, context, configs):
        settlementGroupID = configs.get("settlementGroupID")
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="exchange_future_csv", configs=log_conf)
        if log_conf is None:
            self.logger.warning("exchange_future_csv未配置Log日志")
        # 初始化数据库连接
        self.mysqlDB = mysql(configs=context.get("mysql")[configs.get("mysqlId")])
        # 初始化tradeSystemID
        self.settlementGroupID = settlementGroupID
        # 初始化生成CSV文件路径
        output = path.convert(context.get("csv")[configs.get("csv")]['broker'])
        self.csv_path = os.path.join(output, str(configs.get("csvRoute")))
        self.__to_csv()

    def __to_csv(self):
        mysqlDB = self.mysqlDB
        # PositionDateType=1 and MaxMarginSideAlgorithm=1
        self.__data_to_csv("t_Instrument", mysqlDB)
        self.__data_to_csv("t_DepthMarketData", mysqlDB)
        self.__data_to_csv("t_ExchangeMarginRate", mysqlDB)
        # PositionDateType=1 and MortgageFundUseRange=0 and MortgageFundUseRange=0
        self.__data_to_csv("t_Product", mysqlDB)
        self.__data_to_csv("t_TradingAccount", mysqlDB)
        self.__data_to_csv("t_Investor", mysqlDB)
        self.__data_to_csv("t_InvestorAccount", mysqlDB)
        self.__data_to_csv("t_InvestorDepartmentFlat", mysqlDB)
        self.__data_to_csv("t_InvestorPassword", mysqlDB)
        self.__data_to_csv("t_LinkMan", mysqlDB)
        # self.__data_to_csv("t_MDInstrument", mysqlDB)
        self.__data_to_csv("t_ProductGroup", mysqlDB)
        self.__data_to_csv("t_IndexPrice", mysqlDB)
        # self.__data_to_csv("t_InstrumentMarginRate", mysqlDB)
        self.__data_to_csv("t_InstrumentCommissionRate", mysqlDB)
        self.__data_to_csv("t_OptionInstrCommRate", mysqlDB)
        # ======== 0301 新增 ========
        self.__data_to_csv("t_Trader", mysqlDB)
        self.__data_to_csv("t_TraderAssign", mysqlDB)
        self.__data_to_csv("t_BrokerUser", mysqlDB)
        self.__data_to_csv("t_BrokerUserPassword", mysqlDB)
        self.__data_to_csv("t_DepartmentUser", mysqlDB)
        self.__data_to_csv("t_PartBroker", mysqlDB)
        self.__data_to_csv("t_TradingAccountPassword", mysqlDB)
        self.__data_to_csv("t_TradingCode", mysqlDB)
        self.__data_to_csv("t_UserRightsAssign", mysqlDB)
        self.__data_to_csv("t_InvestorPositionDtl", mysqlDB)

    def __data_to_csv(self, table_name, mysqlDB):
        table_sqls = dict(
            t_Instrument=dict(columns=("InstrumentID", "ExchangeID", "InstrumentName", "ExchangeInstID", "ProductID",
                                       "ProductClass", "DeliveryYear", "DeliveryMonth", "MaxMarketOrderVolume",
                                       "MinMarketOrderVolume", "MaxLimitOrderVolume", "MinLimitOrderVolume",
                                       "VolumeMultiple", "PriceTick", "CreateDate", "OpenDate", "ExpireDate",
                                       "StartDelivDate", "EndDelivDate", "InstLifePhase", "IsTrading", "PositionType",
                                       "PositionDateType", "LongMarginRatio", "ShortMarginRatio",
                                       "MaxMarginSideAlgorithm", "UnderlyingInstrID", "StrikePrice",
                                       "OptionsType", "UnderlyingMultiple", "CombinationType"),
                              sql="""SELECT t.InstrumentID,t3.ExchangeID AS ExchangeID,t.InstrumentName,
                                            t.InstrumentID AS ExchangeInstID,t.ProductID,t.ProductClass,t.DeliveryYear,
                                            t.DeliveryMonth,t1.MaxMarketOrderVolume,t1.MinMarketOrderVolume,
                                            t1.MaxLimitOrderVolume,t1.MinLimitOrderVolume,t.VolumeMultiple,t1.PriceTick,
                                            t1.CreateDate,t1.OpenDate,t1.ExpireDate,t1.StartDelivDate,t1.EndDelivDate,
                                            t1.InstLifePhase,	'1' AS IsTrading,t.PositionType,t.PositionDateType,
                                            t2.LongMarginRatio,t2.ShortMarginRatio,'1' AS MaxMarginSideAlgorithm,
                                            t.UnderlyingInstrID AS tUnderlyingInstrID,t.StrikePrice,t.OptionsType,
                                            t.UnderlyingMultiple,'0' AS CombinationType
                                    FROM siminfo.t_Instrument t INNER JOIN siminfo.t_instrumentproperty t1 on 
                                    t.SettlementGroupID = t1.SettlementGroupID and t.InstrumentID = t1.InstrumentID
                                    AND t.SettlementGroupID in  """ + str(tuple([str(i) for i in self.settlementGroupID])) + """
                                    INNER JOIN siminfo.t_settlementgroup t3 on t.SettlementGroupID = t3.SettlementGroupID
                                    AND t.SettlementGroupID in  """ + str(tuple([str(i) for i in self.settlementGroupID])) + """
                                    LEFT JOIN siminfo.t_marginratedetail t2 on t.SettlementGroupID = t2.SettlementGroupID 
                                    and t.InstrumentID = t2.InstrumentID AND t.SettlementGroupID in """ +
                                  str(tuple([str(i) for i in self.settlementGroupID])),
                              quoting=True),
            t_DepthMarketData=dict(columns=("TradingDay", "InstrumentID", "ExchangeID", "ExchangeInstID", "LastPrice",
                                            "PreSettlementPrice", "PreClosePrice", "PreOpenInterest", "OpenPrice",
                                            "HighestPrice", "LowestPrice", "Volume", "Turnover", "OpenInterest",
                                            "ClosePrice", "SettlementPrice", "UpperLimitPrice", "LowerLimitPrice",
                                            "PreDelta", "CurrDelta", "UpdateTime", "UpdateMillisec", "BidPrice1",
                                            "BidVolume1", "AskPrice1", "AskVolume1", "BidPrice2", "BidVolume2",
                                            "AskPrice2", "AskVolume2", "BidPrice3", "BidVolume3", "AskPrice3",
                                            "AskVolume3", "BidPrice4", "BidVolume4", "AskPrice4", "AskVolume4",
                                            "BidPrice5", "BidVolume5", "AskPrice5", "AskVolume5", "AveragePrice",
                                            "ActionDay"),
                                   sql="""SELECT t1.TradingDay,t.InstrumentID,t2.ExchangeID,
                                        t.InstrumentID AS ExchangeInstID,t1.LastPrice,t1.PreSettlementPrice,
                                        t1.PreClosePrice,t1.PreOpenInterest,t1.OpenPrice,t1.HighestPrice,t1.LowestPrice,
                                        '0' AS Volume,'0' AS Turnover,t1.OpenInterest,t1.ClosePrice,t1.SettlementPrice,
                                        t1.UpperLimitPrice,t1.LowerLimitPrice,t1.PreDelta,t1.CurrDelta,t1.UpdateTime,
                                        t1.UpdateMillisec,'0' AS BidPrice1,'0' AS BidVolume1,'0' AS AskPrice1,
                                        '0' AS AskVolume1,'0' AS BidPrice2,'0' AS BidVolume2,'0' AS AskPrice2,
                                        '0' AS AskVolume2,'0' AS BidPrice3,'0' AS BidVolume3,'0' AS AskPrice3,
                                        '0' AS AskVolume3,'0' AS BidPrice4,'0' AS BidVolume4,'0' AS AskPrice4,
                                        '0' AS AskVolume4,'0' AS BidPrice5,'0' AS BidVolume5,'0' AS AskPrice5,
                                        '0' AS AskVolume5,'0' AS AveragePrice,'' AS ActionDay
                                    FROM siminfo.t_Instrument t,siminfo.t_MarketData t1,siminfo.t_SettlementGroup t2
                                    WHERE t.SettlementGroupID = t1.SettlementGroupID
                                    AND t.InstrumentID = t1.InstrumentID
                                    AND t.SettlementGroupID = t2.SettlementGroupID
                                    AND t.SettlementGroupID in """ +
                                       str(tuple([str(i) for i in self.settlementGroupID])),
                                   quoting=True),
            t_ExchangeMarginRate=dict(columns=("BrokerID", "InstrumentID", "HedgeFlag", "LongMarginRatioByMoney",
                                               "LongMarginRatioByVolume", "ShortMarginRatioByMoney",
                                               "ShortMarginRatioByVolume"),
                                      sql="""SELECT '10010' AS BrokerID,t.InstrumentID AS InstrumentID,
                                                t.HedgeFlag AS HedgeFlag,t.LongMarginRatio LongMarginRatioByMoney,
                                                '0' AS LongMarginRatioByVolume,t.ShortMarginRatio ShortMarginRatioByMoney,
                                                '0' AS ShortMarginRatioByVolume
                                            FROM siminfo.t_MarginRateDetail t,siminfo.t_Instrument t1
                                            WHERE t.InstrumentID = t1.InstrumentID AND t1.SettlementGroupID  in """ +
                                          str(tuple([str(i) for i in self.settlementGroupID])),
                                      quoting=True),
            t_Product=dict(columns=("ProductID", "ProductName", "ExchangeID", "ProductClass", "VolumeMultiple",
                                    "PriceTick", "MaxMarketOrderVolume", "MinMarketOrderVolume", "MaxLimitOrderVolume",
                                    "MinLimitOrderVolume", "PositionType", "PositionDateType", "CloseDealType",
                                    "TradeCurrencyID", "MortgageFundUseRange", "ExchangeProductID",
                                    "UnderlyingMultiple"),
                           sql="""SELECT t.ProductID,t3.ProductName,t2.ExchangeID,t.ProductClass,t.VolumeMultiple,
                                        t1.PriceTick,t1.MaxMarketOrderVolume,t1.MinMarketOrderVolume,
                                        t1.MaxLimitOrderVolume,t1.MinLimitOrderVolume,t.PositionType,
                                        '2' AS PositionDateType,'0' AS CloseDealType,t2.Currency AS TradeCurrencyID,
                                        '0' AS MortgageFundUseRange,'' AS ExchangeProductID,t.UnderlyingMultiple
                                    FROM siminfo.t_Instrument t,siminfo.t_InstrumentProperty t1,
                                        siminfo.t_SettlementGroup t2,siminfo.t_Product t3
                                    WHERE t.InstrumentID = t1.InstrumentID
                                    AND t.SettlementGroupID = t1.SettlementGroupID
                                    AND t.SettlementGroupID = t2.SettlementGroupID
                                    AND t.SettlementGroupID = t3.SettlementGroupID
                                    AND t.ProductID = t3.ProductID
                                    AND t.SettlementGroupID in """ +
                               str(tuple([str(i) for i in self.settlementGroupID])),
                           quoting=True),
            t_TradingAccount=dict(columns=("BrokerID", "AccountID", "PreMortgage", "PreCredit", "PreDeposit",
                                           "PreBalance", "PreMargin", "InterestBase", "Interest", "Deposit", "Withdraw",
                                           "FrozenMargin", "FrozenCash", "FrozenCommission", "CurrMargin", "CashIn",
                                           "Commission", "CloseProfit", "PositionProfit", "Balance", "Available",
                                           "WithdrawQuota", "Reserve", "TradingDay", "SettlementID", "Credit",
                                           "Mortgage", "ExchangeMargin", "DeliveryMargin", "ExchangeDeliveryMargin",
                                           "ReserveBalance", "CurrencyID", "PreFundMortgageIn", "PreFundMortgageOut",
                                           "FundMortgageIn", "FundMortgageOut", "FundMortgageAvailable",
                                           "MortgageableFund", "SpecProductMargin", "SpecProductFrozenMargin",
                                           "SpecProductCommission", "SpecProductFrozenCommission",
                                           "SpecProductPositionProfit", "SpecProductCloseProfit",
                                           "SpecProductPositionProfitByAlg", "SpecProductExchangeMargin",
                                           "FrozenSwap", "RemainSwap"),
                                  sql="""SELECT DISTINCT
                                                '10010' AS BrokerID,
                                                t.InvestorID AS AccountID,
                                                '0' AS PreMortgage,
                                                '0' AS PreCredit,
                                                t.Available AS PreDeposit,
                                                t.Available AS PreBalance,
                                                t.CurrMargin,
                                                '0' AS InterestBase,
                                                '0' AS Interest,
                                                t.Deposit,
                                                t.Withdraw,
                                                '0' AS FrozenMargin,
                                                '0' AS FrozenCash,
                                                '0' AS FrozenCommission,
                                                t.CurrMargin,
                                                '0' AS CashIn,
                                                '0' AS Commission,
                                                t.CloseProfit,
                                                '0' AS PositionProfit,
                                                t.Balance,
                                                t.Available,
                                                '0' AS WithdrawQuota,
                                                '0' AS Reserve,
                                                t1.TradingDay,
                                                '1' AS SettlementID,
                                                '0' AS Credit,
                                                '0' AS Mortgage,
                                                '0' AS ExchangeMargin,
                                                '0' AS DeliveryMargin,
                                                '0' AS ExchangeDeliveryMargin,
                                                '0' AS ReserveBalance,
                                                'CNY' AS CurrencyID,
                                                '0' AS PreFundMortgageIn,
                                                '0' AS PreFundMortgageOut,
                                                '0' AS FundMortgageIn,
                                                '0' AS FundMortgageOut,
                                                '0' AS FundMortgageAvailable,
                                                '0' AS MortgageableFund,
                                                '0' AS SpecProductMargin,
                                                '0' AS SpecProductFrozenMargin,
                                                '0' AS SpecProductCommission,
                                                '0' AS SpecProductFrozenCommission,
                                                '0' AS SpecProductPositionProfit,
                                                '0' AS SpecProductCloseProfit,
                                                '0' AS SpecProductPositionProfitByAlg,
                                                '0' AS SpecProductExchangeMargin,
                                                '0' AS FrozenSwap,
                                                '0' AS RemainSwap 
                                            FROM
                                                siminfo.t_InvestorFund t,
                                                siminfo.t_TradeSystemTradingDay t1,
                                                siminfo.t_brokersystemsettlementgroup t2,
                                                siminfo.t_tradesystembrokersystem t3 
                                            WHERE
                                                t.BrokerSystemID = t2.BrokerSystemID 
                                                AND t.BrokerSystemID = t3.BrokerSystemID 
                                                AND t3.TradeSystemID = t1.TradeSystemID 
                                                AND t2.SettlementGroupID IN """ +
                                      str(tuple([str(i) for i in self.settlementGroupID])),
                                  quoting=True),
            t_Investor=dict(columns=("InvestorID", "BrokerID", "InvestorGroupID", "InvestorName", "IdentifiedCardType",
                                     "IdentifiedCardNo", "IsActive", "Telephone", "Address", "OpenDate", "Mobile",
                                     "CommModelID", "MarginModelID"),
                            sql="""SELECT t.InvestorID AS InvestorID,'10010' AS BrokerID,'' AS InvestorGroupID,
                                        t.InvestorName AS InvestorName,'' AS IdentifiedCardType,'' AS IdentifiedCardNo,
                                        '1' AS IsActive,'' AS Telephone,'' AS Address,'' AS OpenDate,'' AS Mobile,
                                        '' AS CommModelID,'' AS MarginModelID
                                    FROM siminfo.t_Investor t""",
                            quoting=True),
            t_InvestorAccount=dict(columns=("BrokerID", "InvestorID", "AccountID", "CurrencyID"),
                                   sql="""SELECT '10010' AS BrokerID,t.InvestorID AS InvestorID,
                                                t.InvestorID AS AccountID,'CNY' AS CurrencyID
                                          FROM siminfo.t_Investor t""",
                                   quoting=True),
            t_InvestorDepartmentFlat=dict(columns=("BrokerID", "InvestorID", "DepartmentID"),
                                          sql="""SELECT '10010' AS BrokerID,t.InvestorID,'01' AS DepartmentID 
                                                 FROM siminfo.t_Investor t
                                                 UNION ALL
                                                 SELECT '10010' AS BrokerID,t.InvestorID,'0101' AS DepartmentID 
                                                 FROM siminfo.t_Investor t""",
                                          quoting=True),
            t_InvestorPassword=dict(columns=("BrokerID", "InvestorID", "Password"),
                                    sql="""SELECT '10010' AS BrokerID,t.InvestorID,t.Password 
                                            FROM siminfo.t_Investor t""",
                                    quoting=True),
            t_LinkMan=dict(columns=("BrokerID", "InvestorID", "PersonType", "IdentifiedCardType", "IdentifiedCardNo",
                                    "PersonName", "Telephone", "Address", "ZipCode", "Priority", "UOAZipCode",
                                    "PersonFullName"),
                           sql="""SELECT '10010' AS BrokerID,t.InvestorID,'1' AS PersonType,'1' AS IdentifiedCardType,
                                        '' AS IdentifiedCardNo,t.InvestorName AS PersonName,'' AS Telephone,
                                        '' AS Address,'' AS ZipCode,'0' AS Priority,'' AS UOAZipCode,
                                        t.InvestorName AS PersonFullName
                                    FROM siminfo.t_Investor t""",
                           quoting=True),
            t_MDInstrument=dict(columns=("InstrumentID", "ExchangeID", "InstrumentName", "ExchangeInstID", "ProductID",
                                         "ProductClass", "DeliveryYear", "DeliveryMonth", "MaxMarketOrderVolume",
                                         "MinMarketOrderVolume", "MaxLimitOrderVolume", "MinLimitOrderVolume",
                                         "VolumeMultiple", "PriceTick", "CreateDate", "OpenDate", "ExpireDate",
                                         "StartDelivDate", "EndDelivDate", "InstLifePhase", "IsTrading", "PositionType",
                                         "PositionDateType", "LongMarginRatio", "ShortMarginRatio",
                                         "MaxMarginSideAlgorithm", "UnderlyingInstrID", "StrikePrice", "OptionsType",
                                         "UnderlyingMultiple", "CombinationType"),
                                sql="""SELECT t.InstrumentID,t3.ExchangeID AS ExchangeID,t.InstrumentName,
                                            t.InstrumentID AS ExchangeInstID,t.ProductID,t.ProductClass,t.DeliveryYear,
                                            t.DeliveryMonth,t1.MaxMarketOrderVolume,t1.MinMarketOrderVolume,
                                            t1.MaxLimitOrderVolume,t1.MinLimitOrderVolume,t.VolumeMultiple,t1.PriceTick,
                                            t1.CreateDate,t1.OpenDate,t1.ExpireDate,t1.StartDelivDate,t1.EndDelivDate,
                                            t1.InstLifePhase,	'1' AS IsTrading,t.PositionType,'1' AS PositionDateType,
                                            t2.LongMarginRatio,t2.ShortMarginRatio,'1' AS MaxMarginSideAlgorithm,
                                            t.UnderlyingInstrID AS tUnderlyingInstrID,t.StrikePrice,t.OptionsType,
                                            t.UnderlyingMultiple,'0' AS CombinationType
                                        FROM siminfo.t_Instrument t,siminfo.t_InstrumentProperty t1,
                                            siminfo.t_MarginRateDetail t2,siminfo.t_SettlementGroup t3
                                        WHERE t.SettlementGroupID = t1.SettlementGroupID
                                        AND t.InstrumentID = t1.InstrumentID
                                        AND t.SettlementGroupID = t2.SettlementGroupID
                                        AND t.InstrumentID = t2.InstrumentID
                                        AND t.SettlementGroupID = t3.SettlementGroupID
                                        AND t.SettlementGroupID in """ +
                                    str(tuple([str(i) for i in self.settlementGroupID])),
                                quoting=True),
            t_ProductGroup=dict(columns=("ProductID", "ExchangeID", "ProductGroupID"),
                                sql="""SELECT t.ProductID,t1.ExchangeID,t.ProductGroupID
                                        FROM siminfo.t_Product t,siminfo.t_SettlementGroup t1
                                        WHERE t.SettlementGroupID = t1.SettlementGroupID
                                        AND t.SettlementGroupID IN """ +
                                    str(tuple([str(i) for i in self.settlementGroupID])),
                                quoting=True),
            t_IndexPrice=dict(columns=("BrokerID", "InstrumentID", "ClosePrice"),
                              sql="""SELECT '10010' AS BrokerID,t.InstrumentID,t.ClosePrice
                                        FROM siminfo.t_MarketData t WHERE t.SettlementGroupID in """ +
                                  str(tuple([str(i) for i in self.settlementGroupID])),
                              quoting=True),
            t_InstrumentMarginRate=dict(columns=("InstrumentID", "InvestorRange", "BrokerID", "InvestorID", "HedgeFlag",
                                                 "LongMarginRatioByMoney", "LongMarginRatioByVolume",
                                                 "ShortMarginRatioByMoney", "ShortMarginRatioByVolume", "IsRelative"),
                                        sql="""SELECT t.InstrumentID,'1' AS InvestorRange,'10010' AS BrokerID,
                                                    '00000000' AS InvestorID,t1.HedgeFlag,
                                                    t1.LongMarginRatio AS LongMarginRatioByMoney,
                                                    '0' AS LongMarginRatioByVolume,
                                                    t1.ShortMarginRatio AS ShortMarginRatioByMoney,
                                                    '0' AS ShortMarginRatioByVolume,'1' AS IsRelative
                                                FROM siminfo.t_Instrument t,siminfo.t_MarginRateDetail t1
                                                WHERE t.SettlementGroupID = t1.SettlementGroupID
                                                AND t.InstrumentID = t1.InstrumentID
                                                AND t.SettlementGroupID IN """ +
                                            str(tuple([str(i) for i in self.settlementGroupID])),
                                        quoting=True),
            t_InstrumentCommissionRate=dict(columns=("InstrumentID", "InvestorRange", "BrokerID", "InvestorID",
                                                     "OpenRatioByMoney", "OpenRatioByVolume", "CloseRatioByMoney",
                                                     "CloseRatioByVolume", "CloseTodayRatioByMoney",
                                                     "CloseTodayRatioByVolume"),
                                            sql="""SELECT t.InstrumentID,
                                                '1' AS InvestorRange,
                                                '10010' AS BrokerID,
                                                '00000000' AS InvestorID,
                                                if (t1.ValueMode = '1', t1.OpenFeeRatio , '0') as OpenRatioByMoney,
                                                if (t1.ValueMode = '2', t1.OpenFeeRatio , '0') as OpenRatioByVolume,
                                                if (t1.ValueMode = '1', t1.CloseTodayFeeRatio , '0') as CloseRatioByMoney,
                                                if (t1.ValueMode = '2', t1.CloseTodayFeeRatio , '0') as CloseRatioByVolume,
                                                if (t1.ValueMode = '1', t1.CloseTodayFeeRatio , '0') as CloseTodayRatioByMoney,
                                                if (t1.ValueMode = '2', t1.CloseTodayFeeRatio , '0') as CloseTodayRatioByVolume 
                                            FROM
                                                siminfo.t_Instrument t,
                                                siminfo.t_transfeeratedetail t1 
                                            WHERE t.SettlementGroupID = t1.SettlementGroupID
                                                and t.InstrumentID = t1.InstrumentID
                                                and t.SettlementGroupID IN """ +
                                                str(tuple([str(i) for i in self.settlementGroupID])),
                                            quoting=True),
            t_OptionInstrCommRate=dict(columns=("InstrumentID", "InvestorRange", "BrokerID", "InvestorID",
                                                "OpenRatioByMoney", "OpenRatioByVolume", "CloseRatioByMoney",
                                                "CloseRatioByVolume", "CloseTodayRatioByMoney",
                                                "CloseTodayRatioByVolume", "StrikeRatioByMoney", "StrikeRatioByVolume"),
                                       sql="""SELECT t.InstrumentID,
                                                '1' as InvestorRange,
                                                '10010' as BrokerID,
                                                '00000000' as InvestorID,
                                                if(t1.ValueMode = '1',t1.OpenFeeRatio,'0') as OpenRatioByMoney,
                                                if(t1.ValueMode = '2',t1.OpenFeeRatio,'0') as OpenRatioByVolume,
                                                if(t1.ValueMode = '1',t1.CloseTodayFeeRatio,'0') as CloseRatioByMoney,
                                                if(t1.ValueMode = '2',t1.CloseTodayFeeRatio,'0') as CloseRatioByVolume,
                                                if(t1.ValueMode = '1',t1.CloseTodayFeeRatio,'0') as CloseTodayRatioByMoney,
                                                if(t1.ValueMode = '2',t1.CloseTodayFeeRatio,'0') as CloseTodayRatioByVolume,
                                                if(t1.ValueMode = '1',t1.CloseTodayFeeRatio,'0') as StrikeRatioByMoney,
                                                if(t1.ValueMode = '2',t1.CloseTodayFeeRatio,'0') as StrikeRatioByVolume
                                            from siminfo.t_instrument t, siminfo.t_transfeeratedetail t1 
                                            where t.SettlementGroupID = t1.SettlementGroupID 
                                            and t.InstrumentID = t1.InstrumentID
                                            and t.productclass = '2' 
                                            AND t.SettlementGroupID IN """ +
                                           str(tuple([str(i) for i in self.settlementGroupID])),
                                       quoting=True),
            t_Trader=dict(columns=("ExchangeID", "TraderID", "ParticipantID", "Password", "InstallCount", "BrokerID"),
                          sql="""SELECT t2.ExchangeID,t1.UserID AS TraderID,t1.ParticipantID,
                                    '111111' Password,'1' AS InstallCount,'10010' AS BrokerID 
                                FROM siminfo.t_user t1,siminfo.t_settlementgroup t2 
                                WHERE t1.SettlementGroupID = t2.SettlementGroupID 
                                    AND t1.UserID NOT IN ( 'TRADE01', 'TRADE02' )
                                    AND t1.SettlementGroupID IN """ +
                              str(tuple([str(i) for i in self.settlementGroupID])),
                          quoting=True),
            t_TraderAssign=dict(columns=("BrokerID", "ExchangeID", "TraderID", "ParticipantID", "DRIdentityID"),
                                sql="""SELECT '10010' AS BrokerID,t2.ExchangeID,t1.UserID AS TraderID,
                                            t1.ParticipantID,'1' AS DRIdentityID 
                                        FROM siminfo.t_user t1,siminfo.t_settlementgroup t2 
                                        WHERE t1.SettlementGroupID = t2.SettlementGroupID 
                                            AND t1.UserID NOT IN ( 'TRADE01', 'TRADE02' )
                                            AND t1.SettlementGroupID IN """ +
                                    str(tuple([str(i) for i in self.settlementGroupID])),
                                quoting=True),
            t_BrokerUser=dict(columns=("BrokerID", "UserID", "UserName", "UserType", "IsActive",
                                       "IsUsingOTP", "IsAuthForce"),
                              sql="""SELECT '10010' AS BrokerID,t.InvestorID AS UserID,t.InvestorName AS UserName,
                                            '0' AS UserType,'1' AS IsActive,'0' AS IsUsingOTP,
                                            '0' AS IsAuthForce 
                                        FROM siminfo.t_investor t UNION ALL
                                        SELECT '10010' AS BrokerID,'10010_admin' AS UserID,
                                            '10010_admin' AS UserName,'1' AS UserType,'1' AS IsActive,
                                            '0' AS IsUsingOTP,'0' AS IsAuthForce""",
                              quoting=True),
            t_BrokerUserPassword=dict(columns=("BrokerID", "UserID", "Password", "LastUpdateTime", "LastLoginTime",
                                               "ExpireDate", "WeakExpireDate"),
                                      sql="""SELECT '10010' AS BrokerID,t.InvestorID AS UserID,t.`Password` AS PASSWORD,
                                                '' AS LastUpdateTime,'20180101' AS LastLoginTime,'' AS ExpireDate,
                                                '' AS WeakExpireDate 
                                        FROM siminfo.t_investor t UNION ALL
                                        SELECT '10010' AS BrokerID,'10010_admin' AS UserID,'10010_admin' AS PASSWORD,
                                                '' AS LastUpdateTime,'20180101' AS LastLoginTime,'' AS ExpireDate,
                                                '' AS WeakExpireDate""",
                                      quoting=True),
            t_DepartmentUser=dict(columns=("BrokerID", "UserID", "InvestorRange", "InvestorID"),
                                  sql="""SELECT '10010' AS BrokerID,t.InvestorID AS UserID,'3' AS InvestorRange,
                                            t.InvestorID FROM siminfo.t_investor t UNION ALL
                                         SELECT '10010' AS BrokerID,'10010_admin' AS UserID,
                                            '1' AS InvestorRange,'00000000' AS InvestorID""",
                                  quoting=True),
            t_PartBroker=dict(columns=("BrokerID", "ExchangeID", "ParticipantID", "IsActive"),
                              sql="""SELECT '10010' AS BrokerID,t.ExchangeID AS ExchangeID,t1.ParticipantID,t1.IsActive 
                                    FROM siminfo.t_settlementgroup t,siminfo.t_participant t1
                                    WHERE t.SettlementGroupID = t1.SettlementGroupID
                                    AND t.SettlementGroupID IN """ +
                                  str(tuple([str(i) for i in self.settlementGroupID])),
                              quoting=True),
            t_TradingAccountPassword=dict(columns=("BrokerID", "AccountID", "Password", "CurrencyID"),
                                          sql="""SELECT
                                                    '10010' AS BrokerID,
                                                    t.InvestorID AS AccountID,
                                                    t.`Password` AS PASSWORD,
                                                    'CNY' AS CurrencyID 
                                                FROM siminfo.t_investor t""",
                                          quoting=True),
            t_TradingCode=dict(columns=("InvestorID", "BrokerID", "ExchangeID", "ClientID", "IsActive", "ClientIDType"),
                               sql="""SELECT t.InvestorID,'10010' AS BrokerID,t1.ExchangeID,t.ClientID,
                                            t2.IsActive,'1' AS ClientIDType 
                                      FROM siminfo.t_investorclient t,siminfo.t_settlementgroup t1,siminfo.t_client t2 
                                      WHERE t.SettlementGroupID = t1.SettlementGroupID 
                                      AND t.SettlementGroupID = t2.SettlementGroupID 
                                      AND t.ClientID = t2.ClientID AND t.SettlementGroupID IN """ +
                                   str(tuple([str(i) for i in self.settlementGroupID])),
                               quoting=True),
            t_UserRightsAssign=dict(columns=("BrokerID", "UserID", "DRIdentityID"),
                                    sql="""SELECT '10010' AS BrokerID,t.InvestorID AS UserID,'1' AS DRIdentityID 
                                            FROM siminfo.t_investor t
                                            UNION ALL 
                                            SELECT '10010' AS BrokerID,'10010_admin' AS UserID,'1' AS DRIdentityID """,
                                    quoting=True),

            t_InvestorPositionDtl=dict(columns=("InstrumentID", "BrokerID", "InvestorID", "HedgeFlag", "Direction",
                                                "OpenDate", "TradeID", "Volume", "OpenPrice", "TradingDay",
                                                "SettlementID", "TradeType", "CombInstrumentID", "ExchangeID",
                                                "CloseProfitByDate", "CloseProfitByTrade", "PositionProfitByDate",
                                                "PositionProfitByTrade", "Margin", "ExchMargin", "MarginRateByMoney",
                                                "MarginRateByVolume", "LastSettlementPrice", "SettlementPrice",
                                                "CloseVolume", "CloseAmount"),
                                       sql="""select InstrumentID,'10010' as BrokerID,InvestorID,HedgeFlag,Direction,
                                                    OpenDate,TradeID,Volume,OpenPrice,TradingDay,SettlementID,TradeType,
                                                    CombInstrumentID,ExchangeID,CloseProfitByDate,CloseProfitByTrade,
                                                    PositionProfitByDate,PositionProfitByTrade,Margin,ExchMargin,
                                                    MarginRateByMoney,MarginRateByVolume,LastSettlementPrice,
                                                    SettlementPrice,CloseVolume,CloseAmount 
                                                    from sync.t_futurepositiondtl
                                                where SettlementGroupID in """ +
                                           str(tuple([str(i) for i in self.settlementGroupID])),
                                       quoting=True),
        )
        # 查询sync数据库数据内容
        csv_data = mysqlDB.select(table_sqls[table_name]["sql"], table_sqls[table_name].get("params"))
        # 生成csv文件
        self.__produce_csv(table_name, table_sqls[table_name], csv_data)

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


if __name__ == '__main__':
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql", "log", "csv"])
    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)
    # 启动脚本
    exchange_future_csv(context=context, configs=conf)
