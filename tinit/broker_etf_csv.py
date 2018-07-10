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


class broker_etf_csv:
    def __init__(self, context, configs):
        # 初始化settlementGroupID
        self.settlementGroupID = configs.get("settlementGroupID")
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="future_to_csv", configs=log_conf)
        if log_conf is None:
            self.logger.warning("broker_etf_csv未配置Log日志")
        # 初始化数据库连接
        self.mysqlDB = mysql(configs=context.get("mysql")[configs.get("mysqlId")])
        # 初始化生成柜台CSV文件路径
        output = path.convert(context.get("csv")[configs.get("csv")]['broker'])
        self.csv_path = os.path.join(output, str(configs.get("csvRoute")), str(configs.get("settlementGroupID")))
        self.__to_csv()

    def __to_csv(self):
        mysqlDB = self.mysqlDB
        self.__data_to_csv("BUProxy", mysqlDB)
        self.__data_to_csv("BusinessUnit", mysqlDB)
        self.__data_to_csv("ExchangeTradingDay", mysqlDB)
        self.__data_to_csv("Investor", mysqlDB)
        self.__data_to_csv("InvestorLimitAmount", mysqlDB)
        self.__data_to_csv("SSEBusinessUnitAccount", mysqlDB)
        self.__data_to_csv("SSEMarketData", mysqlDB)
        self.__data_to_csv("SSEPosition", mysqlDB)
        self.__data_to_csv("SSESecurity", mysqlDB)
        self.__data_to_csv("SSEShareholderAccount", mysqlDB)
        self.__data_to_csv("SSEShareholderTradingRight", mysqlDB)
        self.__data_to_csv("TradingAccount", mysqlDB)
        self.__data_to_csv("User", mysqlDB)
        self.__data_to_csv("SSEInvestorLimitPositionParam", mysqlDB)
        self.__data_to_csv("SSEInvestorMarginFee", mysqlDB)
        self.__data_to_csv("SSEInvestorTradingFee", mysqlDB)
        self.__data_to_csv("InvestorCondOrderLimitParam", mysqlDB)

    def __data_to_csv(self, csv_name, mysqlDB):
        table_sqls = dict(
            BUProxy=dict(columns=("UserID", "InvestorID", "BusinessUnitID"),
                         sql="""SELECT t.InvestorID AS UserID,t.InvestorID AS InvestorID,t.InvestorID AS BusinessUnitID
                                FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1
                                WHERE t.InvestorID = t1.InvestorID AND t1.SettlementGroupID = %s
                                UNION ALL
                                SELECT 'broker' AS UserID,t.InvestorID AS InvestorID,t.InvestorID AS BusinessUnitID
                                FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1
                                WHERE t.InvestorID = t1.InvestorID AND t1.SettlementGroupID = %s
                                UNION ALL
                                SELECT 'broker1' AS UserID,t.InvestorID AS InvestorID,t.InvestorID AS BusinessUnitID
                                FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1
                                WHERE t.InvestorID = t1.InvestorID AND t1.SettlementGroupID = %s
                                UNION ALL
                                SELECT 'admin' AS UserID,t.InvestorID AS InvestorID,t.InvestorID AS BusinessUnitID
                                FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1
                                WHERE t.InvestorID = t1.InvestorID AND t1.SettlementGroupID = %s
                                UNION ALL
                                SELECT 'admin1' AS UserID,t.InvestorID AS InvestorID,t.InvestorID AS BusinessUnitID
                                FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1
                                WHERE t.InvestorID = t1.InvestorID AND t1.SettlementGroupID = %s""",
                         params=(self.settlementGroupID, self.settlementGroupID, self.settlementGroupID,
                                 self.settlementGroupID, self.settlementGroupID)),
            BusinessUnit=dict(columns=("InvestorID", "BusinessUnitID", "BusinessUnitName"),
                              sql="""SELECT t.InvestorID,t.InvestorID AS BusinessUnitID,
                                            CONCAT('BU', t.InvestorID) AS BusinessUnitName
                                    FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1
                                    WHERE t.InvestorID = t1.InvestorID AND t1.SettlementGroupID = %s""",
                              params=(self.settlementGroupID,)),
            ExchangeTradingDay=dict(columns=("ExchangeID", "TradingDay"),
                                    sql="""SELECT 0 AS ExchangeID,t.TradingDay
                                            FROM siminfo.t_TradeSystemTradingDay t,siminfo.t_TradeSystemSettlementGroup t1
                                            WHERE t.TradeSystemID = t1.TradeSystemID AND t1.SettlementGroupID = %s
                                            UNION ALL
                                            SELECT '1' AS ExchangeID,t.TradingDay
                                            FROM siminfo.t_TradeSystemTradingDay t,siminfo.t_TradeSystemSettlementGroup t1
                                            WHERE t.TradeSystemID = t1.TradeSystemID AND t1.SettlementGroupID = %s""",
                                    params=(self.settlementGroupID, self.settlementGroupID)),
            Investor=dict(columns=("InvestorID", "DepartmentID", "InvestorType", "InvestorName", "IdCardType",
                                   "IdCardNo", "ContractNo", "OpenDate", "CloseDate", "Status", "InnerBranchID",
                                   "InvestorLevel", "Remark"),
                          sql="""SELECT t.InvestorID,'0001' AS DepartmentID,'0' AS InvestorType,InvestorName,
                                        '1' AS IdCardType,OpenID AS IdCardNo,'' AS ContractNo,'' AS OpenDate,
                                        '' AS CloseDate,'1' AS STATUS,'0001' AS InnerBranchID,'1' AS InvestorLevel,
                                        '' AS Remark 
                                  FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1
                                  WHERE t.InvestorID = t1.InvestorID
                                  AND t1.SettlementGroupID = %s""",
                          params=(self.settlementGroupID,)),
            InvestorLimitAmount=dict(columns=("InvestorID", "LongAmountLimit", "LongAmountFrozen"),
                                     sql="""SELECT t.InvestorID,'10000000000' AS LongAmountLimit,'0' AS LongAmountFrozen
                                            FROM siminfo.t_Investor t, siminfo.t_InvestorClient t1
                                            WHERE t.InvestorID = t1.InvestorID AND t1.SettlementGroupID = %s""",
                                     params=(self.settlementGroupID,)),
            SSEBusinessUnitAccount=dict(columns=("UserID", "InvestorID", "BusinessUnitID", "ExchangeID",
                                                 "MarketID", "ShareholderID", "ShareholderIDType", "ProductID",
                                                 "AccountID", "CurrencyID"),
                                        sql="""SELECT t.InvestorID AS UserID,t.InvestorID AS InvestorID,
                                                        t.InvestorID AS BusinessUnitID,'1' AS ExchangeID,'1' AS MarketID,
                                                        t.ClientID AS ShareholderID,'3' AS ShareholderIDType,
                                                        'd' AS ProductID,t.InvestorID AS AccountID,'1' AS CurrencyID
                                                FROM siminfo.t_InvestorClient t WHERE t.SettlementGroupID = %s
                                                UNION ALL 
                                                SELECT 'broker' AS UserID,t.InvestorID AS InvestorID,
                                                        t.InvestorID AS BusinessUnitID,'1' AS ExchangeID,'1' AS MarketID,
                                                        t.ClientID AS ShareholderID,'3' AS ShareholderIDType,
                                                        'd' AS ProductID,t.InvestorID AS AccountID,'1' AS CurrencyID
                                                FROM siminfo.t_InvestorClient t WHERE t.SettlementGroupID = %s
                                                UNION ALL 
                                                SELECT 'broker1' AS UserID,t.InvestorID AS InvestorID,
                                                        t.InvestorID AS BusinessUnitID,'1' AS ExchangeID,'1' AS MarketID,
                                                        t.ClientID AS ShareholderID,'3' AS ShareholderIDType,
                                                        'd' AS ProductID,t.InvestorID AS AccountID,'1' AS CurrencyID
                                                FROM siminfo.t_InvestorClient t WHERE t.SettlementGroupID = %s
                                                UNION ALL 
                                                SELECT 'admin' AS UserID,t.InvestorID AS InvestorID,
                                                        t.InvestorID AS BusinessUnitID,'1' AS ExchangeID,'1' AS MarketID,
                                                        t.ClientID AS ShareholderID,'3' AS ShareholderIDType,
                                                        'd' AS ProductID,t.InvestorID AS AccountID,'1' AS CurrencyID
                                                FROM siminfo.t_InvestorClient t WHERE t.SettlementGroupID = %s
                                                UNION ALL 
                                                SELECT 'admin1' AS UserID,t.InvestorID AS InvestorID,
                                                        t.InvestorID AS BusinessUnitID,'1' AS ExchangeID,'1' AS MarketID,
                                                        t.ClientID AS ShareholderID,'3' AS ShareholderIDType,
                                                        'd' AS ProductID,t.InvestorID AS AccountID,'1' AS CurrencyID
                                                FROM siminfo.t_InvestorClient t WHERE t.SettlementGroupID = %s""",
                                        params=(self.settlementGroupID, self.settlementGroupID,
                                                self.settlementGroupID, self.settlementGroupID,
                                                self.settlementGroupID)),
            SSEMarketData=dict(columns=("SecurityID", "ExchangeID", "TradingDay", "SecurityName", "PreClosePrice",
                                        "OpenPrice", "UpperLimitPrice", "LowerLimitPrice", "Volume", "Turnover",
                                        "TradingCount", "LastPrice", "ClosePrice", "HighestPrice", "LowestPrice",
                                        "PERatio1", "PERatio2", "PriceUpDown1", "PriceUpDown2", "OpenInterest",
                                        "BidPrice1", "AskPrice1", "BidVolume1", "AskVolume1", "BidPrice2", "BidVolume2",
                                        "AskPrice2", "AskVolume2", "BidPrice3", "BidVolume3", "AskPrice3", "AskVolume3",
                                        "BidPrice4", "BidVolume4", "AskPrice4", "AskVolume4", "BidPrice5", "BidVolume5",
                                        "AskPrice5", "AskVolume5", "UpdateTime", "UpdateMillisec"),
                               sql="""SELECT t.InstrumentID AS SecurityID,'1' AS ExchangeID,t.TradingDay AS TradingDay,
                                            t2.InstrumentName AS SecurityName,t.PreClosePrice AS PreClosePrice,
                                            t.OpenPrice AS OpenPrice,t.UpperLimitPrice AS UpperLimitPrice,
                                            t.LowerLimitPrice AS LowerLimitPrice,t.Volume AS Volume,
                                            t.Turnover AS Turnover,"0" AS TradingCount,t.LastPrice AS LastPrice,
                                            t.ClosePrice AS ClosePrice,t.HighestPrice AS HighestPrice,
                                            t.LowestPrice AS LowestPrice,'0' AS PERatio1,'0' AS PERatio2,
                                            '0' AS PriceUpDown1,'0' AS PriceUpDown2,t.OpenInterest AS OpenInterest,
                                            '0' AS BidPrice1,'0' AS AskPrice1,'0' AS BidVolume1,'0' AS AskVolume1,
                                            '0' AS BidPrice2,'0' AS BidVolume2,'0' AS AskPrice2,'0' AS AskVolume2,
                                            '0' AS BidPrice3,'0' AS BidVolume3,'0' AS AskPrice3,'0' AS AskVolume3,
                                            '0' AS BidPrice4,'0' AS BidVolume4,'0' AS AskPrice4,'0' AS AskVolume4,
                                            '0' AS BidPrice5,'0' AS BidVolume5,'0' AS AskPrice5,'0' AS AskVolume5,
                                            '00:00:00' AS UpdateTime,'0' AS UpdateMillisec
                                        FROM siminfo.t_MarketData t,siminfo.t_Instrument t2
                                        WHERE t.SettlementGroupID = t2.SettlementGroupID
                                        AND t.InstrumentID = t2.InstrumentID
                                        AND t.SettlementGroupID = %s""",
                               params=(self.settlementGroupID,)),
            SSEPosition=dict(columns=("InvestorID", "BusinessUnitID", "MarketID", "ShareholderID", "TradingDay",
                                      "ExchangeID", "SecurityID", "PosiDirection", "HedgeFlag", "HistoryPos",
                                      "HistoryPosFrozen", "TodayPos", "TodayPosFrozen", "TotalPosCost", "LongFrozen",
                                      "ShortFrozen", "LongFrozenAmount", "ShortFrozenAmount", "OpenVolume",
                                      "CloseVolume", "OpenAmount", "CloseAmount", "Margin", "FrozenMargin",
                                      "FrozenCash", "FrozenCommission", "CashIn", "Commission", "StrikeFrozen",
                                      "StrikeFrozenAmount", "PrePosition", "HistoryPosPrice", "HistoryCombPos",
                                      "TodayCombPos",
                                      "HistoryCombPosSplitFrozen", "TodayCombPosSplitFrozen", "HistoryPosCombFrozen",
                                      "TodayPosCombFrozen"),
                             sql="""SELECT t1.InvestorID AS InvestorID,t1.InvestorID AS BusinessUnitID,'1' AS MarketID,
                                        t.ClientID AS ShareholderID,t2.TradingDay AS TradingDay,'1' AS ExchangeID,
                                        t.InstrumentID AS SecurityID,t.PosiDirection AS PosiDirection,
                                        t.HedgeFlag AS HedgeFlag,t.YdPosition AS HistoryPos,'0' AS HistoryPosFrozen,
                                        '0' AS TodayPos,'0' AS TodayPosFrozen,t.YdPositionCost AS TotalPosCost,
                                        t.LongFrozen AS LongFrozen,t.ShortFrozen ShortFrozen,'0' AS LongFrozenAmount,
                                        '0' AS ShortFrozenAmount,'30' AS OpenVolume,'0' AS CloseVolume,
                                        '0' AS OpenAmount,'0' AS CloseAmount,t.UseMargin AS Margin,
                                        t.FrozenMargin AS FrozenMargin,'0' AS FrozenCash,'0' AS FrozenCommission,
                                        '0' AS cashIn,'0' AS Commission,'0' AS StrikeFrozen,'0' AS StrikeFrozenAmount,
                                        t.YdPosition AS PrePosition,'0' AS HistoryPosPrice,'0' AS HistoryCombPos,'0' AS TodayCombPos,
                                        '0' AS HistoryCombPosSplitFrozen,'0' AS TodayCombPosSplitFrozen,'0' AS HistoryPosCombFrozen,'0' AS TodayPosCombFrozen
                                    FROM siminfo.t_ClientPosition t,siminfo.t_InvestorClient t1,
                                         siminfo.t_TradeSystemTradingDay t2,siminfo.t_TradeSystemSettlementGroup t3
                                    WHERE t.ClientID = t1.ClientID
                                    AND t.SettlementGroupID = t1.SettlementGroupID
                                    AND t1.SettlementGroupID = t3.SettlementGroupID
                                    AND t3.TradeSystemID = t2.TradeSystemID
                                    AND t.SettlementGroupID = %s""",
                             params=(self.settlementGroupID,)),
            SSESecurity=dict(
                columns=("ExchangeID", "SecurityID", "ExchSecurityID", "SecurityName", "UnderlyingSecurityID",
                         "UnderlyingSecurityName", "UnderlyingMultiple", "StrikeMode", "OptionsType",
                         "MarketID", "ProductID", "SecurityType", "CurrencyID", "OrderUnit",
                         "BuyTradingUnit", "SellTradingUnit", "MaxMarketOrderBuyVolume",
                         "MinMarketOrderBuyVolume", "MaxLimitOrderBuyVolume", "MinLimitOrderBuyVolume",
                         "MaxMarketOrderSellVolume", "MinMarketOrderSellVolume",
                         "MaxLimitOrderSellVolume", "MinLimitOrderSellVolume", "VolumeMultiple",
                         "PriceTick", "PositionType", "SecurityStatus", "StrikePrice", "FirstDate",
                         "LastDate", "StrikeDate", "ExpireDate", "DelivDate", "IsUpDownLimit",
                         "MarginUnit", "PreSettlemetPrice", "PreClosePrice", "UnderlyingPreClosePrice"),
                sql="""SELECT '1' AS ExchangeID,
                                        t.InstrumentID AS SecurityID,
                                        t.ExchInstrumentID AS ExchSecurityID,
                                        t.InstrumentName AS SecurityName,
                                        t.UnderlyingInstrID AS UnderlyingSecurityID,
                                        '50ETF' AS UnderlyingSecurityName,
                                        t.UnderlyingMultiple AS UnderlyingMultiple,
                                        '0' AS StrikeMode,
                                        t.OptionsType AS OptionsType,
                                        '1' AS MarketID,
                                        'd' AS ProductID,
                                        CASE WHEN t.OptionsType LIKE '1' THEN '3'
                                        WHEN t.OptionsType LIKE '2' THEN '4'
                                        END AS SecurityType,
                                        '1' AS CurrencyID,
                                        '3' AS OrderUnit,
                                        '1' AS BuyTradingUnit,
                                        '1' AS SellTradingUnit,
                                        t1.MaxMarketOrderVolume AS MaxMarketOrderBuyVolume,
                                        t1.MinMarketOrderVolume AS MinMarketOrderBuyVolume,
                                        t1.MaxLimitOrderVolume AS MaxLimitOrderBuyVolume,
                                        t1.MinLimitOrderVolume AS MinLimitOrderBuyVolume,
                                        t1.MaxMarketOrderVolume AS MaxMarketOrderSellVolume,
                                        t1.MinMarketOrderVolume AS MinMarketOrderSellVolume,
                                        t1.MaxLimitOrderVolume AS MaxLimitOrderSellVolume,
                                        t1.MinLimitOrderVolume AS MinLimitOrderSellVolume,
                                        t.VolumeMultiple AS VolumeMultiple,
                                        t1.PriceTick AS PriceTick,
                                        t.PositionType AS PositionType,
                                        '0' AS SecurityStatus,
                                        t.StrikePrice AS StrikePrice,
                                        t1.OpenDate AS FirstDate,
                                        t1.ExpireDate AS LastDate,
                                        t1.StrikeDate AS StrikeDate,
                                        t1.ExpireDate AS ExpireDate,
                                        t1.StartDelivDate AS DelivDate,
                                        '1' AS IsUpDownLimit,
                                        t3.ShortMarginRatio AS MarginUnit,
                                        t2.PreSettlementPrice AS PreSettlemetPrice,
                                        t2.PreClosePrice AS PreClosePrice,
                                        t2.UnderlyingClosePx AS UnderlyingPreClosePrice
                                    FROM
                                        siminfo.t_Instrument t,
                                        siminfo.t_InstrumentProperty t1,
                                        siminfo.t_MarketData t2,
                                        siminfo.t_MarginRateDetail t3
                                    WHERE
                                        t.InstrumentID = t1.InstrumentID
                                    AND t.InstrumentID = t2.InstrumentID
                                    AND t.InstrumentID = t3.InstrumentID
                                    AND t.SettlementGroupID = t1.SettlementGroupID
                                    AND t.SettlementGroupID = t2.SettlementGroupID
                                    AND t.SettlementGroupID = t3.SettlementGroupID
                                    AND t.SettlementGroupID = %s""",
                params=(self.settlementGroupID,)),
            SSEShareholderAccount=dict(columns=("ExchangeID", "ShareholderID", "MarketID", "InvestorID",
                                                "ShareholderIDType", "PbuID", "BranchID"),
                                       sql="""SELECT '1' AS ExchangeID,t.ClientID AS ShareholderID,'1' AS MarketID,
                                                t.InvestorID AS InvestorID,'3' AS ShareholderIDType,'25377' AS PbuID,
                                                '2340' AS BranchID
                                            FROM siminfo.t_InvestorClient t WHERE t.SettlementGroupID = %s""",
                                       params=(self.settlementGroupID,)),
            SSEShareholderTradingRight=dict(columns=("MarketID", "ShareholderID", "SystemFlag", "ProductID",
                                                     "SecurityType", "SecurityID", "OffsetFlag", "Direction",
                                                     "HedgeFlag", "ExchangeID", "bForbidden"),
                                            sql="""SELECT '1' AS MarketID,'00000000' AS ShareholderID,'2' AS SystemFlag,
                                                        'd' AS ProductID,'0' AS SecurityType,'00000000' AS SecurityID,
                                                        '0' AS OffsetFlag,'0' AS Direction,'1' AS HedgeFlag,'1' AS ExchangeID,'0' AS bForbidden
                                                    UNION ALL
                                                    SELECT '1' AS MarketID,'00000000' AS ShareholderID,'2' AS SystemFlag,
                                                        'd' AS ProductID,'0' AS SecurityType,'00000000' AS SecurityID,
                                                        '0' AS OffsetFlag,'1' AS Direction,'1' AS HedgeFlag,'1' AS ExchangeID,'0' AS bForbidden
                                                    UNION ALL
                                                    SELECT '1' AS MarketID,'00000000' AS ShareholderID,'2' AS SystemFlag,
                                                        'd' AS ProductID,'0' AS SecurityType,'00000000' AS SecurityID,
                                                        '1' AS OffsetFlag,'0' AS Direction,'1' AS HedgeFlag,'1' AS ExchangeID,'0' AS bForbidden
                                                    UNION ALL
                                                    SELECT '1' AS MarketID,'00000000' AS ShareholderID,'2' AS SystemFlag,
                                                        'd' AS ProductID,'0' AS SecurityType,'00000000' AS SecurityID,
                                                        '1' AS OffsetFlag,'1' AS Direction,'1' AS HedgeFlag,'1' AS ExchangeID,'0' AS bForbidden
                                                    UNION ALL
                                                    SELECT '1' AS MarketID,'00000000' AS ShareholderID,'2' AS SystemFlag,
                                                        'd' AS ProductID,'0' AS SecurityType,'00000000' AS SecurityID,
                                                        '0' AS OffsetFlag,'1' AS Direction,'4' AS HedgeFlag,'1' AS ExchangeID,'0' AS bForbidden
                                                    UNION ALL
                                                    SELECT '1' AS MarketID,'00000000' AS ShareholderID,'2' AS SystemFlag,
                                                        'd' AS ProductID,'0' AS SecurityType,'00000000' AS SecurityID,
                                                        '1' AS OffsetFlag,'1' AS Direction,'4' AS HedgeFlag,'1' AS ExchangeID,'0' AS bForbidden
                                                    UNION ALL
                                                    SELECT '1' AS MarketID,'00000000' AS ShareholderID,'2' AS SystemFlag,
                                                        'd' AS ProductID,'0' AS SecurityType,'00000000' AS SecurityID,
                                                        '7' AS OffsetFlag,'1' AS Direction,'1' AS HedgeFlag,'1' AS ExchangeID,'0' AS bForbidde"""),
            TradingAccount=dict(columns=("DepartmentID", "AccountID", "CurrencyID", "AccountType", "PreDeposit",
                                         "PreFrozenCash", "UsefulMoney", "FetchLimit", "Deposit", "Withdraw",
                                         "FrozenMargin", "FrozenCash", "FrozenCommission", "CurrMargin", "Commission",
                                         "RoyaltyIn", "RoyaltyOut", "BankAccountID", "BankID", "AccountOwner"),
                                sql="""SELECT '0001' AS DepartmentID,t.InvestorID AS AccountID,'1' AS CurrencyID,
                                                '3' AS AccountType,t.Balance AS PreDeposit,'0' AS PreFrozenCash,
                                                t.Available AS UsefulMoney,t.Available AS FetchLimit,
                                                t.Deposit AS Deposit,t.Withdraw AS Withdraw,'0' AS FrozenMargin,
                                                '0' AS FrozenCash,'0' AS FrozenCommission,'0' AS CurrMargin,
                                                '0' AS Commission,'0' AS RoyaltyIn,'0' AS RoyaltyOut,
                                                '2' AS BankAccountID, '1' AS BankID,
                                                t.InvestorID AS AccountOwner
                                            FROM siminfo.t_InvestorFund t,siminfo.t_BrokerSystemSettlementGroup t1
                                            WHERE t.BrokerSystemID = t1.BrokerSystemID AND t1.SettlementGroupID = %s""",
                                params=(self.settlementGroupID,)),
            User=dict(columns=("UserID", "UserName", "UserType", "DepartmentID", "UserPassword", "LoginLimit",
                               "PasswordFailLimit", "Status", "Contacter", "Fax", "Telephone", "Email", "Address",
                               "ZipCode", "OpenDate", "CloseDate", "CommFlux"),
                      sql="""SELECT t.InvestorID AS UserID,t.InvestorName AS UserName,'2' AS UserType,
                            '0001' AS DepartmentID,t.PASSWORD AS UserPassword,'10' AS LoginLimit,
                            '3' AS PasswordFailLimit,'3' AS STATUS,'' AS Contacter,'' AS Fax,'' AS Telephone,
                            '' AS Email,'' AS Address,'' AS ZipCode,'' AS OpenDate,'' AS CloseDate,'0' AS CommFlux
                        FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1
                        WHERE t.InvestorID = t1.InvestorID AND t1.SettlementGroupID =  %s
                        UNION ALL
                        SELECT 'broker' AS UserID,'操作员broker' AS UserName,'0' AS UserType,
                            '0001' AS DepartmentID,'sim@2018' AS UserPassword,'10' AS LoginLimit,
                            '3' AS PasswordFailLimit,'3' AS STATUS,'' AS Contacter,'' AS Fax,'' AS Telephone,
                            '' AS Email,'' AS Address,'' AS ZipCode,'' AS OpenDate,'' AS CloseDate,'0' AS CommFlux
                        UNION ALL
                        SELECT 'broker1' AS UserID,'操作员broker1' AS UserName,'0' AS UserType,
                            '0001' AS DepartmentID,'sim@2018' AS UserPassword,'10' AS LoginLimit,
                            '3' AS PasswordFailLimit,'3' AS STATUS,'' AS Contacter,'' AS Fax,'' AS Telephone,
                            '' AS Email,'' AS Address,'' AS ZipCode,'' AS OpenDate,'' AS CloseDate,'0' AS CommFlux
                        UNION ALL
                        SELECT 'admin' AS UserID,'管理员admin' AS UserName,'1' AS UserType,
                            '0001' AS DepartmentID,'sim@2018' AS UserPassword,'10' AS LoginLimit,
                            '3' AS PasswordFailLimit,'3' AS STATUS,'' AS Contacter,'' AS Fax,'' AS Telephone,
                            '' AS Email,'' AS Address,'' AS ZipCode,'' AS OpenDate,'' AS CloseDate,'0' AS CommFlux
                        UNION ALL
                        SELECT 'admin1' AS UserID,'管理员admin1' AS UserName,'1' AS UserType,
                            '0001' AS DepartmentID,'sim@2018' AS UserPassword,'10' AS LoginLimit,
                            '3' AS PasswordFailLimit,'3' AS STATUS,'' AS Contacter,'' AS Fax,'' AS Telephone,
                            '' AS Email,'' AS Address,'' AS ZipCode,'' AS OpenDate,'' AS CloseDate,'0' AS CommFlux""",
                      params=(self.settlementGroupID,)),
            SSEInvestorLimitPositionParam=dict(columns=("InvestorID", "ExchangeID", "ProductID", "SecurityID",
                                                        "LimitPositionUnit", "TotalPositionLimit", "LongPositionLimit",
                                                        "TodayBuyOpenLimit", "TodaySellOpenLimit",
                                                        "TodayCoveredOpenLimit", "TodayOpenLimit",
                                                        "LongCallPositionLimit", "LongPutPositionLimit",
                                                        "LongUnderlyingPositionLimit", "ShortUnderlyingPositionLimit"),
                                               sql="""SELECT t.InvestorID,'1' AS ExchangeID,'d' AS ProductID,
                                                            '0' AS SecurityID,'2' AS LimitPositionUnit,
                                                            '1000000' AS TotalPositionLimit,'800000' AS LongPositionLimit,
                                                            '200000' AS TodayBuyOpenLimit,'200000' AS TodaySellOpenLimit,
                                                            '200000' AS TodayCoveredOpenLimit,'500000' AS TodayOpenLimit,
                                                            '0' AS LongCallPositionLimit,'0' AS LongPutPositionLimit,
                                                            '0' AS LongUnderlyingPositionLimit,'0' AS ShortUnderlyingPositionLimit
                                                    FROM siminfo.t_Investor t,siminfo.t_InvestorClient t1
                                                    WHERE t.InvestorID = t1.InvestorID
                                                        AND t1.SettlementGroupID = %s""",
                                               params=(self.settlementGroupID,)),
            SSEInvestorMarginFee=dict(columns=("DepartmentID", "InvestorID", "ExchangeID", "ProductID", "SecurityType",
                                               "SecurityID", "BusinessClass", "FeeByVolume", "PriceAdjustRatio",
                                               "OTMPreferRatio", "PriceAdjustGuardRatio", "UpperRatio"),
                                      sql="""SELECT '0001' AS DepartmentID,'00000000' AS InvestorID,
                                                    '1' AS ExchangeID,'d' AS ProductID,
                                                CASE WHEN t.OptionsType LIKE '1' THEN '3'
                                                WHEN t.OptionsType LIKE '2' THEN '4' END AS SecurityType,
                                                 t.InstrumentID,'C' AS BusinessClass,'120' AS FeeByVolume,
                                                 t1.AdjustRatio1 / 100 AS PriceAdjustRatio,'1' AS OTMPreferRatio,
                                                 t1.AdjustRatio2 / 100 AS PriceAdjustGuardRatio,'0' AS UpperRatio
                                                FROM t_Instrument t,t_MarginRateDetail t1
                                                WHERE t.InstrumentID = t1.InstrumentID
                                                AND t.SettlementGroupID = t1.SettlementGroupID
                                                AND t.SettlementGroupID = %s""",
                                      params=(self.settlementGroupID,)),
            SSEInvestorTradingFee=dict(columns=("DepartmentID", "InvestorID", "ExchangeID", "ProductID", "SecurityType",
                                                "SecurityID", "BusinessClass", "BrokerageType", "RatioByAmt",
                                                "RatioByPar", "FeePerOrder", "FeeMin", "FeeMax", "FeeByVolume"),
                                       sql="""SELECT "0001" AS DepartmentID,"00000000" as InvestorID,"1" AS ExchangeID,
                                                        "d" AS ProductID,"0" AS SecurityType,"00000000" AS SecurityID,
                                                        "A" AS BusinessClass,"0" AS BrokerageType,"0" AS RatioByAmt,
                                                        "0" AS RatioByPar,"0" AS FeePerOrder,t2.MinOpenFee AS FeeMin,
                                                        t2.MaxOpenFee AS FeeMax,t2.CloseYesterdayFeeRatio AS FeeByVolume
                                                        FROM siminfo.t_transfeeratedetail t2
                                                        WHERE t2.SettlementGroupID = %s
                                                UNION ALL 
                                                SELECT "0001" AS DepartmentID,"00000000" as InvestorID,"1" AS ExchangeID,
                                                    "d" AS ProductID,"0" AS SecurityType,"00000000" AS SecurityID,
                                                    "B" AS BusinessClass,"0" AS BrokerageType,"0" AS RatioByAmt,
                                                    "0" AS RatioByPar,"0" AS FeePerOrder,t2.MinOpenFee AS FeeMin,
                                                    t2.MaxOpenFee AS FeeMax,t2.CloseYesterdayFeeRatio AS FeeByVolume
                                                    FROM siminfo.t_transfeeratedetail t2
                                                    WHERE t2.SettlementGroupID = %s
                                                UNION ALL 
                                                SELECT "0001" AS DepartmentID,"00000000" as InvestorID,"1" AS ExchangeID,
                                                    "d" AS ProductID,"0" AS SecurityType,"00000000" AS SecurityID,
                                                    "C" AS BusinessClass,"0" AS BrokerageType,"0" AS RatioByAmt,
                                                    "0" AS RatioByPar,"0" AS FeePerOrder,t2.MinOpenFee AS FeeMin,
                                                    t2.MaxOpenFee AS FeeMax,t2.CloseYesterdayFeeRatio AS FeeByVolume
                                                    FROM siminfo.t_transfeeratedetail t2
                                                    WHERE t2.SettlementGroupID = %s
                                                UNION ALL 
                                                SELECT "0001" AS DepartmentID,"00000000" as InvestorID,"1" AS ExchangeID,
                                                    "d" AS ProductID,"0" AS SecurityType,"00000000" AS SecurityID,
                                                    "D" AS BusinessClass,"0" AS BrokerageType,"0" AS RatioByAmt,
                                                    "0" AS RatioByPar,"0" AS FeePerOrder,t2.MinOpenFee AS FeeMin,
                                                    t2.MaxOpenFee AS FeeMax,t2.CloseYesterdayFeeRatio AS FeeByVolume
                                                    FROM siminfo.t_transfeeratedetail t2
                                                    WHERE t2.SettlementGroupID = %s
                                                UNION ALL 
                                                SELECT "0001" AS DepartmentID,"00000000" as InvestorID,"1" AS ExchangeID,
                                                    "d" AS ProductID,"0" AS SecurityType,"00000000" AS SecurityID,
                                                    "E" AS BusinessClass,"0" AS BrokerageType,"0" AS RatioByAmt,
                                                    "0" AS RatioByPar,"0" AS FeePerOrder,t2.MinOpenFee AS FeeMin,
                                                    t2.MaxOpenFee AS FeeMax,t2.CloseYesterdayFeeRatio AS FeeByVolume
                                                    FROM siminfo.t_transfeeratedetail t2
                                                    WHERE t2.SettlementGroupID = %s
                                                UNION ALL 
                                                SELECT "0001" AS DepartmentID,"00000000" as InvestorID,"1" AS ExchangeID,
                                                    "d" AS ProductID,"0" AS SecurityType,"00000000" AS SecurityID,
                                                    "F" AS BusinessClass,"0" AS BrokerageType,"0" AS RatioByAmt,
                                                    "0" AS RatioByPar,"0" AS FeePerOrder,t2.MinOpenFee AS FeeMin,
                                                    t2.MaxOpenFee AS FeeMax,t2.CloseYesterdayFeeRatio AS FeeByVolume
                                                    FROM siminfo.t_transfeeratedetail t2
                                                    WHERE t2.SettlementGroupID = %s
                                                UNION ALL 
                                                SELECT "0001" AS DepartmentID,"00000000" as InvestorID,"1" AS ExchangeID,
                                                    "d" AS ProductID,"0" AS SecurityType,"00000000" AS SecurityID,
                                                    "G" AS BusinessClass,"0" AS BrokerageType,"0" AS RatioByAmt,
                                                    "0" AS RatioByPar,"0" AS FeePerOrder,t2.MinOpenFee AS FeeMin,
                                                    t2.MaxOpenFee AS FeeMax,t2.CloseYesterdayFeeRatio AS FeeByVolume
                                                    FROM siminfo.t_transfeeratedetail t2
                                                    WHERE t2.SettlementGroupID = %s""",
                                       params=(self.settlementGroupID, self.settlementGroupID, self.settlementGroupID,
                                               self.settlementGroupID, self.settlementGroupID, self.settlementGroupID,
                                               self.settlementGroupID,)),
            InvestorCondOrderLimitParam=dict(columns=("InvestorID", "MaxCondOrderLimitCnt", "CurrCondOrderCnt"),
                                             sql="""select InvestorID, '100' as MaxCondOrderLimitCnt, 
                                                    '0' as CurrCondOrderCnt from siminfo.t_investor""")
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
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql", "log", "csv"])
    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)
    # 启动脚本
    broker_etf_csv(context=context, configs=conf)
