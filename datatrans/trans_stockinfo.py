# -*- coding: UTF-8 -*-

import os
import datetime

from utils.logger.log import log
from dbfread import DBF

log = log.get_logger('trans_stockinfo', console_level='DEBUG')


def transform(param, mysql):
    dbfs = __checkFile()
    if dbfs is None:
        return

    # ================================处理stock_dbf======================================
    stock_dbf = dbfs[0]
    # 判断合约是否已存在，存在不执行
    dbf_stock = []
    exist_stock = []
    sql_Instrument = " SELECT InstrumentID " + \
                     " FROM siminfo.t_Instrument " + \
                     " WHERE SettlementGroupID = '" + param['SettlementGroupID'] + "'" + \
                     " AND InstrumentID in ("
    for stock in stock_dbf:
        dbf_stock.append(stock['ZQDM'])
        sql_Instrument = sql_Instrument + "'" + stock['ZQDM'] + "',"
    sql_Instrument = sql_Instrument[0:-1] + ")"

    # 查询存在数据
    for stock in mysql.select(sql_Instrument):
        exist_stock.append(str(stock[0]))

    # 获取差集
    inexist_stock = list(set(dbf_stock) ^ set(exist_stock))
    log.info("%s%d%s" % ("dbf导入stock条数：", len(dbf_stock), "条"))
    log.info("%s%d%s" % ("t_Instrument存在：", len(exist_stock), "条"))
    log.info("%s%d%s" % ("t_Instrument不存在：", len(inexist_stock), "条"))

    # 写入t_Instrument
    sql_Instrument = """INSERT INTO siminfo.t_Instrument (
                            SettlementGroupID,ProductID,
                            ProductGroupID,UnderlyingInstrID,
                            ProductClass,PositionType,
                            StrikePrice,OptionsType,
                            VolumeMultiple,UnderlyingMultiple,
                            InstrumentID,InstrumentName,
                            DeliveryYear,DeliveryMonth,AdvanceMonth
                        )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    sql_params = []
    for stock in stock_dbf:
        if stock['ZQDM'] in inexist_stock:
            sql_params.append((param['SettlementGroupID'],
                               param['ProductID'],
                               param['ProductGroupID'],
                               param['ProductID'],
                               "4", "2", 0, "0",
                               param['VolumeMultiple'],
                               1, stock['ZQDM'], stock['ZQJC'],
                               2099, 12, "012"
                               ))
    mysql.executemany(sql_Instrument, sql_params)

    # ================================处理info_dbf======================================
    info_dbf = dbfs[1]
    # 判断权益信息是否已存在，存在不执行
    dbf_qy_info = []
    exist_qy_info = []
    sql_qy_info = " SELECT SecurityID, SecurityType, SecurityMarketID,  ProfitType" + \
                  " FROM siminfo.t_SecurityProfit " + \
                  " WHERE SettlementGroupID = '" + param['SettlementGroupID'] + "'" + \
                  " AND (SecurityID, SecurityType, SecurityMarketID, ProfitType) in ("
    for info in info_dbf:
        dbf_qy_info.append((info['ZQDM'], info['ZQLX'], info['SCDM'], info['QYKIND']))
        sql_values = "('" + info['ZQDM'] + "', '" + info['ZQLX'] + "', '" + info['SCDM'] + "', '" + info[
            'QYKIND'] + "')"
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

    # 写入t_SecurityProfit
    sql_qy_info = """INSERT INTO siminfo.t_SecurityProfit (
                            SettlementGroupID,SecurityID,
                            SecurityType,SecurityMarketID,
                            ProfitType,DJDate,
                            CQDate,EndDate,
                            DZDate,BeforeRate,
                            AfterRate,Price
                        )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    sql_params = []
    for info in info_dbf:
        if (info['ZQDM'], info['ZQLX'], info['SCDM'], info['QYKIND']) in inexist_qy_info:
            sql_params.append((param['SettlementGroupID'], info['ZQDM'],
                               info['ZQLX'], info['SCDM'], info['QYKIND'],
                               info['DJDATE'], info['CQDATE'], info['ENDDATE'],
                               info['DZDATE'], info['BEFORERATE'],
                               info['AFTERRATE'], info['PRICE']))
    mysql.executemany(sql_qy_info, sql_params)


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
    par_stock = '%s%s%s%s%s' % (catalog, os.path.sep, 'PAR_STOCK', now, '.dbf')
    par_qy_info = '%s%s%s%s%s' % (catalog, os.path.sep, 'PAR_QY_INFO', now, '.dbf')

    # 判断PAR_STOCKYYYYMMDD.dbf文件是否存在
    if not os.path.exists(par_stock):
        log.debug("%s%s" % (par_stock, " is not exists"))
        return None
    # 判断PAR_QY_INFOYYYYMMDD.dbf文件是否存在
    if not os.path.exists(par_qy_info):
        log.debug("%s%s" % (par_qy_info, " is not exists"))
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
