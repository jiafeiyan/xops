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
        # ===========处理stock_dbf写入t_Instrument表==============
        self.__t_Instrument(mysqlDB=mysqlDB, dbf=dbfs[0])

        # ===========处理stock_dbf写入t_TradingSegmentAttr表==============
        self.__t_TradingSegmentAttr(mysqlDB=mysqlDB, dbf=dbfs[0])

        # ===========处理stock_dbf写入t_MarginRate表(未更新)==============
        self.__t_MarginRate(mysqlDB=mysqlDB, dbf=dbfs[0])

        # ===========处理stock_dbf写入t_MarginRateDetail表==============
        self.__t_MarginRateDetail(mysqlDB=mysqlDB, dbf=dbfs[0])

        # ===========处理stock_dbf写入t_PriceBanding表==============
        self.__t_PriceBanding(mysqlDB=mysqlDB, dbf=dbfs[0])

        # ===========处理info_dbf写入t_SecurityProfit表===========
        self.__t_SecurityProfit(mysqlDB=mysqlDB, dbf=dbfs[1])

        # ===========判断并写入t_InstrumentProperty表(未更新)==============
        self.__t_InstrumentProperty(mysqlDB=mysqlDB, dbf=dbfs[0])

    # 读取处理PAR_STOCK文件
    def __t_Instrument(self, mysqlDB, dbf):
        stock_dbf = dbf
        # 判断合约是否已存在
        dbf_stock = []
        exist_stock = []
        sql_Instrument = " SELECT InstrumentID " + \
                         " FROM siminfo.t_Instrument " + \
                         " WHERE (InstrumentID, SettlementGroupID) in ("
        for stock in stock_dbf:
            dbf_stock.append(stock['ZQDM'])
            sql_values = "('" + stock['ZQDM'] + "', '" + self.self_conf[str(stock['SCDM'])] + "') "
            sql_Instrument = sql_Instrument + sql_values + ","
        sql_Instrument = sql_Instrument[0:-1] + ")"

        # 查询存在数据
        for stock in mysqlDB.select(sql_Instrument):
            exist_stock.append(str(stock[0]))

        # 获取差集
        inexist_stock = list(set(dbf_stock) ^ set(exist_stock))
        self.logger.info("%s%d%s" % ("dbf导入stock条数：", len(dbf_stock), "条"))
        self.logger.info("%s%d%s" % ("t_Instrument中stock存在：", len(exist_stock), "条"))
        self.logger.info("%s%d%s" % ("t_Instrument中stock不存在：", len(inexist_stock), "条"))

        # 不存在插入记录
        sql_insert_Instrument = """INSERT INTO siminfo.t_Instrument (
                                   SettlementGroupID,ProductID,
                                   ProductGroupID,UnderlyingInstrID,
                                   ProductClass,PositionType,
                                   StrikePrice,OptionsType,
                                   VolumeMultiple,UnderlyingMultiple,
                                   TotalEquity,CirculationEquity,
                                   InstrumentID,InstrumentName,
                                   DeliveryYear,DeliveryMonth,AdvanceMonth
                               )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        # 存在更新记录
        sql_update_Instrument = """UPDATE siminfo.t_Instrument
                                       SET InstrumentName=%s,TotalEquity=%s,CirculationEquity=%s
                                       WHERE InstrumentID = %s
                                       AND SettlementGroupID = %s"""
        sql_insert_params = []
        sql_update_params = []
        for stock in stock_dbf:
            if stock['ZQDM'] in inexist_stock:
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
                continue
            if stock['ZQDM'] in exist_stock:
                sql_update_params.append((stock['ZQJC'], stock['ZGB'], stock['LTGB'],
                                          stock['ZQDM'], self.self_conf[str(stock['SCDM'])]))
        mysqlDB.executemany(sql_insert_Instrument, sql_insert_params)
        mysqlDB.executemany(sql_update_Instrument, sql_update_params)

    # 读取处理PAR_QY_INFO文件
    def __t_SecurityProfit(self, mysqlDB, dbf):
        info_dbf = dbf
        # 判断权益信息是否已存在
        dbf_qy_info = []
        exist_qy_info = []
        sql_qy_info = " SELECT SecurityID, SecurityType, SecurityMarketID,  ProfitType" + \
                      " FROM siminfo.t_SecurityProfit " + \
                      " WHERE (SecurityID, SecurityType, SecurityMarketID, ProfitType, SettlementGroupID) in ("
        for info in info_dbf:
            dbf_qy_info.append((info['ZQDM'], info['ZQLX'], info['SCDM'], info['QYKIND']))
            sql_values = "('" + info['ZQDM'] + "', '" + info['ZQLX'] + "', '" + info['SCDM'] + "', '" + \
                         info['QYKIND'] + "', '" + self.self_conf[str(info['SCDM'])] + "') "
            sql_qy_info = sql_qy_info + sql_values + ","
        sql_qy_info = sql_qy_info[0:-1] + ")"

        # 查询存在数据
        for info in mysqlDB.select(sql_qy_info):
            exist_qy_info.append((str(info[0]), str(info[1]), str(info[2]), str(info[3])))

        # 获取差集
        inexist_qy_info = list(set(dbf_qy_info) ^ set(exist_qy_info))
        self.logger.info("%s%d%s" % ("dbf导入qy_info条数：", len(dbf_qy_info), "条"))
        self.logger.info("%s%d%s" % ("t_SecurityProfit存在：", len(exist_qy_info), "条"))
        self.logger.info("%s%d%s" % ("t_SecurityProfit不存在：", len(inexist_qy_info), "条"))

        # 不存在插入记录
        sql_insert_qy_info = """INSERT INTO siminfo.t_SecurityProfit (
                                   SettlementGroupID,SecurityID,
                                   SecurityType,SecurityMarketID,
                                   ProfitType,DJDate,
                                   CQDate,EndDate,
                                   DZDate,BeforeRate,
                                   AfterRate,Price
                               )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        # 存在更新记录
        sql_update_qy_info = """UPDATE siminfo.t_SecurityProfit
                                   SET DJDate=%s,CQDate=%s,EndDate=%s,
                                   DZDate=%s,BeforeRate=%s,
                                   AfterRate=%s,Price=%s
                                   WHERE SecurityID=%s AND SettlementGroupID=%s
                                   AND SecurityType=%s AND SecurityMarketID=%s
                                   AND ProfitType=%s"""
        sql_insert_params = []
        sql_update_params = []
        for info in info_dbf:
            if (info['ZQDM'], info['ZQLX'], info['SCDM'], info['QYKIND']) in inexist_qy_info:
                sql_insert_params.append((self.self_conf[str(info['SCDM'])], info['ZQDM'],
                                          info['ZQLX'], info['SCDM'], info['QYKIND'],
                                          info['DJDATE'], info['CQDATE'], info['ENDDATE'],
                                          info['DZDATE'], info['BEFORERATE'],
                                          info['AFTERRATE'], info['PRICE']))
                continue
            if (info['ZQDM'], info['ZQLX'], info['SCDM'], info['QYKIND']) in exist_qy_info:
                sql_update_params.append((info['DJDATE'], info['CQDATE'], info['ENDDATE'],
                                          info['DZDATE'], info['BEFORERATE'],
                                          info['AFTERRATE'], info['PRICE'],
                                          info['ZQDM'], self.self_conf[str(info['SCDM'])],
                                          info['ZQLX'], info['SCDM'], info['QYKIND']))
        mysqlDB.executemany(sql_insert_qy_info, sql_insert_params)
        mysqlDB.executemany(sql_update_qy_info, sql_update_params)

    # 写入t_InstrumentProperty
    def __t_InstrumentProperty(self, mysqlDB, dbf):
        dbf_stock = []
        exist_stock = []
        sql_Property = " SELECT InstrumentID " + \
                       " FROM siminfo.t_InstrumentProperty " + \
                       " WHERE (InstrumentID, SettlementGroupID) in ("
        for stock in dbf:
            dbf_stock.append(stock['ZQDM'])
            sql_values = "('" + stock['ZQDM'] + "', '" + self.self_conf[str(stock['SCDM'])] + "') "
            sql_Property = sql_Property + sql_values + ","
        sql_Property = sql_Property[0:-1] + ")"

        # 查询存在数据
        for stock in mysqlDB.select(sql_Property):
            exist_stock.append(str(stock[0]))

        # 获取差集
        inexist_stock = list(set(dbf_stock) ^ set(exist_stock))

        self.logger.info("%s%d%s" % ("stock导入t_InstrumentProperty存在：", len(exist_stock), "条"))
        self.logger.info("%s%d%s" % ("stock导入t_InstrumentProperty不存在：", len(inexist_stock), "条"))

        # 插入不存在记录
        sql_Property = """INSERT INTO siminfo.t_InstrumentProperty (
                                      SettlementGroupID,CreateDate,OpenDate,ExpireDate,StartDelivDate,
                                      EndDelivDate,BasisPrice,MaxMarketOrderVolume,MinMarketOrderVolume,
                                      MaxLimitOrderVolume,MinLimitOrderVolume,PriceTick,
                                      AllowDelivPersonOpen,InstrumentID,InstLifePhase
                                      )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        sql_params = []
        for stock in dbf:
            if stock['ZQDM'] in inexist_stock:
                sql_params.append((self.self_conf[str(stock['SCDM'])], stock['FXRQ'], stock['SSRQ'],
                                   '99991219', '99991219', '99991219', 0, 1000000, 100,
                                   1000000, 100, 0.01, 0, stock['ZQDM'], 1))
        mysqlDB.executemany(sql_Property, sql_params)

    # 写入t_TradingSegmentAttr
    def __t_TradingSegmentAttr(self, mysqlDB, dbf):
        # 判断合约是否已存在
        dbf_stock = []
        exist_segment = []
        sql_segment = " SELECT InstrumentID " + \
                      " FROM siminfo.t_TradingSegmentAttr " + \
                      " WHERE (InstrumentID, SettlementGroupID) in ("
        for stock in dbf:
            dbf_stock.append(stock['ZQDM'])
            sql_values = "('" + stock['ZQDM'] + "', '" + self.self_conf[str(stock['SCDM'])] + "') "
            sql_segment = sql_segment + sql_values + ","
        sql_segment = sql_segment[0:-1] + ") GROUP BY InstrumentID"

        # 查询存在数据
        for stock in mysqlDB.select(sql_segment):
            exist_segment.append(str(stock[0]))

        # 获取差集
        inexist_segment = list(set(dbf_stock) ^ set(exist_segment))
        self.logger.info("%s%d%s" % ("stock导入t_TradingSegmentAttr存在：", len(exist_segment), "个合约"))
        self.logger.info("%s%d%s" % ("stock导入t_TradingSegmentAttr不存在：", len(inexist_segment), "个合约"))

        # 不存在插入记录
        sql_insert_segment = """INSERT INTO siminfo.t_TradingSegmentAttr (
                                        SettlementGroupID,TradingSegmentSN,
                                        TradingSegmentName,StartTime,
                                        InstrumentStatus,InstrumentID
                                    ) VALUES (%s,%s,%s,%s,%s,%s)"""
        # 存在更新记录
        sql_update_segment = """UPDATE siminfo.t_TradingSegmentAttr
                                        SET TradingSegmentName=%s,
                                         StartTime=%s,InstrumentStatus=%s
                                        WHERE SettlementGroupID=%s AND InstrumentID=%s AND TradingSegmentSN=%s"""
        sql_insert_params = []
        sql_update_params = []
        SegmentAttr = self.__loadJSON(tableName='t_TradingSegmentAttr')
        if SegmentAttr is None:
            return
        for stock in dbf:
            SGID = self.self_conf[str(stock['SCDM'])]
            # 插入记录
            if stock['ZQDM'] in inexist_segment and SGID in SegmentAttr:
                for attr in SegmentAttr[SGID]:
                    sql_insert_params.append((
                        SGID, attr[1], attr[2], attr[3], attr[4], stock['ZQDM']
                    ))
                continue
            # 更新记录
            if stock['ZQDM'] in exist_segment and SGID in SegmentAttr:
                for attr in SegmentAttr[SGID]:
                    sql_update_params.append((
                        attr[2], attr[3], attr[4], SGID, stock['ZQDM'], attr[1]
                    ))
        mysqlDB.executemany(sql_insert_segment, sql_insert_params)
        mysqlDB.executemany(sql_update_segment, sql_update_params)

    # 写入t_MarginRate
    def __t_MarginRate(self, mysqlDB, dbf):
        # 判断合约是否存在
        dbf_stock = []
        exist_rate = []
        # 获取模板文件
        template = self.__loadJSON(tableName='t_MarginRate')
        if template is None:
            self.logger.error("t_MarginRate template is None")
            return
        sql_marginrate = " SELECT InstrumentID " + \
                         " FROM siminfo.t_MarginRate " + \
                         " WHERE (SettlementGroupID, MarginCalcID, InstrumentID, ParticipantID) in ("
        for stock in dbf:
            dbf_stock.append(stock['ZQDM'])
            SGID = self.self_conf[str(stock['SCDM'])]
            sql_values = "('" + SGID + \
                         "', '" + template[SGID][1] + \
                         "', '" + stock['ZQDM'] + \
                         "', '" + template[SGID][3] + \
                         "') "
            sql_marginrate = sql_marginrate + sql_values + ","
        sql_marginrate = sql_marginrate[0:-1] + ") "

        for stock in mysqlDB.select(sql_marginrate):
            exist_rate.append(str(stock[0]))

        # 获取差集
        inexist_rate = list(set(dbf_stock) ^ set(exist_rate))
        self.logger.info("%s%d%s" % ("stock导入t_MarginRate存在：", len(exist_rate), "个合约"))
        self.logger.info("%s%d%s" % ("stock导入t_MarginRate不存在：", len(inexist_rate), "个合约"))

        # 不存在插入记录
        sql_insert_rate = """INSERT INTO t_MarginRate (
                                SettlementGroupID,
                                MarginCalcID,
                                InstrumentID,
                                ParticipantID
                            ) VALUES (%s,%s,%s,%s)"""
        sql_insert_params = []
        for stock in dbf:
            # 插入记录
            if stock['ZQDM'] in inexist_rate:
                SGID = self.self_conf[str(stock['SCDM'])]
                sql_insert_params.append((SGID, template[SGID][1], stock['ZQDM'], template[SGID][3]))
        mysqlDB.executemany(sql_insert_rate, sql_insert_params)

    # 写入t_MarginRateDetail
    def __t_MarginRateDetail(self, mysqlDB, dbf):
        # 判断合约是否存在
        dbf_stock = []
        exist_detail = []
        # 获取模板文件
        template = self.__loadJSON(tableName='t_MarginRateDetail')
        if template is None:
            self.logger.error("t_MarginRateDetail template is None")
            return
        sql_marginratedetail = " SELECT InstrumentID " + \
                               " FROM siminfo.t_MarginRateDetail " + \
                               " WHERE (SettlementGroupID, TradingRole, HedgeFlag, " \
                               " InstrumentID, ParticipantID, ClientID) in ("
        for stock in dbf:
            dbf_stock.append(stock['ZQDM'])
            SGID = self.self_conf[str(stock['SCDM'])]
            sql_values = "('" + SGID + \
                         "', '" + template[SGID][1] + \
                         "', '" + template[SGID][2] + \
                         "', '" + stock['ZQDM'] + \
                         "', '" + template[SGID][9] + \
                         "', '" + template[SGID][10] + \
                         "') "
            sql_marginratedetail = sql_marginratedetail + sql_values + ","
        sql_marginratedetail = sql_marginratedetail[0:-1] + ") "

        for stock in mysqlDB.select(sql_marginratedetail):
            exist_detail.append(str(stock[0]))

        # 获取差集
        inexist_detail = list(set(dbf_stock) ^ set(exist_detail))
        self.logger.info("%s%d%s" % ("stock导入t_MarginRateDetail存在：", len(exist_detail), "个合约"))
        self.logger.info("%s%d%s" % ("stock导入t_MarginRateDetail不存在：", len(inexist_detail), "个合约"))

        # 不存在插入记录
        sql_insert_detail = """INSERT INTO siminfo.t_MarginRateDetail (
                                SettlementGroupID,TradingRole,HedgeFlag,
                                ValueMode,LongMarginRatio,ShortMarginRatio,
                                InstrumentID,ParticipantID,ClientID
                            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        # 存在更新记录
        sql_update_detail = """UPDATE siminfo.t_MarginRateDetail
                                SET ValueMode=%s,LongMarginRatio=%s,ShortMarginRatio=%s
                                WHERE SettlementGroupID=%s AND TradingRole=%s AND HedgeFlag=%s
                                AND InstrumentID=%s AND ParticipantID=%s AND ClientID=%s"""
        sql_insert_params = []
        sql_update_params = []
        for stock in dbf:
            SGID = self.self_conf[str(stock['SCDM'])]
            # 插入记录
            if stock['ZQDM'] in inexist_detail:
                sql_insert_params.append((SGID, template[SGID][1], template[SGID][2], template[SGID][3],
                                          template[SGID][4], template[SGID][5], stock['ZQDM'],
                                          template[SGID][9], template[SGID][10]))
                continue
            # 更新记录
            if stock['ZQDM'] in exist_detail:
                sql_update_params.append((template[SGID][3], template[SGID][4], template[SGID][5],
                                          SGID, template[SGID][1], template[SGID][2],
                                          stock['ZQDM'], template[SGID][9], template[SGID][10]))
        mysqlDB.executemany(sql_insert_detail, sql_insert_params)
        mysqlDB.executemany(sql_update_detail, sql_update_params)

    # 写入t_PriceBanding
    def __t_PriceBanding(self, mysqlDB, dbf):
        # 判断合约是否存在
        dbf_stock = []
        exist_price = []
        # 获取模板文件
        template = self.__loadJSON(tableName='t_PriceBanding')
        if template is None:
            self.logger.error("t_PriceBanding template is None")
            return
        sql_pricebanding = "SELECT InstrumentID FROM siminfo.t_PriceBanding " \
                           "WHERE (SettlementGroupID,InstrumentID,TradingSegmentSN) in ("
        for stock in dbf:
            dbf_stock.append(stock['ZQDM'])
            SGID = self.self_conf[str(stock['SCDM'])]
            sql_values = "('" + SGID + \
                         "', '" + stock['ZQDM'] + \
                         "', '" + template[SGID][7] + \
                         "') "
            sql_pricebanding = sql_pricebanding + sql_values + ","
        sql_pricebanding = sql_pricebanding[0:-1] + ") "

        for stock in mysqlDB.select(sql_pricebanding):
            exist_price.append(str(stock[0]))

        # 获取差集
        inexist_price = list(set(dbf_stock) ^ set(exist_price))
        self.logger.info("%s%d%s" % ("stock导入t_PriceBanding存在：", len(exist_price), "个合约"))
        self.logger.info("%s%d%s" % ("stock导入t_PriceBanding不存在：", len(inexist_price), "个合约"))

        # 不存在插入记录
        sql_insert_price = """INSERT INTO siminfo.t_PriceBanding (
                                SettlementGroupID,PriceLimitType,ValueMode,RoundingMode,
                                UpperValue,LowerValue,InstrumentID,TradingSegmentSN
                            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) """
        # 存在更新记录
        sql_update_price = """UPDATE siminfo.t_PriceBanding
                                SET PriceLimitType=%s,ValueMode=%s,RoundingMode=%s,UpperValue=%s,LowerValue=%s
                                WHERE SettlementGroupID=%s AND InstrumentID=%s AND TradingSegmentSN=%s"""
        sql_insert_params = []
        sql_update_params = []
        for stock in dbf:
            SGID = self.self_conf[str(stock['SCDM'])]
            if stock['ZQDM'] in inexist_price:
                sql_insert_params.append((SGID, template[SGID][1], template[SGID][2], template[SGID][3],
                                          template[SGID][4], template[SGID][5], stock['ZQDM'],
                                          template[SGID][7]))
                continue
            # 更新记录
            if stock['ZQDM'] in exist_price:
                sql_update_params.append((template[SGID][1], template[SGID][2], template[SGID][3],
                                          template[SGID][4], template[SGID][5], SGID, stock['ZQDM'],
                                          template[SGID][7]))
        mysqlDB.executemany(sql_insert_price, sql_insert_params)
        mysqlDB.executemany(sql_update_price, sql_update_params)

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
        par_stock = '%s%s%s%s%s' % (catalog, os.path.sep, self.stock_filename, now, '.dbf')
        par_qy_info = '%s%s%s%s%s' % (catalog, os.path.sep, self.qy_info_filename, now, '.dbf')

        # 判断PAR_STOCKYYYYMMDD.dbf文件是否存在
        if not os.path.exists(par_stock):
            self.logger.error("%s%s" % (par_stock, " is not exists"))
            return None
        # 判断PAR_QY_INFOYYYYMMDD.dbf文件是否存在
        if not os.path.exists(par_qy_info):
            self.logger.error("%s%s" % (par_qy_info, " is not exists"))
            return None
        # 读取DBF文件
        return self.__loadDBF(stock=par_stock, info=par_qy_info)

    def __loadDBF(self, **par):
        # 加载 PAR_STOCK 数据
        stock = DBF(filename=par['stock'], encoding='GBK')
        stock.load()
        # 加载 PAR_QY_INFO 数据
        info = DBF(filename=par['info'], encoding='GBK')
        info.load()
        return stock.records, info.records

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
