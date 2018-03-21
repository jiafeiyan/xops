# -*- coding: UTF-8 -*-

import os
import datetime
import json
import codecs

from utils import parse_conf_args, Configuration, path, mysql, log
from stock_entity import stockVO


class trans_stockinfo_txt:
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
        # 上证文件
        self.stock_filename = {
            "cpxx": "SG01"
        }
        self.__transform()

    def __transform(self):
        # 读取txt文件(‘ES’表示股票；‘EU’表示基金；‘D’表示债券； ‘RWS’表示权证；‘FF’表示期货。（参考ISO10962），集合资产管理计划、债券预发行取‘D’)
        stock_list = self.__check_file("ES")
        if stock_list is None:
            return
        mysqlDB = self.mysqlDB
        for settlement_group in stock_list:
            stock_data = stock_list[settlement_group]
            # ===========处理stock_dbf写入t_Instrument表==============
            self.__t_Instrument(mysqlDB=mysqlDB, settlement_group=settlement_group, stock_data=stock_data)

            # ===========处理stock_dbf写入t_TradingSegmentAttr表==============
            self.__t_TradingSegmentAttr(mysqlDB=mysqlDB, settlement_group=settlement_group, stock_data=stock_data)

            # ===========处理stock_dbf写入t_MarginRate表==============
            self.__t_MarginRate(mysqlDB=mysqlDB, settlement_group=settlement_group, stock_data=stock_data)

            # ===========处理stock_dbf写入t_MarginRateDetail表==============
            self.__t_MarginRateDetail(mysqlDB=mysqlDB, settlement_group=settlement_group, stock_data=stock_data)

            # ===========处理stock_dbf写入t_PriceBanding表==============
            self.__t_PriceBanding(mysqlDB=mysqlDB, settlement_group=settlement_group, stock_data=stock_data)

            # ===========写入t_InstrumentProperty表==============
            self.__t_InstrumentProperty(mysqlDB=mysqlDB, settlement_group=settlement_group, stock_data=stock_data)

            # ===========写入t_MarketData表==============
            self.__t_MarketData(mysqlDB=mysqlDB, settlement_group=settlement_group, stock_data=stock_data)

    def __t_Instrument(self, mysqlDB, settlement_group, stock_data):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            sql_insert_instrument = """INSERT INTO siminfo.t_Instrument (
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
            if settlement_group == 'SG01':
                ProductID = 'ZQ_SH'
                ProductGroupID = 'ZQ'
            for stock in stock_data:
                sql_insert_params.append((settlement_group,
                                          ProductID,
                                          ProductGroupID,
                                          ProductID,
                                          "4", "2", None, "0",
                                          1, 1, 123, 123,
                                          stock.ZQDM, stock.ZWMC,
                                          2099, 12, "012"))
            cursor.executemany(sql_insert_instrument, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_Instrument完成")

    def __t_TradingSegmentAttr(self, mysqlDB, settlement_group, stock_data):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            # 加载模版文件
            SegmentAttr = self.__loadJSON(tableName='t_TradingSegmentAttr')
            if SegmentAttr is None or settlement_group not in SegmentAttr:
                self.logger.error("SegmentAttr is None or settlement_group not in SegmentAttr")
                return
            sql_insert_segment = """INSERT INTO siminfo.t_TradingSegmentAttr(SettlementGroupID,TradingSegmentSN,
                                            TradingSegmentName,StartTime,InstrumentStatus,DayOffset,InstrumentID)
                                VALUES(%s,%s,%s,%s,%s,%s,%s) 
                                ON DUPLICATE KEY UPDATE 
                                InstrumentStatus=VALUES(InstrumentStatus),
                                StartTime=VALUES(StartTime),
                                InstrumentStatus=VALUES(InstrumentStatus),
                                DayOffset=VALUES(DayOffset)"""
            sql_insert_params = []
            for stock in stock_data:
                for attr in SegmentAttr[settlement_group]:
                    sql_insert_params.append((settlement_group, attr[1], attr[2], attr[3], attr[4], '0', stock.ZQDM))
            cursor.executemany(sql_insert_segment, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_TradingSegmentAttr完成")

    def __t_MarginRate(self, mysqlDB, settlement_group, stock_data):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
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
            for stock in stock_data:
                sql_insert_params.append((settlement_group, template[settlement_group][1], stock.ZQDM, template[settlement_group][3]))
            cursor.executemany(sql_insert_rate, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_MarginRate完成")

    def __t_MarginRateDetail(self, mysqlDB, settlement_group, stock_data):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
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
            for stock in stock_data:
                sql_insert_params.append((settlement_group, template[settlement_group][1],
                                          template[settlement_group][2], template[settlement_group][3],
                                          template[settlement_group][4], template[settlement_group][5],
                                          stock.ZQDM, template[settlement_group][9], template[settlement_group][10]))
            cursor.executemany(sql_insert_detail, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_MarginRateDetail完成")

    def __t_PriceBanding(self, mysqlDB, settlement_group, stock_data):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
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
            for stock in stock_data:
                sql_insert_params.append((settlement_group, template[settlement_group][1],
                                      template[settlement_group][2], template[settlement_group][3],
                                      template[settlement_group][4], template[settlement_group][5],
                                      stock.ZQDM, template[settlement_group][7]))
            cursor.executemany(sql_insert_price, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_PriceBanding完成")

    def __t_InstrumentProperty(self, mysqlDB, settlement_group, stock_data):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            sql_Property = """INSERT INTO siminfo.t_InstrumentProperty (
                                 SettlementGroupID,CreateDate,OpenDate,ExpireDate,StartDelivDate,
                                 EndDelivDate,BasisPrice,MaxMarketOrderVolume,MinMarketOrderVolume,
                                 MaxLimitOrderVolume,MinLimitOrderVolume,PriceTick,
                                 AllowDelivPersonOpen,InstrumentID,InstLifePhase
                                 )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)  
                               ON DUPLICATE KEY UPDATE 
                                 CreateDate=VALUES(CreateDate),OpenDate=VALUES(OpenDate)"""
            sql_params = []
            for stock in stock_data:
                sql_params.append((settlement_group, '99991219', stock.SSRQ,
                           '99991219', '99991219', '99991219', 0, 1000000, 100,
                           1000000, 100, 0.01, 0, stock.ZQDM, 1))
            cursor.executemany(sql_Property, sql_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_InstrumentProperty完成")

    def __t_MarketData(self, mysqlDB, settlement_group, stock_data):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
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
            for stock in stock_data:
                sql_insert_params.append((self.TradingDay, settlement_group, None, stock.QSPJ,
                                          stock.QSPJ, None, '0', None,
                                          None, None, None, None,
                                          None, None, None,
                                          None, None, None,
                                          None, stock.GXSJ, "100", stock.ZQDM))
            cursor.executemany(sql_insert_market, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_MarketData完成")

    def __check_file(self, *stock_filter):
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
        stock_data = dict()
        # 遍历导入文件
        for filename in self.stock_filename:
            stock_path = '%s%s%s%s%s' % (catalog, os.path.sep, filename, now[4:8], '.txt')
            # 判断文件是否存在
            if not os.path.exists(stock_path):
                self.logger.error("%s%s" % (stock_path, " is not exists"))
                return None
            # 读取txt文件
            stock_file = codecs.open(stock_path, encoding='gbk')
            stock_data.update({self.stock_filename[filename]: self.__txt_to_stock(stock_file, stock_filter)})
        return stock_data

    def __txt_to_stock(self, txt, stock_filter):
        stock_list = []
        for lines in txt:
            VO = stockVO(lines.split("|"))
            if stock_filter is None:
                stock_list.append(VO)
            elif VO.ZQLB in stock_filter:
                stock_list.append(VO)
        return stock_list

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
    # 启动stock脚本
    trans_stockinfo_txt(context=context, configs=conf)
