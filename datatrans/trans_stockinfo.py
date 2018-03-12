# -*- coding: UTF-8 -*-

import os
import datetime
import json
import csv
import copy

from itertools import islice
from utils import parse_conf_args
from utils import Configuration
from utils import path
from utils import mysql
from utils import log
from dbfread import DBF


class trans_stockinfo:
    def __init__(self, context, configs):
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="trans_stock", configs=log_conf)
        if log_conf is None:
            self.logger.warning("trans_stock未配置Log日志")
        # 初始化数据库连接
        self.mysqlDB = mysql(configs=context.get("mysql")[configs.get("mysqlId")])
        # 初始化模板路径
        self.initTemplate = context.get("init")[configs.get("initId")]
        self.stock_filename = "PAR_STOCK"
        self.qy_info_filename = "PAR_QY_INFO"
        self.stock_market = "stock_exp"
        # 结算组ID和交易所对应关系
        self.self_conf = {
            "1": "SG01",
            "2": "SG02",
            "3": "SG99",
            "4": "SG98"
        }
        self.__transform()

    def __transform(self):
        # 读取dbf文件
        dbfs = self.__check_file()
        if dbfs is None:
            return
        mysqlDB = self.mysqlDB
        if dbfs[0] is not None:
            # ===========处理stock_dbf写入t_Instrument表==============
            self.__t_Instrument(mysqlDB=mysqlDB, dbf=dbfs[0])

            # ===========处理stock_dbf写入t_TradingSegmentAttr表==============
            self.__t_TradingSegmentAttr(mysqlDB=mysqlDB, dbf=dbfs[0])

            # ===========处理stock_dbf写入t_MarginRate表==============
            self.__t_MarginRate(mysqlDB=mysqlDB, dbf=dbfs[0])

            # ===========处理stock_dbf写入t_MarginRateDetail表==============
            self.__t_MarginRateDetail(mysqlDB=mysqlDB, dbf=dbfs[0])

            # ===========处理stock_dbf写入t_PriceBanding表==============
            self.__t_PriceBanding(mysqlDB=mysqlDB, dbf=dbfs[0])

            # ===========判断并写入t_InstrumentProperty表==============
            self.__t_InstrumentProperty(mysqlDB=mysqlDB, dbf=dbfs[0])

        if dbfs[1] is not None:
            # ===========处理info_dbf写入t_SecurityProfit表===========
            self.__t_SecurityProfit(mysqlDB=mysqlDB, dbf=dbfs[1])

        if dbfs[2] is not None:
            # ===========处理stock_exp写入t_MarketData表 ==============
            self.__t_MarketData(mysqlDB=mysqlDB, market=dbfs[2])

    # 读取处理PAR_STOCK文件
    def __t_Instrument(self, mysqlDB, dbf):
        sql_insert_Instrument = """INSERT INTO siminfo.t_Instrument (
                                   SettlementGroupID,ProductID,
                                   ProductGroupID,UnderlyingInstrID,
                                   ProductClass,PositionType,
                                   StrikePrice,OptionsType,
                                   VolumeMultiple,UnderlyingMultiple,
                                   TotalEquity,CirculationEquity,
                                   InstrumentID,InstrumentName,
                                   DeliveryYear,DeliveryMonth,AdvanceMonth
                               )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
                               ON DUPLICATE KEY UPDATE 
                               InstrumentName=VALUES(InstrumentName),
                               TotalEquity=VALUES(TotalEquity),
                               CirculationEquity=VALUES(CirculationEquity)"""
        sql_insert_params = []
        for stock in dbf:
            # 判断市场代码，如果没有跳过本次循环
            if str(stock['SCDM']) == '1':
                ProductID = 'ZQ_SH'
                ProductGroupID = 'ZQ'
                pass
            elif str(stock['SCDM']) == '2':
                ProductID = 'ZQ_SZ'
                ProductGroupID = 'ZQ'
            else:
                continue
            sql_insert_params.append((self.self_conf[str(stock['SCDM'])],
                                      ProductID,
                                      ProductGroupID,
                                      ProductID,
                                      "4", "2", None, "0",
                                      1, 1, stock['ZGB'], stock['LTGB'],
                                      stock['ZQDM'], stock['ZQJC'],
                                      2099, 12, "012"))
        mysqlDB.executemany(sql_insert_Instrument, sql_insert_params)
        self.logger.info("写入t_Instrument完成")

    # 读取处理PAR_QY_INFO文件
    def __t_SecurityProfit(self, mysqlDB, dbf):
        sql_insert_qy_info = """INSERT INTO siminfo.t_SecurityProfit (
                                   SettlementGroupID,SecurityID,
                                   SecurityType,SecurityMarketID,
                                   ProfitType,DJDate,
                                   CQDate,EndDate,
                                   DZDate,BeforeRate,
                                   AfterRate,Price
                               )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                              ON DUPLICATE KEY UPDATE 
                                  DJDate=VALUES(DJDate),CQDate=VALUES(CQDate),EndDate=VALUES(EndDate),
                                  DZDate=VALUES(DZDate),BeforeRate=VALUES(BeforeRate),
                                  AfterRate=VALUES(AfterRate),Price=VALUES(Price)"""
        sql_insert_params = []
        for info in dbf:
            sql_insert_params.append((self.self_conf[str(info['SCDM'])], info['ZQDM'],
                                      info['ZQLX'], info['SCDM'], info['QYKIND'],
                                      info['DJDATE'], info['CQDATE'], info['ENDDATE'],
                                      info['DZDATE'], info['BEFORERATE'],
                                      info['AFTERRATE'], info['PRICE']))
        mysqlDB.executemany(sql_insert_qy_info, sql_insert_params)
        self.logger.info("写入t_SecurityProfit完成")

    # 写入t_InstrumentProperty
    def __t_InstrumentProperty(self, mysqlDB, dbf):
        sql_Property = """INSERT INTO siminfo.t_InstrumentProperty (
                                      SettlementGroupID,CreateDate,OpenDate,ExpireDate,StartDelivDate,
                                      EndDelivDate,BasisPrice,MaxMarketOrderVolume,MinMarketOrderVolume,
                                      MaxLimitOrderVolume,MinLimitOrderVolume,PriceTick,
                                      AllowDelivPersonOpen,InstrumentID,InstLifePhase
                                      )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)  
                                    ON DUPLICATE KEY UPDATE 
                                      CreateDate=VALUES(CreateDate),OpenDate=VALUES(OpenDate)"""
        sql_params = []
        for stock in dbf:
            sql_params.append((self.self_conf[str(stock['SCDM'])], stock['FXRQ'], stock['SSRQ'],
                               '99991219', '99991219', '99991219', 0, 1000000, 100,
                               1000000, 100, 0.01, 0, stock['ZQDM'], 1))
        mysqlDB.executemany(sql_Property, sql_params)
        self.logger.info("写入t_InstrumentProperty完成")

    # 写入t_TradingSegmentAttr
    def __t_TradingSegmentAttr(self, mysqlDB, dbf):
        # 判断合约是否已存在
        sql_insert_segment = """INSERT INTO siminfo.t_TradingSegmentAttr(SettlementGroupID,TradingSegmentSN,
                                            TradingSegmentName,StartTime,InstrumentStatus,DayOffset,InstrumentID)
                                VALUES(%s,%s,%s,%s,%s,%s,%s) 
                                ON DUPLICATE KEY UPDATE 
                                InstrumentStatus=VALUES(InstrumentStatus),
                                StartTime=VALUES(StartTime),
                                InstrumentStatus=VALUES(InstrumentStatus),
                                DayOffset=VALUES(DayOffset)"""
        sql_insert_params = []
        SegmentAttr = self.__loadJSON(tableName='t_TradingSegmentAttr')
        if SegmentAttr is None:
            return
        for stock in dbf:
            SGID = self.self_conf[str(stock['SCDM'])]
            # 插入记录
            if SGID in SegmentAttr:
                for attr in SegmentAttr[SGID]:
                    sql_insert_params.append((
                        SGID, attr[1], attr[2], attr[3], attr[4], '0', stock['ZQDM']))
        mysqlDB.executemany(sql_insert_segment, sql_insert_params)
        self.logger.info("写入t_TradingSegmentAttr完成")

    # 写入t_MarginRate
    def __t_MarginRate(self, mysqlDB, dbf):
        # 获取模板文件
        template = self.__loadJSON(tableName='t_MarginRate')
        if template is None:
            self.logger.error("t_MarginRate template is None")
            return
        sql_insert_rate = """INSERT INTO t_MarginRate (
                                SettlementGroupID,
                                MarginCalcID,
                                InstrumentID,
                                ParticipantID
                            ) VALUES (%s,%s,%s,%s) 
                        ON DUPLICATE KEY UPDATE MarginCalcID=VALUES(MarginCalcID),ParticipantID=VALUES(ParticipantID)"""
        sql_insert_params = []
        for stock in dbf:
            SGID = self.self_conf[str(stock['SCDM'])]
            sql_insert_params.append((SGID, template[SGID][1], stock['ZQDM'], template[SGID][3]))
        mysqlDB.executemany(sql_insert_rate, sql_insert_params)
        self.logger.info("写入t_MarginRate完成")

    # 写入t_MarginRateDetail
    def __t_MarginRateDetail(self, mysqlDB, dbf):
        # 获取模板文件
        template = self.__loadJSON(tableName='t_MarginRateDetail')
        if template is None:
            self.logger.error("t_MarginRateDetail template is None")
            return
        sql_insert_detail = """INSERT INTO siminfo.t_MarginRateDetail (
                                SettlementGroupID,TradingRole,HedgeFlag,
                                ValueMode,LongMarginRatio,ShortMarginRatio,
                                InstrumentID,ParticipantID,ClientID
                            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                             ON DUPLICATE KEY UPDATE 
                             ValueMode=VALUES(ValueMode),LongMarginRatio=VALUES(LongMarginRatio),
                             ShortMarginRatio=VALUES(ShortMarginRatio)"""
        sql_insert_params = []
        for stock in dbf:
            SGID = self.self_conf[str(stock['SCDM'])]
            sql_insert_params.append((SGID, template[SGID][1], template[SGID][2], template[SGID][3],
                                      template[SGID][4], template[SGID][5], stock['ZQDM'],
                                      template[SGID][9], template[SGID][10]))

        mysqlDB.executemany(sql_insert_detail, sql_insert_params)
        self.logger.info("写入t_MarginRateDetail完成")

    # 写入t_PriceBanding
    def __t_PriceBanding(self, mysqlDB, dbf):
        # 获取模板文件
        template = self.__loadJSON(tableName='t_PriceBanding')
        if template is None:
            self.logger.error("t_PriceBanding template is None")
            return
        sql_insert_price = """INSERT INTO siminfo.t_PriceBanding (
                                SettlementGroupID,PriceLimitType,ValueMode,RoundingMode,
                                UpperValue,LowerValue,InstrumentID,TradingSegmentSN
                            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) 
                             ON DUPLICATE KEY UPDATE 
                             PriceLimitType=VALUES(PriceLimitType),ValueMode=VALUES(ValueMode),
                             RoundingMode=VALUES(RoundingMode),UpperValue=VALUES(UpperValue),LowerValue=VALUES(LowerValue)"""
        sql_insert_params = []
        for stock in dbf:
            SGID = self.self_conf[str(stock['SCDM'])]
            sql_insert_params.append((SGID, template[SGID][1], template[SGID][2], template[SGID][3],
                                      template[SGID][4], template[SGID][5], stock['ZQDM'], template[SGID][7]))
        mysqlDB.executemany(sql_insert_price, sql_insert_params)
        self.logger.info("写入t_PriceBanding完成")

    # 写入t_MarketData
    def __t_MarketData(self, mysqlDB, market):
        sql_insert_market = """INSERT INTO siminfo.t_MarketData (
                                                TradingDay,SettlementGroupID,LastPrice,PreSettlementPrice,
                                                PreClosePrice,UnderlyingClosePx,PreOpenInterest,OpenPrice,
                                                HighestPrice,LowestPrice,Volume,Turnover,
                                                OpenInterest,ClosePrice,SettlementPrice,
                                                UpperLimitPrice,LowerLimitPrice,PreDelta,
                                                CurrDelta,UpdateTime,UpdateMillisec,InstrumentID
                                           )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                              ON DUPLICATE KEY UPDATE PreSettlementPrice = VALUES(PreSettlementPrice),
                                                PreClosePrice = VALUES(PreClosePrice),
                                                UpdateTime = VALUES(UpdateTime),
                                                UpdateMillisec = VALUES(UpdateMillisec)"""
        sql_insert_params = []
        for stock in islice(market, 1, None):
            sql_insert_params.append((self.TradingDay, stock[8], None, stock[5],
                                      stock[5], None, '0', None,
                                      None, None, None, None,
                                      None, None, None,
                                      None, None, None,
                                      None, "08:30:00", "-1", stock[0]))
        mysqlDB.executemany(sql_insert_market, sql_insert_params)
        self.logger.info("写入t_MarketData完成")

    def __check_file(self):
        env_dist = os.environ
        # 判断环境变量是否存在HOME配置
        if 'HOME' not in env_dist:
            self.logger.error("HOME not in environment variable")
            return None
        # 获取文件路径
        catalog = env_dist['HOME']
        now = datetime.datetime.now().strftime("%Y%m%d")
        self.TradingDay = now
        catalog = '%s%s%s%s%s' % (catalog, os.path.sep, 'sim_data', os.path.sep, now)
        par_stock = '%s%s%s%s%s' % (catalog, os.path.sep, self.stock_filename, now, '.dbf')
        par_qy_info = '%s%s%s%s%s' % (catalog, os.path.sep, self.qy_info_filename, now, '.dbf')
        par_stock_market = '%s%s%s%s%s' % (catalog, os.path.sep, self.stock_market, now, '.csv')

        # 判断PAR_STOCKYYYYMMDD.dbf文件是否存在，不存在设置为空
        if not os.path.exists(par_stock):
            self.logger.error("%s%s" % (par_stock, " is not exists"))
            par_stock = None
        # 判断PAR_QY_INFOYYYYMMDD.dbf文件是否存在，不存在设置为空
        if not os.path.exists(par_qy_info):
            self.logger.error("%s%s" % (par_qy_info, " is not exists"))
            par_qy_info = None
        # 判断stock_exp.csv文件是否存在，不存在设置为空
        if not os.path.exists(par_stock_market):
            self.logger.error("%s%s" % (par_stock_market, " is not exists"))
            par_stock_market = None
        # 读取DBF文件和CSV文件
        _dbf = self.__loadDBF(stock=par_stock, info=par_qy_info)
        _csv = self.__loadCSV(market=par_stock_market)
        return _dbf[0], _dbf[1], _csv

    def __loadCSV(self, market):
        # 加载 par_stock_market 数据
        if market is not None:
            csv_file = csv.reader(open(market))
            return csv_file
        else:
            return None

    def __loadDBF(self, **par):
        dbf_1 = None
        dbf_2 = None
        # 加载 PAR_STOCK 数据
        if par['stock'] is not None:
            stock = DBF(filename=par['stock'], encoding='GBK')
            stock.load()
            dbf_1 = stock.records
        # 加载 PAR_QY_INFO 数据
        if par['info'] is not None:
            info = DBF(filename=par['info'], encoding='GBK')
            info.load()
            dbf_2 = info.records
        return dbf_1, dbf_2

    # 主要读取template数据
    def __loadJSON(self, tableName):
        _output = path.convert(self.initTemplate['initTemplate'])
        _path = "%s%s%s%s" % (_output, os.path.sep, tableName, ".json")
        if not os.path.exists(_path):
            self.logger.error("文件" + tableName + ".json不存在")
            return None
        f = open(_path)
        return json.load(f)


if __name__ == '__main__':
    base_dir, config_names, config_files = parse_conf_args(__file__, config_names=["mysql", "log", "init"])
    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)
    # 启动stock脚本
    trans_stockinfo(context=context, configs=conf)
