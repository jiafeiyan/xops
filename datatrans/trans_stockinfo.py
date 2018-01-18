# -*- coding: UTF-8 -*-

import os
import datetime
import json

from utils.logger.log import log
from dbfread import DBF

stock_filename = "PAR_STOCK"
qy_info_filename = "PAR_QY_INFO"

log = log.get_logger('trans_stock')

# 结算组ID和交易所对应关系
__self_conf = {
    "1": "SG01",
    "2": "SG02",
    "3": "SG99",
    "4": "SG98"
}


def transform(mysql, param=None, config=None):
    # 读取dbf文件
    dbfs = __checkFile()
    if dbfs is None:
        return
    # ===========处理stock_dbf写入t_Instrument表==============
    __t_Instrument(mysql=mysql, dbf=dbfs[0])

    # ===========处理futures_dbf写入t_TradingSegmentAttr表==============
    __t_TradingSegmentAttr(mysql=mysql, dbf=dbfs[0], config=config)

    # ===========处理info_dbf写入t_SecurityProfit表===========
    __t_SecurityProfit(mysql=mysql, dbf=dbfs[1])

    # ===========判断并写入t_InstrumentProperty表(如果存在不写入)==============
    __t_InstrumentProperty(mysql=mysql, dbf=dbfs[0])


# 读取处理PAR_STOCK文件
def __t_Instrument(mysql, dbf, param=None):
    stock_dbf = dbf
    # 判断合约是否已存在
    dbf_stock = []
    exist_stock = []
    sql_Instrument = " SELECT InstrumentID " + \
                     " FROM siminfo.t_Instrument " + \
                     " WHERE (InstrumentID, SettlementGroupID) in ("
    for stock in stock_dbf:
        dbf_stock.append(stock['ZQDM'])
        sql_values = "('" + stock['ZQDM'] + "', '" + __self_conf[str(stock['SCDM'])] + "') "
        sql_Instrument = sql_Instrument + sql_values + ","
    sql_Instrument = sql_Instrument[0:-1] + ")"

    # 查询存在数据
    for stock in mysql.select(sql_Instrument):
        exist_stock.append(str(stock[0]))

    # 获取差集
    inexist_stock = list(set(dbf_stock) ^ set(exist_stock))
    log.info("%s%d%s" % ("dbf导入stock条数：", len(dbf_stock), "条"))
    log.info("%s%d%s" % ("t_Instrument存在：", len(exist_stock), "条"))
    log.info("%s%d%s" % ("t_Instrument不存在：", len(inexist_stock), "条"))

    # 不存在插入记录
    sql_insert_Instrument = """INSERT INTO siminfo.t_Instrument (
                               SettlementGroupID,ProductID,
                               ProductGroupID,UnderlyingInstrID,
                               ProductClass,PositionType,
                               StrikePrice,OptionsType,
                               VolumeMultiple,UnderlyingMultiple,
                               InstrumentID,InstrumentName,
                               DeliveryYear,DeliveryMonth,AdvanceMonth
                           )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    # 存在更新记录
    sql_update_Instrument = """UPDATE t_Instrument
                                   SET InstrumentName = %s
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
            sql_insert_params.append((__self_conf[str(stock['SCDM'])],
                                      ProductID,
                                      ProductGroupID,
                                      ProductID,
                                      "4", "2", None, "0",
                                      1, 1, stock['ZQDM'], stock['ZQJC'],
                                      2099, 12, "012"))
            continue
        if stock['ZQDM'] in exist_stock:
            sql_update_params.append((stock['ZQJC'], stock['ZQDM'], __self_conf[str(stock['SCDM'])]))
    mysql.executemany(sql_insert_Instrument, sql_insert_params)
    mysql.executemany(sql_update_Instrument, sql_update_params)


# 读取处理PAR_QY_INFO文件
def __t_SecurityProfit(mysql, dbf, param=None):
    info_dbf = dbf
    # 判断权益信息是否已存在
    dbf_qy_info = []
    exist_qy_info = []
    sql_qy_info = " SELECT SecurityID, SecurityType, SecurityMarketID,  ProfitType" + \
                  " FROM siminfo.t_SecurityProfit " + \
                  " WHERE (SecurityID, SecurityType, SecurityMarketID, ProfitType, SettlementGroupID) in ("
    for info in info_dbf:
        dbf_qy_info.append((info['ZQDM'], info['ZQLX'], info['SCDM'], info['QYKIND']))
        sql_values = "('" + info['ZQDM'] + "', '" + info['ZQLX'] + "', '" + info['SCDM'] + "', '" + info['QYKIND'] + \
                     "', '" + __self_conf[str(info['SCDM'])] + "') "
        sql_qy_info = sql_qy_info + sql_values + ","
    sql_qy_info = sql_qy_info[0:-1] + ")"

    # 查询存在数据
    for info in mysql.select(sql_qy_info):
        exist_qy_info.append((str(info[0]), str(info[1]), str(info[2]), str(info[3])))

    # 获取差集
    inexist_qy_info = list(set(dbf_qy_info) ^ set(exist_qy_info))
    log.info("%s%d%s" % ("dbf导入qy_info条数：", len(dbf_qy_info), "条"))
    log.info("%s%d%s" % ("t_SecurityProfit存在：", len(exist_qy_info), "条"))
    log.info("%s%d%s" % ("t_SecurityProfit不存在：", len(inexist_qy_info), "条"))

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
    sql_update_qy_info = """UPDATE t_SecurityProfit
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
            sql_insert_params.append((__self_conf[str(info['SCDM'])], info['ZQDM'],
                                      info['ZQLX'], info['SCDM'], info['QYKIND'],
                                      info['DJDATE'], info['CQDATE'], info['ENDDATE'],
                                      info['DZDATE'], info['BEFORERATE'],
                                      info['AFTERRATE'], info['PRICE']))
            continue
        if (info['ZQDM'], info['ZQLX'], info['SCDM'], info['QYKIND']) in exist_qy_info:
            sql_update_params.append((info['DJDATE'], info['CQDATE'], info['ENDDATE'],
                                      info['DZDATE'], info['BEFORERATE'],
                                      info['AFTERRATE'], info['PRICE'],
                                      info['ZQDM'], __self_conf[str(info['SCDM'])],
                                      info['ZQLX'], info['SCDM'], info['QYKIND']))
    mysql.executemany(sql_insert_qy_info, sql_insert_params)
    mysql.executemany(sql_update_qy_info, sql_update_params)


# 写入t_InstrumentProperty
def __t_InstrumentProperty(mysql, dbf, param=None):
    dbf_stock = []
    exist_stock = []
    sql_Property = " SELECT InstrumentID " + \
                   " FROM t_InstrumentProperty " + \
                   " WHERE (InstrumentID, SettlementGroupID) in ("
    for stock in dbf:
        dbf_stock.append(stock['ZQDM'])
        sql_values = "('" + stock['ZQDM'] + "', '" + __self_conf[str(stock['SCDM'])] + "') "
        sql_Property = sql_Property + sql_values + ","
    sql_Property = sql_Property[0:-1] + ")"

    # 查询存在数据
    for stock in mysql.select(sql_Property):
        exist_stock.append(str(stock[0]))

    # 获取差集
    inexist_stock = list(set(dbf_stock) ^ set(exist_stock))

    log.info("%s%d%s" % ("stock导入t_InstrumentProperty存在：", len(exist_stock), "条"))
    log.info("%s%d%s" % ("stock导入t_InstrumentProperty不存在：", len(inexist_stock), "条"))

    # 插入不存在记录
    sql_Property = """INSERT INTO t_InstrumentProperty (
                                  SettlementGroupID,CreateDate,OpenDate,ExpireDate,StartDelivDate,
                                  EndDelivDate,BasisPrice,MaxMarketOrderVolume,MinMarketOrderVolume,
                                  MaxLimitOrderVolume,MinLimitOrderVolume,PriceTick,
                                  AllowDelivPersonOpen,InstrumentID,InstLifePhase
                                  )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    sql_params = []
    for stock in dbf:
        if stock['ZQDM'] in inexist_stock:
            sql_params.append((__self_conf[str(stock['SCDM'])], stock['FXRQ'], stock['SSRQ'],
                               '99991219', '99991219', '99991219', 0, 1000000, 100,
                               1000000, 100, 0.01, 0, stock['ZQDM'], 1))
    mysql.executemany(sql_Property, sql_params)


def __t_TradingSegmentAttr(mysql, dbf, config, param=None):
    # 判断合约是否已存在
    dbf_stock = []
    exist_segment = []
    sql_segment = " SELECT InstrumentID " + \
                  " FROM siminfo.t_TradingSegmentAttr " + \
                  " WHERE (InstrumentID, SettlementGroupID) in ("
    for stock in dbf:
        dbf_stock.append(stock['ZQDM'])
        sql_values = "('" + stock['ZQDM'] + "', '" + __self_conf[str(stock['SCDM'])] + "') "
        sql_segment = sql_segment + sql_values + ","
    sql_segment = sql_segment[0:-1] + ") GROUP BY InstrumentID"

    # 查询存在数据
    for stock in mysql.select(sql_segment):
        exist_segment.append(str(stock[0]))

    # 获取差集
    inexist_segment = list(set(dbf_stock) ^ set(exist_segment))
    log.info("%s%d%s" % ("future导入t_TradingSegmentAttr存在：", len(exist_segment), "个合约"))
    log.info("%s%d%s" % ("future导入t_TradingSegmentAttr不存在：", len(inexist_segment), "个合约"))

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
    SegmentAttr = __loadJSON(tableName='t_TradingSegmentAttr', config=config)
    if SegmentAttr is None:
        return
    for stock in dbf:
        SGID = __self_conf[str(stock['SCDM'])]
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
    mysql.executemany(sql_insert_segment, sql_insert_params)
    mysql.executemany(sql_update_segment, sql_update_params)

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
    par_stock = '%s%s%s%s%s' % (catalog, os.path.sep, stock_filename, now, '.dbf')
    par_qy_info = '%s%s%s%s%s' % (catalog, os.path.sep, qy_info_filename, now, '.dbf')

    # 判断PAR_STOCKYYYYMMDD.dbf文件是否存在
    if not os.path.exists(par_stock):
        log.error("%s%s" % (par_stock, " is not exists"))
        return None
    # 判断PAR_QY_INFOYYYYMMDD.dbf文件是否存在
    if not os.path.exists(par_qy_info):
        log.error("%s%s" % (par_qy_info, " is not exists"))
        return None
    # 读取DBF文件
    return __loadDBF(stock=par_stock, info=par_qy_info)


def __loadDBF(**par):
    # 加载 PAR_STOCK 数据
    stock = DBF(filename=par['stock'], encoding='GBK')
    stock.load()
    # 加载 PAR_QY_INFO 数据
    info = DBF(filename=par['info'], encoding='GBK')
    info.load()
    return stock.records, info.records


# 主要读取TradingSegmentAttr配置数据
def __loadJSON(tableName, config):
    path = "%s%s%s%s" % (config["Init"]["path"], os.path.sep, tableName, ".json")
    if not os.path.exists(path):
        log.error("文件" + tableName + ".json不存在")
        return None
    f = open(path)
    return json.load(f)
