# -*- coding: UTF-8 -*-

import os
import datetime
import json

from utils import log
from utils import parse_conf_args
from utils import path
from utils import Configuration
from utils import mysql
from etf_entity import etfVO


class trans_etfinfo:
    def __init__(self, context, configs):
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="trans_etfinfo", configs=log_conf)
        if log_conf is None:
            self.logger.warning("trans_etfinfo未配置Log日志")
        # 初始化数据库连接
        self.mysqlDB = mysql(configs=context.get("mysql")[configs.get("mysqlId")])
        # 初始化模板路径
        self.initTemplate = context.get("init")[configs.get("initId")]
        self.etf_filename = "reff03"
        self.SettlementGroupID = "SG07"
        self.__transform()

    def __transform(self):
        etf_list = self.__check_file()
        if etf_list is None:
            return

        mysqlDB = self.mysqlDB
        # ===========处理etf_txt写入t_Instrument表==============
        self.__t_Instrument(mysqlDB=mysqlDB, etf_list=etf_list)

        # ===========判断并写入t_InstrumentProperty表==============
        self.__t_InstrumentProperty(mysqlDB=mysqlDB, etf_list=etf_list)

        # ===========处理etf_txt写入t_MarginRate表==============
        self.__t_MarginRate(mysqlDB=mysqlDB, etf_list=etf_list)

        # ===========处理etf_txt写入t_MarginRateDetail表==============
        self.__t_MarginRateDetail(mysqlDB=mysqlDB, etf_list=etf_list)

        # ===========处理etf_txt写入t_PriceBanding表==============
        self.__t_PriceBanding(mysqlDB=mysqlDB, etf_list=etf_list)

        # ===========处理etf_txt写入t_MarketData表==============
        self.__t_MarketData(mysqlDB=mysqlDB, etf_list=etf_list)

        # ===========处理etf_txt写入t_TradingSegmentAttr表==============
        self.__t_TradingSegmentAttr(mysqlDB=mysqlDB, etf_list=etf_list)

    # 读取处理reff03文件
    def __t_Instrument(self, mysqlDB, etf_list):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_Instrument where SettlementGroupID = %s", (self.SettlementGroupID,))
            sql_insert_etf = """INSERT INTO siminfo.t_Instrument (
                                   SettlementGroupID,ProductID,
                                   ProductGroupID,UnderlyingInstrID,
                                   ProductClass,PositionType,
                                   UnderlyingType,StrikeType,
                                   StrikePrice,OptionsType,
                                   VolumeMultiple,UnderlyingMultiple,
                                   InstrumentID,ExchInstrumentID,InstrumentName,
                                   DeliveryYear,DeliveryMonth,AdvanceMonth
                              )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                              ON DUPLICATE KEY UPDATE 
                                InstrumentName=VALUES(InstrumentName),StrikePrice=VALUES(StrikePrice),
                                DeliveryYear=VALUES(DeliveryYear),DeliveryMonth=VALUES(DeliveryMonth),
                                OptionsType=VALUES(OptionsType),UnderlyingType=VALUES(UnderlyingType),
                                StrikeType=VALUES(StrikeType)"""
            sql_insert_params = []
            for etf in etf_list:
                ProductID = 'ETF'
                ProductGroupID = 'ZQ'
                # 判断认购认沽
                if str(etf.CallOrPut) == 'C':
                    OptionsType = '1'
                elif str(etf.CallOrPut) == 'P':
                    OptionsType = '2'
                # 判断欧式美式
                if str(etf.OptionType) == 'E':
                    StrikeType = '1'
                elif str(etf.OptionType) == 'A':
                    StrikeType = '2'
                # 判断ETF还是股票
                if str(etf.UnderlyingType) == 'EBS':
                    UnderlyingType = '1'
                elif str(etf.UnderlyingType) == 'ASH':
                    UnderlyingType = '2'
                sql_insert_params.append((self.SettlementGroupID, ProductID,
                                          ProductGroupID, etf.UnderlyingSecurityID,
                                          "2", "2", UnderlyingType, StrikeType, etf.ExercisePrice, OptionsType,
                                          1, 10000, etf.SecurityID, etf.ContractID, etf.ContractSymbol,
                                          etf.DeliveryDate[0:4], etf.DeliveryDate[4:6], "012"))
            cursor.executemany(sql_insert_etf, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_Instrument完成")

    # 写入t_InstrumentProperty
    def __t_InstrumentProperty(self, mysqlDB, etf_list):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_InstrumentProperty where SettlementGroupID = %s", (self.SettlementGroupID,))
            sql_Property = """INSERT INTO siminfo.t_InstrumentProperty (
                                          SettlementGroupID,CreateDate,OpenDate,ExpireDate,StartDelivDate,
                                          EndDelivDate,StrikeDate,BasisPrice,MaxMarketOrderVolume,MinMarketOrderVolume,
                                          MaxLimitOrderVolume,MinLimitOrderVolume,PriceTick,
                                          AllowDelivPersonOpen,InstrumentID,InstLifePhase
                                          )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                        ON DUPLICATE KEY UPDATE 
                                        OpenDate=VALUES(OpenDate),
                                        ExpireDate=VALUES(ExpireDate),
                                        StartDelivDate=VALUES(StartDelivDate),
                                        EndDelivDate=VALUES(EndDelivDate),
                                        StrikeDate=VALUES(StrikeDate),
                                        MaxMarketOrderVolume=VALUES(MaxMarketOrderVolume),
                                        MinMarketOrderVolume=VALUES(MinMarketOrderVolume),
                                        MaxLimitOrderVolume=VALUES(MaxLimitOrderVolume),
                                        MinLimitOrderVolume=VALUES(MinLimitOrderVolume),
                                        PriceTick=VALUES(PriceTick)"""
            sql_params = []
            for etf in etf_list:
                sql_params.append((self.SettlementGroupID, '99991219', etf.StartDate, etf.ExpireDate, etf.DeliveryDate,
                                   etf.DeliveryDate, etf.ExerciseDate, 0, etf.MktOrdMaxFloor, etf.MktOrdMinFloor,
                                   etf.LmtOrdMaxFloor, etf.LmtOrdMinFloor, etf.TickSize,
                                   0, etf.SecurityID, 1))
            cursor.executemany(sql_Property, sql_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_InstrumentProperty完成")

    # 写入t_MarginRate
    def __t_MarginRate(self, mysqlDB, etf_list):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_MarginRate where SettlementGroupID = %s", (self.SettlementGroupID,))
            # 获取模板文件
            template = self.__loadJSON(tableName='t_MarginRate')
            if template is None:
                self.logger.error("t_MarginRate template is None")
                return
            sql_insert_rate = """INSERT INTO siminfo.t_MarginRate (
                                            SettlementGroupID,
                                            MarginCalcID,
                                            InstrumentID,
                                            ParticipantID
                                        ) VALUES (%s,%s,%s,%s)
                                     ON DUPLICATE KEY UPDATE 
                                        MarginCalcID=VALUES(MarginCalcID),
                                        ParticipantID=VALUES(ParticipantID)"""
            sql_insert_params = []
            for etf in etf_list:
                SGID = self.SettlementGroupID
                sql_insert_params.append((SGID, template[SGID][1], etf.SecurityID, template[SGID][3]))
            cursor.executemany(sql_insert_rate, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_MarginRate完成")

    # 写入t_MarginRateDetail
    def __t_MarginRateDetail(self, mysqlDB, etf_list):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_MarginRateDetail where SettlementGroupID = %s", (self.SettlementGroupID,))
            # 获取模板文件
            template = self.__loadJSON(tableName='t_MarginRateDetail')
            if template is None:
                self.logger.error("t_MarginRateDetail template is None")
                return
            # 不存在插入记录
            sql_insert_detail = """INSERT INTO siminfo.t_MarginRateDetail (
                                          SettlementGroupID,TradingRole,HedgeFlag,
                                          ValueMode,LongMarginRatio,ShortMarginRatio,AdjustRatio1,AdjustRatio2,
                                          InstrumentID,ParticipantID,ClientID
                                      ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                    ON DUPLICATE KEY UPDATE 
                                    ValueMode=VALUES(ValueMode),LongMarginRatio=VALUES(LongMarginRatio),
                                    ShortMarginRatio=VALUES(ShortMarginRatio),AdjustRatio1=VALUES(AdjustRatio1),
                                    AdjustRatio2=VALUES(AdjustRatio2)"""
            sql_insert_params = []
            for etf in etf_list:
                SGID = self.SettlementGroupID
                # 插入记录
                sql_insert_params.append((SGID, template[SGID][1], template[SGID][2], template[SGID][3],
                                          template[SGID][4], etf.MarginUnit, etf.MarginRatioParam1,
                                          etf.MarginRatioParam2, etf.SecurityID, template[SGID][9], template[SGID][10]))
            cursor.executemany(sql_insert_detail, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_MarginRateDetail完成")

    # 写入t_PriceBanding
    def __t_PriceBanding(self, mysqlDB, etf_list):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_PriceBanding where SettlementGroupID = %s", (self.SettlementGroupID,))
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
                                        RoundingMode=VALUES(RoundingMode),UpperValue=VALUES(UpperValue),
                                        LowerValue=VALUES(LowerValue)"""
            sql_insert_params = []
            for etf in etf_list:
                SGID = self.SettlementGroupID
                sql_insert_params.append((SGID, template[SGID][1], template[SGID][2], template[SGID][3],
                                          template[SGID][4], template[SGID][5], etf.SecurityID,
                                          template[SGID][7]))
            cursor.executemany(sql_insert_price, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_PriceBanding完成")

    # 写入t_MarketData
    def __t_MarketData(self, mysqlDB, etf_list):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_MarketData where SettlementGroupID = %s", (self.SettlementGroupID,))
            sql_insert_market = """INSERT INTO siminfo.t_MarketData (
                                            TradingDay,SettlementGroupID,LastPrice,PreSettlementPrice,
                                            PreClosePrice,UnderlyingClosePx,PreOpenInterest,OpenPrice,
                                            HighestPrice,LowestPrice,Volume,Turnover,
                                            OpenInterest,ClosePrice,SettlementPrice,
                                            UpperLimitPrice,LowerLimitPrice,PreDelta,
                                            CurrDelta,UpdateTime,UpdateMillisec,InstrumentID
                                       )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                    ON DUPLICATE KEY UPDATE  
                                        PreSettlementPrice = VALUES(PreSettlementPrice),
                                        PreClosePrice = VALUES(PreClosePrice),
                                        UnderlyingClosePx=VALUES(UnderlyingClosePx),
                                        UpperLimitPrice = VALUES(UpperLimitPrice),
                                        LowerLimitPrice = VALUES(LowerLimitPrice)"""
            sql_insert_params = []
            for etf in etf_list:
                sql_insert_params.append((self.TradingDay, self.SettlementGroupID, None, etf.SettlePrice,
                                          etf.SecurityClosePx, etf.UnderlyingClosePx, '0', None,
                                          None, None, None, None,
                                          None, None, None,
                                          etf.DailyPriceUpLimit, etf.DailyPriceDownLimit, None,
                                          None, None, None, etf.SecurityID))
            cursor.executemany(sql_insert_market, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_MarketData完成")

    # 读取处理reff03文件
    def __t_TradingSegmentAttr(self, mysqlDB, etf_list):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_TradingSegmentAttr where SettlementGroupID = %s", (self.SettlementGroupID,))
            sql_insert_segment = """INSERT INTO siminfo.t_TradingSegmentAttr (
                                                    SettlementGroupID,TradingSegmentSN,
                                                    TradingSegmentName,StartTime,
                                                    InstrumentStatus,InstrumentID
                                                ) VALUES (%s,%s,%s,%s,%s,%s)
                                                ON DUPLICATE KEY UPDATE  
                                                    TradingSegmentName=VALUES(TradingSegmentName),
                                                    StartTime=VALUES(StartTime),InstrumentStatus=VALUES(InstrumentStatus)"""
            # 存在更新记录
            sql_insert_params = []
            SegmentAttr = self.__loadJSON(tableName='t_TradingSegmentAttr')
            if SegmentAttr is None:
                return
            for etf in etf_list:
                SGID = self.SettlementGroupID
                # 插入记录
                if SGID in SegmentAttr:
                    for attr in SegmentAttr[SGID]:
                        sql_insert_params.append((SGID, attr[1], attr[2], attr[3], attr[4], etf.SecurityID))
            cursor.executemany(sql_insert_segment, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_TradingSegmentAttr完成")

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
        etf = '%s%s%s%s%s' % (catalog, os.path.sep, self.etf_filename, now[4:8], '.txt')
        # 判断reff03MMDD.txt文件是否存在
        if not os.path.exists(etf):
            self.logger.error("%s%s" % (etf, " is not exists"))
            return None
        # 读取txt文件
        etf_file = open(etf)
        return self.__txt_to_etf(etf_file)

    def __txt_to_etf(self, txt):
        etf_list = []
        for lines in txt:
            VO = etfVO(lines.split("|"))
            etf_list.append(VO)
        return etf_list

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
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql", "log", "init"])
    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)
    # 启动etf脚本
    trans_etfinfo(context=context, configs=conf)
