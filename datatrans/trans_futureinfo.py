# -*- coding: UTF-8 -*-

import os
import datetime

from utils.logger.log import log
from dbfread import DBF

futures_filename = "PAR_FUTURES"
gjshq_filename = "GJSHQ"

log = log.get_logger('trans_future')


def transform(param, mysql):
    dbfs = __checkFile()
    if dbfs is None:
        return

    # ================================处理futures_dbf======================================
    futures_dbf = dbfs[0]
    # 判断合约是否已存在，存在不执行
    dbf_futures = []
    exist_futures = []
    sql_futures = " SELECT InstrumentID " + \
                  " FROM siminfo.t_Instrument " + \
                  " WHERE SettlementGroupID = '" + param['SettlementGroupID'] + "'" + \
                  " AND InstrumentID in ("
    for future in futures_dbf:
        dbf_futures.append(future['ZQDM'])
        sql_futures = sql_futures + "'" + future['ZQDM'] + "',"
    sql_futures = sql_futures[0:-1] + ")"

    # 查询存在数据
    for future in mysql.select(sql_futures):
        exist_futures.append(str(future[0]))

    # 获取差集
    inexist_futures = list(set(dbf_futures) ^ set(exist_futures))
    log.info("%s%d%s" % ("dbf导入futures条数：", len(dbf_futures), "条"))
    log.info("%s%d%s" % ("t_Instrument存在：", len(exist_futures), "条"))
    log.info("%s%d%s" % ("t_Instrument不存在：", len(inexist_futures), "条"))

    # 写入t_Instrument
    sql_futures = """INSERT INTO siminfo.t_Instrument (
                            SettlementGroupID,ProductID,
                            ProductGroupID,UnderlyingInstrID,
                            ProductClass,PositionType,
                            StrikePrice,OptionsType,
                            VolumeMultiple,UnderlyingMultiple,
                            InstrumentID,InstrumentName,
                            DeliveryYear,DeliveryMonth,AdvanceMonth
                        )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    sql_params = []
    for future in futures_dbf:
        if future['ZQDM'] in inexist_futures:
            sql_params.append((param['SettlementGroupID'],
                               param['ProductID'],
                               param['ProductGroupID'],
                               param['ProductID'],
                               "1", "2", None, "0",
                               param['VolumeMultiple'],
                               1, future['ZQDM'], future['ZQMC'],
                               2099, 12, "012"
                               ))
    mysql.executemany(sql_futures, sql_params)

    # ================================处理gjshq_dbf======================================
    gjshq_dbf = dbfs[1]
    dbf_gjshq = []
    exist_gjshq = []
    sql_gjshq = " SELECT InstrumentID " + \
                " FROM siminfo.t_MarketData " + \
                " WHERE SettlementGroupID = '" + param['SettlementGroupID'] + "'" + \
                " AND InstrumentID in ("
    for hq in gjshq_dbf:
        dbf_gjshq.append(hq['HYDM'])
        sql_gjshq = sql_gjshq + "'" + hq['HYDM'] + "',"
    sql_gjshq = sql_gjshq[0:-1] + ")"

    # 查询存在数据
    for hq in mysql.select(sql_gjshq):
        exist_gjshq.append(str(hq[0]))

    # 获取差集
    inexist_gjshq = list(set(dbf_gjshq) ^ set(exist_gjshq))
    log.info("%s%d%s" % ("dbf导入gjshq条数：", len(dbf_gjshq), "条"))
    log.info("%s%d%s" % ("t_MarketData存在：", len(exist_gjshq), "条"))
    log.info("%s%d%s" % ("t_MarketData不存在：", len(inexist_gjshq), "条"))

    # 写入t_MarketData
    sql_gjshq = """INSERT INTO siminfo.t_MarketData (
                                SettlementGroupID,
                                LastPrice,
                                PreSettlementPrice,
                                PreClosePrice,
                                PreOpenInterest,
                                OpenPrice,
                                HighestPrice,
                                LowestPrice,
                                Volume,
                                Turnover,
                                OpenInterest,
                                ClosePrice,
                                SettlementPrice,
                                UpperLimitPrice,
                                LowerLimitPrice,
                                PreDelta,
                                CurrDelta,
                                UpdateTime,
                                UpdateMillisec,
                                InstrumentID
                           )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    sql_params = []
    for hq in gjshq_dbf:
        if hq['HYDM'] in inexist_gjshq:
            sql_params.append((param['SettlementGroupID'],
                               None, None, None, 0, hq['KPJ'], hq['ZGJ'], hq['ZDJ'], hq['CJL'],
                               hq['CJJE'], None, hq['SPJ'], None, None, None, None, None, None, None, hq['HYDM']
                               ))
    mysql.executemany(sql_gjshq, sql_params)


def __checkFile():
    env_dist = os.environ
    # 判断环境变量是否存在HOME配置
    if 'HOME' not in env_dist:
        log.debug("HOME not in environment variable")
        return None
    # 获取文件路径
    catalog = env_dist['HOME']
    now = datetime.datetime.now().strftime("%Y%m%d")
    catalog = '%s%s%s%s%s' % (catalog, os.path.sep, 'sim_data', os.path.sep, now)
    par_futures = '%s%s%s%s%s' % (catalog, os.path.sep, futures_filename, now, '.dbf')
    gjshq = '%s%s%s%s%s' % (catalog, os.path.sep, gjshq_filename, now, '.dbf')

    # 判断par_futuresYYYYMMDD.dbf文件是否存在
    if not os.path.exists(par_futures):
        log.debug("%s%s" % (par_futures, " is not exists"))
        return None
    # 判断gjshqYYYYMMDD.dbf文件是否存在
    if not os.path.exists(gjshq):
        log.debug("%s%s" % (gjshq, " is not exists"))
        return None
    # 读取DBF文件
    return __loadDBF(futures=par_futures, gjshq=gjshq)


def __loadDBF(**par):
    # 加载 par_futures 数据
    stock = DBF(filename=par['futures'], encoding='GBK')
    stock.load()
    # 加载 gjshq 数据
    info = DBF(filename=par['gjshq'], encoding='GBK')
    info.load()
    return stock.records, info.records
