# -*- coding: UTF-8 -*-

import os
import datetime

from utils.logger.log import log
from dbfread import DBF

futures_filename = "PAR_FUTURES"
gjshq_filename = "GJSHQ"

log = log.get_logger('trans_future')


def transform(param, mysql):
    # 读取dbf文件
    dbfs = __checkFile()
    if dbfs is None:
        return
    # ===========处理futures_dbf写入t_Instrument表==============
    __t_Instrument(mysql=mysql, dbf=dbfs[0], param=param)

    # ===========处理gjshq_dbf写入t_MarketData表 ==============
    __t_MarketData(mysql=mysql, dbf=dbfs[1], param=param)

    # ===========判断并写入t_InstrumentProperty表(如果存在不写入)==============
    __t_InstrumentProperty(mysql=mysql, dbf=dbfs[0], param=param)


# 读取处理PAR_FUTURES文件
def __t_Instrument(mysql, dbf, param):
    futures_dbf = dbf
    # 判断合约是否已存在
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

    # 不存在插入记录
    sql_insert_futures = """INSERT INTO siminfo.t_Instrument (
                               SettlementGroupID,ProductID,
                               ProductGroupID,UnderlyingInstrID,
                               ProductClass,PositionType,
                               StrikePrice,OptionsType,
                               VolumeMultiple,UnderlyingMultiple,
                               InstrumentID,InstrumentName,
                               DeliveryYear,DeliveryMonth,AdvanceMonth
                           )SELECT %s,t1.ProductID,t1.ProductGroupID,t1.ProductID,t1.ProductClass,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
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
            sql_insert_params.append((param['SettlementGroupID'], "2", None, "0",
                                      future['JYDW'], 1, future['ZQDM'], future['ZQMC'],
                                      2099, 12, "012", future['JYPZ'], ProductClass))
        if future['ZQDM'] in exist_futures:
            sql_update_params.append((future['ZQMC'], future['JYDW'], future['ZQDM'], param['SettlementGroupID']))

    mysql.executemany(sql_insert_futures, sql_insert_params)
    mysql.executemany(sql_update_futures, sql_update_params)


# 读取处理GJSHQ文件
def __t_MarketData(mysql, dbf, param):
    gjshq_dbf = dbf
    # 判断贵金属行情是否已存在
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
            sql_insert_params.append((param['SettlementGroupID'],
                                      None, None, None, 0, hq['KPJ'], hq['ZGJ'], hq['ZDJ'], hq['CJL'],
                                      hq['CJJE'], None, hq['SPJ'], hq['JQPJJ'], None, None, None, None, None, None,
                                      hq['HYDM']))
        if hq['HYDM'] in exist_gjshq:
            sql_update_params.append((hq['KPJ'], hq['ZGJ'], hq['ZDJ'], hq['CJL'], hq['CJJE'], hq['SPJ'], hq['JQPJJ'],
                                      param['SettlementGroupID'], hq['HYDM']))
    mysql.executemany(sql_insert_gjshq, sql_insert_params)
    mysql.executemany(sql_update_gjshq, sql_update_params)


# 写入t_InstrumentProperty
def __t_InstrumentProperty(mysql, dbf, param):
    dbf_futures = []
    exist_futures = []
    sql_Property = " SELECT InstrumentID " + \
                   " FROM t_InstrumentProperty " + \
                   " WHERE SettlementGroupID = '" + param['SettlementGroupID'] + "'" + \
                   " AND InstrumentID in ("
    for stock in dbf:
        dbf_futures.append(stock['ZQDM'])
        sql_Property = sql_Property + "'" + stock['ZQDM'] + "',"
    sql_Property = sql_Property[0:-1] + ")"

    # 查询存在数据
    for future in mysql.select(sql_Property):
        exist_futures.append(str(future[0]))

    # 获取差集
    inexist_futures = list(set(dbf_futures) ^ set(exist_futures))
    log.info("%s%d%s" % ("future导入t_InstrumentProperty存在：", len(exist_futures), "条"))
    log.info("%s%d%s" % ("future导入t_InstrumentProperty不存在：", len(inexist_futures), "条"))

    # 插入不存在记录
    sql_Property = """INSERT INTO t_InstrumentProperty (
                                     SettlementGroupID,CreateDate,OpenDate,ExpireDate,StartDelivDate,
                                     EndDelivDate,BasisPrice,MaxMarketOrderVolume,MinMarketOrderVolume,
                                     MaxLimitOrderVolume,MinLimitOrderVolume,PriceTick,
                                     AllowDelivPersonOpen,InstrumentID,InstLifePhase
                                     )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    sql_params = []
    for stock in dbf:
        if stock['ZQDM'] in inexist_futures:
            sql_params.append((param['SettlementGroupID'], stock['SSRQ'], stock['SSRQ'],
                               '99991219', '99991219', '99991219', 0, 1000000, 100,
                               1000000, 100, 0.01, 0, stock['ZQDM'], 1))
    mysql.executemany(sql_Property, sql_params)

def __checkFile():
    env_dist = os.environ
    # 判断环境变量是否存在HOME配置
    if 'HOME' not in env_dist:
        log.error("HOME not in environment variable")
        return None
    # 获取文件路径
    catalog = env_dist['HOME']
    now = datetime.datetime.now().strftime("%Y%m%d")
    catalog = '%s%s%s%s%s' % (catalog, os.path.sep, 'sim_data', os.path.sep, now)
    par_futures = '%s%s%s%s%s' % (catalog, os.path.sep, futures_filename, now, '.dbf')
    gjshq = '%s%s%s%s%s' % (catalog, os.path.sep, gjshq_filename, now, '.dbf')

    # 判断par_futuresYYYYMMDD.dbf文件是否存在
    if not os.path.exists(par_futures):
        log.error("%s%s" % (par_futures, " is not exists"))
        return None
    # 判断gjshqYYYYMMDD.dbf文件是否存在
    if not os.path.exists(gjshq):
        log.error("%s%s" % (gjshq, " is not exists"))
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
