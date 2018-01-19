# -*- coding: UTF-8 -*-

import os
import datetime
import json


from utils import parse_args
from utils import load
from utils import mysql
from utils import log
from dbfread import DBF


class trans_futureinfo:
    def __init__(self, configs):
        if "Log" in configs:
            self.logger = log.get_logger(category="trans_future",
                                         file_Path=configs["Log"]["file_path"],
                                         console_level=configs["Log"]["console_level"],
                                         file_level=configs["Log"]["file_level"])
        else:
            self.logger = log.get_logger(category="trans_future")

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
        self.configs = configs
        self.__transform()

    def __transform(self):
        # 读取dbf文件
        dbfs = self.__check_file()
        if dbfs is None:
            return

        mysqlDB = self.configs['db_instance']
        # ===========处理futures_dbf写入t_Instrument表==============
        self.__t_Instrument(mysqlDB=mysqlDB, dbf=dbfs[0])

        # ===========处理futures_dbf写入t_TradingSegmentAttr表==============
        self.__t_TradingSegmentAttr(mysqlDB=mysqlDB, dbf=dbfs[0], config=self.configs)

        # ===========处理gjshq_dbf写入t_MarketData表 ==============
        self.__t_MarketData(mysqlDB=mysqlDB, dbf=dbfs[1])

        # ===========判断并写入t_InstrumentProperty表(如果存在不写入)==============
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
        self.logger.info("%s%d%s" % ("dbf导入futures条数：", len(dbf_futures), "条"))
        self.logger.info("%s%d%s" % ("t_Instrument存在：", len(exist_futures), "条"))
        self.logger.info("%s%d%s" % ("t_Instrument不存在：", len(inexist_futures), "条"))

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
                                   FROM t_Product t1, t_ProductGroup t2
                                   WHERE t1.SettlementGroupID = t2.SettlementGroupID
                                   AND t1.ProductGroupID = t2.ProductGroupID
                                   AND t2.CommodityID = %s AND t1.ProductClass = %s"""
        # 存在更新记录
        sql_update_futures = """UPDATE t_Instrument
                                        SET InstrumentName=%s,VolumeMultiple=%s
                                        WHERE InstrumentID = %s
                                        AND SettlementGroupID = %s"""
        sql_insert_params = []
        sql_update_params = []
        for future in futures_dbf:
            if future['ZQDM'] in inexist_futures:
                # 判断行业类型是否为CP,如果是为期权，其余为期货
                ProductClass = '1'
                if str(future['HYLX']) == 'C' or str(future['HYLX']) == 'P':
                    ProductClass = '2'
                sql_insert_params.append((self.self_conf[future['JYSC'].encode('UTF-8')], "2", None, "0",
                                          future['JYDW'], 1, future['ZQDM'], future['ZQMC'],
                                          2099, 12, "012", future['JYPZ'], ProductClass))
                continue
            if future['ZQDM'] in exist_futures:
                sql_update_params.append(
                    (future['ZQMC'], future['JYDW'], future['ZQDM'], self.self_conf[future['JYSC'].encode('UTF-8')]))
        mysqlDB.executemany(sql_insert_futures, sql_insert_params)
        mysqlDB.executemany(sql_update_futures, sql_update_params)

    # 读取处理GJSHQ文件
    def __t_MarketData(self, mysqlDB, dbf):
        gjshq_dbf = dbf
        # 判断贵金属行情是否已存在
        dbf_gjshq = []
        exist_gjshq = []
        sql_gjshq = " SELECT InstrumentID " + \
                    " FROM siminfo.t_MarketData " + \
                    " WHERE  (InstrumentID,SettlementGroupID) in ("
        for hq in gjshq_dbf:
            dbf_gjshq.append(hq['HYDM'])
            sql_values = "('" + hq['HYDM'] + "', '" + self.self_conf[hq['JYSC'].encode('UTF-8')] + "') "
            sql_gjshq = sql_gjshq + sql_values + ","
        sql_gjshq = sql_gjshq[0:-1] + ")"

        # 查询存在数据
        for hq in mysqlDB.select(sql_gjshq):
            exist_gjshq.append(str(hq[0]))

        # 获取差集
        inexist_gjshq = list(set(dbf_gjshq) ^ set(exist_gjshq))
        self.logger.info("%s%d%s" % ("dbf导入gjshq条数：", len(dbf_gjshq), "条"))
        self.logger.info("%s%d%s" % ("t_MarketData存在：", len(exist_gjshq), "条"))
        self.logger.info("%s%d%s" % ("t_MarketData不存在：", len(inexist_gjshq), "条"))

        # 不存在插入记录
        sql_insert_gjshq = """INSERT INTO siminfo.t_MarketData (
                                        SettlementGroupID,LastPrice,PreSettlementPrice,
                                        PreClosePrice,PreOpenInterest,OpenPrice,
                                        HighestPrice,LowestPrice,Volume,Turnover,
                                        OpenInterest,ClosePrice,SettlementPrice,
                                        UpperLimitPrice,LowerLimitPrice,PreDelta,
                                        CurrDelta,UpdateTime,UpdateMillisec,InstrumentID
                                   )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        # 存在更新记录
        sql_update_gjshq = """UPDATE t_MarketData 
                                    SET OpenPrice = %s,
                                        HighestPrice = %s,
                                        LowestPrice = %s,
                                        Volume = %s,
                                        Turnover = %s,
                                        ClosePrice = %s,
                                        SettlementPrice = %s
                                    WHERE SettlementGroupID = %s AND InstrumentID = %s"""
        sql_insert_params = []
        sql_update_params = []
        for hq in gjshq_dbf:
            if hq['HYDM'] in inexist_gjshq:
                sql_insert_params.append((self.self_conf[hq['JYSC'].encode('UTF-8')],
                                          None, None, None, 0, hq['KPJ'], hq['ZGJ'], hq['ZDJ'], hq['CJL'],
                                          hq['CJJE'], None, hq['SPJ'], hq['JQPJJ'], None, None, None, None, None, None,
                                          hq['HYDM']))
                continue
            if hq['HYDM'] in exist_gjshq:
                sql_update_params.append(
                    (hq['KPJ'], hq['ZGJ'], hq['ZDJ'], hq['CJL'], hq['CJJE'], hq['SPJ'], hq['JQPJJ'],
                     self.self_conf[hq['JYSC'].encode('UTF-8')], hq['HYDM']))
        mysqlDB.executemany(sql_insert_gjshq, sql_insert_params)
        mysqlDB.executemany(sql_update_gjshq, sql_update_params)

    # 写入t_InstrumentProperty
    def __t_InstrumentProperty(self, mysqlDB, dbf):
        dbf_futures = []
        exist_futures = []
        sql_Property = " SELECT InstrumentID " + \
                       " FROM t_InstrumentProperty " + \
                       " WHERE (InstrumentID,SettlementGroupID) in ("
        for future in dbf:
            dbf_futures.append(future['ZQDM'])
            sql_values = "('" + future['ZQDM'] + "', '" + self.self_conf[future['JYSC'].encode('UTF-8')] + "') "
            sql_Property = sql_Property + sql_values + ","

        sql_Property = sql_Property[0:-1] + ")"

        # 查询存在数据
        for future in mysqlDB.select(sql_Property):
            exist_futures.append(str(future[0]))

        # 获取差集
        inexist_futures = list(set(dbf_futures) ^ set(exist_futures))
        self.logger.info("%s%d%s" % ("future导入t_InstrumentProperty存在：", len(exist_futures), "条"))
        self.logger.info("%s%d%s" % ("future导入t_InstrumentProperty不存在：", len(inexist_futures), "条"))

        # 插入不存在记录
        sql_Property = """INSERT INTO t_InstrumentProperty (
                                         SettlementGroupID,CreateDate,OpenDate,ExpireDate,StartDelivDate,
                                         EndDelivDate,BasisPrice,MaxMarketOrderVolume,MinMarketOrderVolume,
                                         MaxLimitOrderVolume,MinLimitOrderVolume,PriceTick,
                                         AllowDelivPersonOpen,InstrumentID,InstLifePhase
                                         )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        sql_params = []
        for future in dbf:
            if future['ZQDM'] in inexist_futures:
                sql_params.append((self.self_conf[future['JYSC'].encode('UTF-8')], future['SSRQ'], future['SSRQ'],
                                   '99991219', '99991219', '99991219', 0, 1000000, 100,
                                   1000000, 100, 0.01, 0, future['ZQDM'], 1))
        mysqlDB.executemany(sql_Property, sql_params)

    def __t_TradingSegmentAttr(self, mysqlDB, dbf, config):
        # 判断合约是否已存在
        dbf_futures = []
        exist_segment = []
        sql_segment = " SELECT InstrumentID " + \
                      " FROM siminfo.t_TradingSegmentAttr " + \
                      " WHERE (InstrumentID, SettlementGroupID) in ("
        for future in dbf:
            dbf_futures.append(future['ZQDM'])
            sql_values = "('" + future['ZQDM'] + "', '" + self.self_conf[future['JYSC'].encode('UTF-8')] + "') "
            sql_segment = sql_segment + sql_values + ","
        sql_segment = sql_segment[0:-1] + ") GROUP BY InstrumentID"

        # 查询存在数据
        for future in mysqlDB.select(sql_segment):
            exist_segment.append(str(future[0]))

        # 获取差集
        inexist_segment = list(set(dbf_futures) ^ set(exist_segment))
        self.logger.info("%s%d%s" % ("future导入t_TradingSegmentAttr存在：", len(exist_segment), "个合约"))
        self.logger.info("%s%d%s" % ("future导入t_TradingSegmentAttr不存在：", len(inexist_segment), "个合约"))

        # 不存在插入记录
        sql_insert_segment = """INSERT INTO t_TradingSegmentAttr (
                                    SettlementGroupID,TradingSegmentSN,
                                    TradingSegmentName,StartTime,
                                    InstrumentStatus,InstrumentID
                                ) VALUES (%s,%s,%s,%s,%s,%s)"""
        # 存在更新记录
        sql_update_segment = """UPDATE t_TradingSegmentAttr
                                    SET TradingSegmentName=%s,
                                     StartTime=%s,InstrumentStatus=%s
                                    WHERE SettlementGroupID=%s AND InstrumentID=%s AND TradingSegmentSN=%s"""
        sql_insert_params = []
        sql_update_params = []
        SegmentAttr = self.__loadJSON(tableName='t_TradingSegmentAttr', config=config)
        if SegmentAttr is None:
            return
        for future in dbf:
            SGID = self.self_conf[future['JYSC'].encode('UTF-8')]
            # 插入记录
            if future['ZQDM'] in inexist_segment and SGID in SegmentAttr:
                for attr in SegmentAttr[SGID]:
                    sql_insert_params.append((
                        SGID, attr[1], attr[2], attr[3], attr[4], future['ZQDM']
                    ))
                continue
            # 更新记录
            if future['ZQDM'] in exist_segment and SGID in SegmentAttr:
                for attr in SegmentAttr[SGID]:
                    sql_update_params.append((
                        attr[2], attr[3], attr[4], SGID, future['ZQDM'], attr[1]
                    ))
        mysqlDB.executemany(sql_insert_segment, sql_insert_params)
        mysqlDB.executemany(sql_update_segment, sql_update_params)

    def __check_file(self):
        env_dist = os.environ
        # 判断环境变量是否存在HOME配置
        if 'HOME' not in env_dist:
            self.logger.error("HOME not in environment variable")
            return None
        # 获取文件路径
        catalog = env_dist['HOME']
        now = datetime.datetime.now().strftime("%Y%m%d")
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
        stock = DBF(filename=par['futures'], encoding='GBK')
        stock.load()
        # 加载 gjshq 数据
        info = DBF(filename=par['gjshq'], encoding='GBK')
        info.load()
        return stock.records, info.records

    # 主要读取TradingSegmentAttr配置数据
    def __loadJSON(self, tableName, config):
        path = "%s%s%s%s" % (config['Path']['initialize'], os.path.sep, tableName, ".json")
        if not os.path.exists(path):
            self.logger.error("文件" + tableName + ".json不存在")
            return None
        f = open(path)
        return json.load(f)


if __name__ == '__main__':
    args = parse_args()

    # 读取参数文件
    conf = load(args.conf)

    # 建立mysql数据库连接
    mysql_instance = mysql(configs=conf)
    conf["db_instance"] = mysql_instance

    # 启动future脚本
    trans_futureinfo(conf)
