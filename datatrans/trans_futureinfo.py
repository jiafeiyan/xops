# -*- coding: UTF-8 -*-

import os
import datetime
import json


from utils import parse_conf_args
from utils import Configuration
from utils import path
from utils import mysql
from utils import log
from dbfread import DBF


class trans_futureinfo:
    def __init__(self, context, configs):
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="trans_future", configs=log_conf)
        if log_conf is None:
            self.logger.warning("trans_futureinfo未配置Log日志")
        # 初始化数据库连接
        self.mysqlDB = mysql(configs=context.get("mysql")[configs.get("mysqlId")])
        # 初始化模板路径
        self.initTemplate = context.get("init")[configs.get("initId")]
        self.futures_filename = "PAR_FUTURES"
        self.gjshq_filename = "GJSHQ"
        # 结算组ID和交易所对应关系
        self.self_conf = {
            "上海期货交易所": "SG03",
            "大连商品交易所": "SG04",
            "郑州商品交易所": "SG05",
            "中国金融期货交易所": "SG06",
            "上海黄金交易所": "SG97"
        }
        self.__transform()

    def __transform(self):
        # 读取dbf文件
        dbfs = self.__check_file()
        if dbfs is None:
            return

        mysqlDB = self.mysqlDB
        # ===========处理futures_dbf写入t_Instrument表==============
        self.__t_Instrument(mysqlDB=mysqlDB, dbf=dbfs[0])

        # ===========处理futures_dbf写入t_TradingSegmentAttr表==============
        self.__t_TradingSegmentAttr(mysqlDB=mysqlDB, dbf=dbfs[0])

        # ===========处理futures_dbf写入t_MarginRate表==============
        self.__t_MarginRate(mysqlDB=mysqlDB, dbf=dbfs[0])

        # ===========处理futures_dbf写入t_MarginRateDetail表==============
        self.__t_MarginRateDetail(mysqlDB=mysqlDB, dbf=dbfs[0])

        # ===========处理futures_dbf写入t_PriceBanding表==============
        self.__t_PriceBanding(mysqlDB=mysqlDB, dbf=dbfs[0])

        # ===========处理gjshq_dbf写入t_MarketData表 ==============
        self.__t_MarketData(mysqlDB=mysqlDB, dbf=dbfs[1])

        # ===========判断并写入t_InstrumentProperty表==============
        self.__t_InstrumentProperty(mysqlDB=mysqlDB, dbf=dbfs[0])

    # 读取处理PAR_FUTURES文件
    def __t_Instrument(self, mysqlDB, dbf):
        futures_dbf = dbf
        # 判断合约是否已存在
        dbf_futures = []
        exist_futures = []
        sql_futures = " SELECT InstrumentID " + \
                      " FROM siminfo.t_Instrument " + \
                      " WHERE (InstrumentID, SettlementGroupID) in ("
        for future in futures_dbf:
            dbf_futures.append(future['ZQDM'])
            sql_values = "('" + future['ZQDM'] + "', '" + self.self_conf[future['JYSC'].encode('UTF-8')] + "') "
            sql_futures = sql_futures + sql_values + ","
        sql_futures = sql_futures[0:-1] + ")"

        # 查询存在数据
        for future in mysqlDB.select(sql_futures):
            exist_futures.append(str(future[0]))

        # 获取差集
        inexist_futures = list(set(dbf_futures) ^ set(exist_futures))
        # 不存在插入记录
        sql_insert_futures = """INSERT INTO siminfo.t_Instrument (
                                   SettlementGroupID,ProductID,
                                   ProductGroupID,UnderlyingInstrID,
                                   ProductClass,PositionType,
                                   StrikePrice,OptionsType,
                                   VolumeMultiple,UnderlyingMultiple,
                                   InstrumentID,InstrumentName,
                                   DeliveryYear,DeliveryMonth,AdvanceMonth
                               )SELECT %s,t1.ProductID,t1.ProductGroupID,t1.ProductID,t1.ProductClass,
                                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                                   FROM siminfo.t_Product t1, siminfo.t_ProductGroup t2
                                   WHERE t1.SettlementGroupID = t2.SettlementGroupID
                                   AND t1.ProductGroupID = t2.ProductGroupID
                                   AND t2.CommodityID = %s AND t1.ProductClass = %s"""
        # 存在更新记录
        sql_update_futures = """UPDATE siminfo.t_Instrument
                                        SET InstrumentName=%s,VolumeMultiple=%s
                                        WHERE InstrumentID = %s
                                        AND SettlementGroupID = %s"""
        sql_insert_params = []
        sql_update_params = []
        for future in futures_dbf:
            if future['ZQDM'] in inexist_futures:
                # 判断行业类型是否为CP,如果是为期权，其余为期货
                ProductClass = '1'
                OptionsType = '0'
                if str(future['HYLX']) == 'C' or str(future['HYLX']) == 'P':
                    ProductClass = '2'
                    if str(future['HYLX']) == 'C':
                        OptionsType = '1'
                    elif str(future['HYLX']) == 'P':
                        OptionsType = '2'
                sql_insert_params.append((self.self_conf[future['JYSC'].encode('UTF-8')], "2", None, OptionsType,
                                          future['JYDW'], 1, future['ZQDM'], future['ZQMC'],
                                          2099, 12, "012", future['JYPZ'], ProductClass))
                continue
            if future['ZQDM'] in exist_futures:
                sql_update_params.append(
                    (future['ZQMC'], future['JYDW'], future['ZQDM'], self.self_conf[future['JYSC'].encode('UTF-8')]))
        mysqlDB.executemany(sql_insert_futures, sql_insert_params)
        mysqlDB.executemany(sql_update_futures, sql_update_params)
        self.logger.info("写入t_Instrument完成")

    # 读取处理GJSHQ文件
    def __t_MarketData(self, mysqlDB, dbf):
        sql_insert_gjshq = """INSERT INTO siminfo.t_MarketData (
                                        TradingDay,SettlementGroupID,LastPrice,PreSettlementPrice,
                                        PreClosePrice,PreOpenInterest,OpenPrice,
                                        HighestPrice,LowestPrice,Volume,Turnover,
                                        OpenInterest,ClosePrice,SettlementPrice,
                                        UpperLimitPrice,LowerLimitPrice,PreDelta,
                                        CurrDelta,UpdateTime,UpdateMillisec,InstrumentID
                                   )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                   ON DUPLICATE KEY UPDATE  
                                        OpenPrice = VALUES(OpenPrice),
                                        HighestPrice = VALUES(HighestPrice),
                                        LowestPrice = VALUES(LowestPrice),
                                        Volume = VALUES(Volume),
                                        Turnover = VALUES(Turnover),
                                        ClosePrice = VALUES(ClosePrice),
                                        SettlementPrice = VALUES(SettlementPrice)"""
        sql_insert_params = []
        for hq in dbf:
            sql_insert_params.append((self.TradingDay, self.self_conf[hq['JYSC'].encode('UTF-8')],
                                      None, None, None, 0, hq['KPJ'], hq['ZGJ'], hq['ZDJ'], hq['CJL'],
                                      hq['CJJE'], None, hq['SPJ'], hq['JQPJJ'], None, None, None, None, None, None,
                                      hq['HYDM']))
        mysqlDB.executemany(sql_insert_gjshq, sql_insert_params)
        self.logger.info("写入t_MarketData完成")

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
        for future in dbf:
            sql_params.append((self.self_conf[future['JYSC'].encode('UTF-8')], future['SSRQ'], future['SSRQ'],
                               '99991219', '99991219', '99991219', 0, 1000000, 100,
                               1000000, 100, 0.01, 0, future['ZQDM'], 1))
        mysqlDB.executemany(sql_Property, sql_params)
        self.logger.info("写入t_InstrumentProperty完成")

    # 写入t_TradingSegmentAttr
    def __t_TradingSegmentAttr(self, mysqlDB, dbf):
        sql_insert_segment = """INSERT INTO siminfo.t_TradingSegmentAttr (
                                    SettlementGroupID,TradingSegmentSN,
                                    TradingSegmentName,StartTime,
                                    InstrumentStatus,InstrumentID
                                ) VALUES (%s,%s,%s,%s,%s,%s)
                                ON DUPLICATE KEY UPDATE 
                                  TradingSegmentName=VALUES(TradingSegmentName),StartTime=VALUES(StartTime),
                                  InstrumentStatus=VALUES(InstrumentStatus)"""
        sql_insert_params = []
        SegmentAttr = self.__loadJSON(tableName='t_TradingSegmentAttr')
        if SegmentAttr is None:
            return
        for future in dbf:
            SGID = self.self_conf[future['JYSC'].encode('UTF-8')]
            if SGID in SegmentAttr:
                for attr in SegmentAttr[SGID]:
                    sql_insert_params.append((
                        SGID, attr[1], attr[2], attr[3], attr[4], future['ZQDM']
                    ))
        mysqlDB.executemany(sql_insert_segment, sql_insert_params)
        self.logger.info("写入t_TradingSegmentAttr完成")

    # 写入t_MarginRate
    def __t_MarginRate(self, mysqlDB, dbf):
        # 获取模板文件
        template = self.__loadJSON(tableName='t_MarginRate')
        if template is None:
            self.logger.error("t_MarginRate template is None")
            return
        # 不存在插入记录
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
        for future in dbf:
            SGID = self.self_conf[future['JYSC'].encode('UTF-8')]
            if SGID in template:
                sql_insert_params.append((SGID, template[SGID][1], future['ZQDM'], template[SGID][3]))
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
        for future in dbf:
            SGID = self.self_conf[future['JYSC'].encode('UTF-8')]
            if SGID in template:
                sql_insert_params.append((SGID, template[SGID][1], template[SGID][2], template[SGID][3],
                                          template[SGID][4], template[SGID][5], future['ZQDM'],
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
                            RoundingMode=VALUES(RoundingMode),UpperValue=VALUES(UpperValue),
                            LowerValue=VALUES(LowerValue)"""
        sql_insert_params = []
        for future in dbf:
            SGID = self.self_conf[future['JYSC'].encode('UTF-8')]
            if SGID in template:
                sql_insert_params.append((SGID, template[SGID][1], template[SGID][2], template[SGID][3],
                                          template[SGID][4], template[SGID][5], future['ZQDM'],
                                          template[SGID][7]))
        mysqlDB.executemany(sql_insert_price, sql_insert_params)
        self.logger.info("写入t_PriceBanding完成")

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
        par_futures = '%s%s%s%s%s' % (catalog, os.path.sep, self.futures_filename, now, '.dbf')
        gjshq = '%s%s%s%s%s' % (catalog, os.path.sep, self.gjshq_filename, now, '.dbf')

        # 判断par_futuresYYYYMMDD.dbf文件是否存在
        if not os.path.exists(par_futures):
            self.logger.error("%s%s" % (par_futures, " is not exists"))
            return None
        # 判断gjshqYYYYMMDD.dbf文件是否存在
        if not os.path.exists(gjshq):
            self.logger.error("%s%s" % (gjshq, " is not exists"))
            return None
        # 读取DBF文件
        return self.__loadDBF(futures=par_futures, gjshq=gjshq)

    def __loadDBF(self, **par):
        # 加载 par_futures 数据
        future = DBF(filename=par['futures'], encoding='GBK')
        future.load()
        # 加载 gjshq 数据
        info = DBF(filename=par['gjshq'], encoding='GBK')
        info.load()
        return future.records, info.records

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
    # 启动future脚本
    trans_futureinfo(context=context, configs=conf)
