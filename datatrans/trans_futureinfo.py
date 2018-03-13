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

        if dbfs[0] is not None:
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

            # ===========判断并写入t_InstrumentProperty表==============
            self.__t_InstrumentProperty(mysqlDB=mysqlDB, dbf=dbfs[0])

        if dbfs[1] is not None:
            # ===========处理gjshq_dbf写入t_MarketData表 ==============
            self.__t_MarketData(mysqlDB=mysqlDB, dbf=dbfs[1])

    # 读取处理PAR_FUTURES文件
    def __t_Instrument(self, mysqlDB, dbf):
        sql_insert_futures = """INSERT INTO siminfo.t_Instrument (
                                   SettlementGroupID,ProductID,
                                   ProductGroupID,UnderlyingInstrID,
                                   ProductClass,PositionType,
                                   StrikePrice,OptionsType,
                                   VolumeMultiple,UnderlyingMultiple,
                                   InstrumentID,InstrumentName,
                                   DeliveryYear,DeliveryMonth,AdvanceMonth
                               )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                ON DUPLICATE KEY UPDATE
                                ProductID = VALUES (ProductID),
                                ProductGroupID = VALUES (ProductGroupID),
                                UnderlyingInstrID = VALUES (UnderlyingInstrID),
                                ProductClass = VALUES (ProductClass),
                                PositionType = VALUES (PositionType),
                                StrikePrice = VALUES (StrikePrice),
                                VolumeMultiple = VALUES (VolumeMultiple),
                                UnderlyingMultiple = VALUES (UnderlyingMultiple),
                                InstrumentName = VALUES (InstrumentName),
                                DeliveryYear = VALUES (DeliveryYear),
                                DeliveryMonth = VALUES (DeliveryMonth),
                                AdvanceMonth = VALUES (AdvanceMonth)"""
        sql_insert_params = []
        for future in dbf:
            # 判断行业类型是否为CP,如果是为期权，其余为期货
            ProductClass = '1'
            OptionsType = '0'
            ProductID = str.upper(str(future['JYPZ']))
            ProductGroupID = str.upper(str(future['JYPZ']))
            # 获取结算组ID
            settlement = self.self_conf[future['JYSC'].encode('UTF-8')]
            if str(future['HYLX']) == 'C' or str(future['HYLX']) == 'P':
                ProductClass = '2'
                if str(future['HYLX']) == 'C':
                    OptionsType = '1'
                elif str(future['HYLX']) == 'P':
                    OptionsType = '2'

                if settlement == 'SG03':
                    ProductID = ProductID + '_O'
                if settlement == 'SG04':
                    ProductID = ProductID + '_O'
                if settlement == 'SG05':
                    if str(future['HYLX']) == 'C':
                        ProductID = ProductID + '_C'
                    elif str(future['HYLX']) == 'P':
                        ProductID = ProductID + '_P'
                if settlement == 'SG06':
                    ProductID = ProductID + 'O'
            sql_insert_params.append((settlement, ProductID, ProductGroupID, ProductID, ProductClass,
                                      "2", None, OptionsType,
                                      future['JYDW'], 1, future['ZQDM'], future['ZQMC'],
                                      9999 if not future['DQRQ'] else int(str(future['DQRQ'])[0:4]),
                                      12 if not future['DQRQ'] else int(str(future['DQRQ'])[4:6]), "012"))
        mysqlDB.executemany(sql_insert_futures, sql_insert_params)
        self.logger.info("写入t_Instrument完成")
        # 导入完成后写入产品表
        self.__init_product()

    def __init_product(self):
        mysqlDB = self.mysqlDB
        # t_ClientProductRight
        self.logger.info("产品类型导入t_ClientProductRight")
        sql = """INSERT into siminfo.t_ClientProductRight(
                SELECT SettlementGroupID,ProductID,'00000000' AS ClientID,'0' AS TradingRight 
                FROM siminfo.t_instrument 
                WHERE SettlementGroupID in ('SG03','SG04','SG05','SG06')
                GROUP BY SettlementGroupID,ProductID)
                ON DUPLICATE KEY UPDATE
                SettlementGroupID = VALUES (SettlementGroupID),
                ProductID = VALUES (ProductID)"""
        mysqlDB.execute(sql=sql)
        # t_MarketProduct
        self.logger.info("产品类型导入t_MarketProduct")
        sql = """INSERT into siminfo.t_MarketProduct(
                SELECT t.SettlementGroupID, t1.MarketID, t.ProductID 
                FROM siminfo.t_instrument t,siminfo.t_market t1 
                WHERE t.SettlementGroupID = t1.SettlementGroupID 
                    AND t.SettlementGroupID IN ( 'SG03', 'SG04', 'SG05', 'SG06' ) 
                GROUP BY t.SettlementGroupID,t.ProductID,t1.MarketID)
                ON DUPLICATE KEY UPDATE
                SettlementGroupID = VALUES (SettlementGroupID),
                MarketID = VALUES (MarketID),
                ProductID = VALUES (ProductID)"""
        mysqlDB.execute(sql=sql)
        # t_MdPubStatus
        self.logger.info("产品类型导入t_MdPubStatus")
        sql = """INSERT into siminfo.t_MdPubStatus(
                SELECT SettlementGroupID,ProductID,'3' AS InstrumentStatus,'0' AS MdPubStatus 
                FROM siminfo.t_instrument 
                WHERE SettlementGroupID IN ('SG03','SG04','SG05','SG06')
                GROUP BY SettlementGroupID,ProductID)
                ON DUPLICATE KEY UPDATE
                SettlementGroupID = VALUES (SettlementGroupID),
                ProductID = VALUES (ProductID)"""
        mysqlDB.execute(sql=sql)
        # t_PartProductRight
        self.logger.info("产品类型导入t_PartProductRight")
        sql = """INSERT INTO siminfo.t_PartProductRight(
                SELECT SettlementGroupID,ProductID,'00000000' AS ParticipantID,'0' AS TradingRight 
                FROM siminfo.t_instrument 
                WHERE SettlementGroupID IN ('SG03','SG04','SG05','SG06')
                GROUP BY SettlementGroupID,ProductID)
                ON DUPLICATE KEY UPDATE
                SettlementGroupID = VALUES (SettlementGroupID),
                ProductID = VALUES (ProductID)"""
        mysqlDB.execute(sql=sql)
        # t_PartProductRole
        self.logger.info("产品类型导入t_PartProductRole")
        sql = """INSERT INTO siminfo.t_PartProductRole(
                SELECT SettlementGroupID,'00000000' AS ParticipantID,ProductID,'1' AS TradingRole 
                FROM siminfo.t_instrument 
                WHERE SettlementGroupID IN ('SG03','SG04','SG05','SG06')
                GROUP BY SettlementGroupID,ProductID)
                ON DUPLICATE KEY UPDATE
                SettlementGroupID = VALUES (SettlementGroupID),
                ProductID = VALUES (ProductID)"""
        mysqlDB.execute(sql=sql)
        # t_Product
        self.logger.info("产品类型导入t_Product")
        sql = """INSERT INTO siminfo.t_Product(
                SELECT SettlementGroupID, ProductID, ProductGroupID, '' AS ProductName,'' AS ProductClass 
                FROM siminfo.t_instrument 
                WHERE SettlementGroupID IN ('SG03','SG04','SG05','SG06')
                GROUP BY SettlementGroupID,ProductID,ProductGroupID)
                ON DUPLICATE KEY UPDATE
                SettlementGroupID = VALUES (SettlementGroupID),
                ProductID = VALUES (ProductID),
                ProductGroupID = VALUES (ProductGroupID)"""
        mysqlDB.execute(sql=sql)
        # t_ProductGroup
        self.logger.info("产品类型导入t_ProductGroup")
        sql = """INSERT INTO siminfo.t_ProductGroup(
                SELECT SettlementGroupID,ProductGroupID,'' AS ProductGroupName,ProductGroupID as CommodityID
                FROM siminfo.t_instrument 
                WHERE SettlementGroupID IN ('SG03','SG04','SG05','SG06')
                GROUP BY SettlementGroupID,ProductGroupID,ProductGroupID)
                ON DUPLICATE KEY UPDATE
                SettlementGroupID = VALUES (SettlementGroupID),
                ProductGroupID = VALUES (ProductGroupID)"""
        mysqlDB.execute(sql=sql)

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
                                        PreSettlementPrice = VALUES(PreSettlementPrice),
                                        PreClosePrice = VALUES(PreClosePrice),
                                        UpdateTime = VALUES(UpdateTime),
                                        UpdateMillisec = VALUES(UpdateMillisec)"""
        sql_insert_params = []
        for hq in dbf:
            sql_insert_params.append((self.TradingDay, self.self_conf[hq['JYSC'].encode('UTF-8')], None, hq['JQPJJ'],
                                      hq['SPJ'], '0', None,
                                      None, None, None, None,
                                      None, None, None,
                                      None, None, None,
                                      None, "15:15:00", "100", hq['HYDM']))
        mysqlDB.executemany(sql_insert_gjshq, sql_insert_params)
        self.logger.info("写入t_MarketData完成")

    # 写入t_InstrumentProperty
    def __t_InstrumentProperty(self, mysqlDB, dbf):
        property = self.__loadJSON("t_InstrumentProperty")
        sql_Property = """INSERT INTO siminfo.t_InstrumentProperty (
                                         SettlementGroupID,CreateDate,OpenDate,ExpireDate,StartDelivDate,
                                         EndDelivDate,BasisPrice,MaxMarketOrderVolume,MinMarketOrderVolume,
                                         MaxLimitOrderVolume,MinLimitOrderVolume,PriceTick,
                                         AllowDelivPersonOpen,InstrumentID,InstLifePhase
                                         )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                       ON DUPLICATE KEY UPDATE 
                                          CreateDate=VALUES(CreateDate),OpenDate=VALUES(OpenDate),
                                          ExpireDate=VALUES(ExpireDate),StartDelivDate=VALUES(StartDelivDate),
                                          EndDelivDate=VALUES(EndDelivDate),
                                          MaxMarketOrderVolume=VALUES(MaxMarketOrderVolume),
                                          MinMarketOrderVolume=VALUES(MinMarketOrderVolume),
                                          MaxLimitOrderVolume=VALUES(MaxLimitOrderVolume),
                                          MinLimitOrderVolume=VALUES(MinLimitOrderVolume),
                                          PriceTick=VALUES(PriceTick)"""
        sql_params = []
        for future in dbf:
            ProductID = str.upper(str(future['JYPZ']))
            settlement = self.self_conf[future['JYSC'].encode('UTF-8')]
            if str(future['HYLX']) == 'C' or str(future['HYLX']) == 'P':
                if settlement == 'SG03':
                    ProductID = ProductID + '_O'
                if settlement == 'SG04':
                    ProductID = ProductID + '_O'
                if settlement == 'SG05':
                    if str(future['HYLX']) == 'C':
                        ProductID = ProductID + '_C'
                    elif str(future['HYLX']) == 'P':
                        ProductID = ProductID + '_P'
                if settlement == 'SG06':
                    ProductID = ProductID + 'O'
            sql_params.append((settlement, future['SSRQ'], future['SSRQ'],
                               '99991219' if not future['DQRQ'] else future['DQRQ'],
                               '99991219' if not future['DQRQ'] else future['DQRQ'],
                               '99991219' if not future['DQRQ'] else future['DQRQ'], 0,
                               1000000 if not property[ProductID] else property[ProductID][0],
                               1 if not property[ProductID] else property[ProductID][1],
                               1000000 if not property[ProductID] else property[ProductID][2],
                               1 if not property[ProductID] else property[ProductID][3],
                               0.01 if not property[ProductID] else property[ProductID][4],
                               0, future['ZQDM'], 1))
        mysqlDB.executemany(sql_Property, sql_params)
        self.logger.info("写入t_InstrumentProperty完成")

    # 写入t_TradingSegmentAttr
    def __t_TradingSegmentAttr(self, mysqlDB, dbf):
        sql_insert_segment = """INSERT INTO siminfo.t_TradingSegmentAttr (
                                    SettlementGroupID,TradingSegmentSN,
                                    TradingSegmentName,StartTime,
                                    InstrumentStatus,DayOffset,InstrumentID
                                ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                                ON DUPLICATE KEY UPDATE 
                                  TradingSegmentName=VALUES(TradingSegmentName),
                                  StartTime=VALUES(StartTime),
                                  InstrumentStatus=VALUES(InstrumentStatus),
                                  DayOffset=VALUES(DayOffset)"""
        sql_insert_params = []
        SegmentAttr = self.__loadJSON(tableName='t_TradingSegmentAttr')
        if SegmentAttr is None:
            return
        for future in dbf:
            SGID = self.self_conf[future['JYSC'].encode('UTF-8')]
            if SGID in SegmentAttr:
                for attr in SegmentAttr[SGID]:
                    sql_insert_params.append((
                        SGID, attr[1], attr[2], attr[3], attr[4], '1', future['ZQDM']
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

        # 判断par_futuresYYYYMMDD.dbf文件是否存在，不存在设置为空
        if not os.path.exists(par_futures):
            self.logger.error("%s%s" % (par_futures, " is not exists"))
            par_futures = None
        # 判断gjshqYYYYMMDD.dbf文件是否存在，不存在设置为空
        if not os.path.exists(gjshq):
            self.logger.error("%s%s" % (gjshq, " is not exists"))
            gjshq = None
        # 读取DBF文件
        return self.__loadDBF(futures=par_futures, gjshq=gjshq)

    def __loadDBF(self, **par):
        dbf_1 = None
        dbf_2 = None
        # 加载 par_futures 数据
        if par['futures'] is not None:
            future = DBF(filename=par['futures'], encoding='GBK')
            future.load()
            dbf_1 = future.records
        # 加载 gjshq 数据
        if par['gjshq'] is not None:
            info = DBF(filename=par['gjshq'], encoding='GBK')
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
    # 启动future脚本
    trans_futureinfo(context=context, configs=conf)
