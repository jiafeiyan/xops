# -*- coding: UTF-8 -*-

import os
import datetime
import json

from utils import log
from utils import parse_conf_args
from utils import Configuration
from utils import mysql
from etf_entity import etfVO


class trans_etfinfo:
    def __init__(self, context, configs):
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="trans_future", configs=log_conf)
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

        # ===========判断并写入t_InstrumentProperty表(未更新)==============
        self.__t_InstrumentProperty(mysqlDB=mysqlDB, etf_list=etf_list)

        # ===========处理stock_dbf写入t_MarginRate表(未更新)==============
        self.__t_MarginRate(mysqlDB=mysqlDB, etf_list=etf_list)

        # ===========处理stock_dbf写入t_MarginRateDetail表==============
        self.__t_MarginRateDetail(mysqlDB=mysqlDB, etf_list=etf_list)

    # 读取处理reff03文件
    def __t_Instrument(self, mysqlDB, etf_list):
        # 判断合约是否已存在
        all_etf = []
        exist_etf = []
        sql_etf = " SELECT InstrumentID " + \
                  " FROM siminfo.t_Instrument " + \
                  " WHERE (InstrumentID, SettlementGroupID) in ("
        for etf in etf_list:
            all_etf.append(etf.SecurityID)
            sql_values = "('" + etf.SecurityID + "', '" + self.SettlementGroupID + "') "
            sql_etf = sql_etf + sql_values + ","
        sql_etf = sql_etf[0:-1] + ")"

        # 查询存在数据
        for etf in mysqlDB.select(sql_etf):
            exist_etf.append(str(etf[0]))

        # 获取差集
        inexist_etf = list(set(all_etf) ^ set(exist_etf))
        self.logger.info("%s%d%s" % ("dbf导入etf条数：", len(all_etf), "条"))
        self.logger.info("%s%d%s" % ("t_Instrument中etf存在：", len(exist_etf), "条"))
        self.logger.info("%s%d%s" % ("t_Instrument中etf不存在：", len(inexist_etf), "条"))

        # 不存在插入记录
        sql_insert_etf = """INSERT INTO siminfo.t_Instrument (
                               SettlementGroupID,ProductID,
                               ProductGroupID,UnderlyingInstrID,
                               ProductClass,PositionType,
                               StrikePrice,OptionsType,
                               VolumeMultiple,UnderlyingMultiple,
                               InstrumentID,InstrumentName,
                               DeliveryYear,DeliveryMonth,AdvanceMonth
                          )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        # 存在更新记录
        sql_update_etf = """UPDATE siminfo.t_Instrument
                                    SET InstrumentName=%s,StrikePrice=%s,DeliveryYear=%s,
                                        DeliveryMonth=%s,OptionsType=%s
                                    WHERE InstrumentID = %s
                                    AND SettlementGroupID = %s"""
        sql_insert_params = []
        sql_update_params = []
        for etf in etf_list:
            if etf.SecurityID in inexist_etf:
                ProductID = 'ETF'
                ProductGroupID = 'ZQ'
                if str(etf.CallOrPut) == 'C':
                    OptionsType = '1'
                elif str(etf.CallOrPut) == 'P':
                    OptionsType = '2'
                sql_insert_params.append((self.SettlementGroupID,
                                          ProductID,
                                          ProductGroupID,
                                          ProductID,
                                          "2", "2", etf.ExercisePrice, OptionsType,
                                          1, 1, etf.SecurityID, etf.ContractSymbol,
                                          etf.DeliveryDate[0:4], etf.DeliveryDate[4:6], "012"))
                continue
            if etf.SecurityID in exist_etf:
                if str(etf.CallOrPut) == 'C':
                    OptionsType = '1'
                elif str(etf.CallOrPut) == 'P':
                    OptionsType = '2'
                sql_update_params.append((etf.ContractSymbol, etf.ExercisePrice,
                                          etf.DeliveryDate[0:4], etf.DeliveryDate[4:6], OptionsType,
                                          etf.SecurityID, self.SettlementGroupID
                                          ))
        mysqlDB.executemany(sql_insert_etf, sql_insert_params)
        mysqlDB.executemany(sql_update_etf, sql_update_params)

    # 写入t_InstrumentProperty
    def __t_InstrumentProperty(self, mysqlDB, etf_list):
        # 判断合约是否已存在
        all_etf = []
        exist_etf = []
        sql_etf = " SELECT InstrumentID " + \
                  " FROM siminfo.t_InstrumentProperty " + \
                  " WHERE (InstrumentID, SettlementGroupID) in ("
        for etf in etf_list:
            all_etf.append(etf.SecurityID)
            sql_values = "('" + etf.SecurityID + "', '" + self.SettlementGroupID + "') "
            sql_etf = sql_etf + sql_values + ","
        sql_etf = sql_etf[0:-1] + ")"

        # 查询存在数据
        for etf in mysqlDB.select(sql_etf):
            exist_etf.append(str(etf[0]))

        # 获取差集
        inexist_etf = list(set(all_etf) ^ set(exist_etf))

        self.logger.info("%s%d%s" % ("etf导入t_InstrumentProperty存在：", len(exist_etf), "条"))
        self.logger.info("%s%d%s" % ("etf导入t_InstrumentProperty不存在：", len(inexist_etf), "条"))

        # 插入不存在记录
        sql_Property = """INSERT INTO siminfo.t_InstrumentProperty (
                                      SettlementGroupID,CreateDate,OpenDate,ExpireDate,StartDelivDate,
                                      EndDelivDate,BasisPrice,MaxMarketOrderVolume,MinMarketOrderVolume,
                                      MaxLimitOrderVolume,MinLimitOrderVolume,PriceTick,
                                      AllowDelivPersonOpen,InstrumentID,InstLifePhase
                                      )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        sql_params = []
        for etf in etf_list:
            if etf.SecurityID in inexist_etf:
                sql_params.append((self.SettlementGroupID, '99991219', '99991219', etf.ExpireDate, etf.StartDate,
                                   etf.EndDate, 0, etf.MktOrdMaxFloor, etf.MktOrdMinFloor,
                                   etf.LmtOrdMaxFloor, etf.LmtOrdMinFloor, etf.TickSize,
                                   0, etf.SecurityID, 1))
        mysqlDB.executemany(sql_Property, sql_params)

    # 写入t_MarginRate
    def __t_MarginRate(self, mysqlDB, etf_list):
        # 判断合约是否已存在
        all_etf = []
        exist_rate = []
        # 获取模板文件
        template = self.__loadJSON(tableName='t_MarginRate')
        if template is None:
            self.logger.error("t_MarginRate template is None")
            return
        sql_marginrate = " SELECT InstrumentID " + \
                         " FROM siminfo.t_MarginRate " + \
                         " WHERE (SettlementGroupID, MarginCalcID, InstrumentID, ParticipantID) in ("
        for etf in etf_list:
            all_etf.append(etf.SecurityID)
            SGID = self.SettlementGroupID
            sql_values = "('" + SGID + \
                         "', '" + template[SGID][1] + \
                         "', '" + etf.SecurityID + \
                         "', '" + template[SGID][3] + \
                         "') "
            sql_marginrate = sql_marginrate + sql_values + ","
        sql_marginrate = sql_marginrate[0:-1] + ")"

        for etf in mysqlDB.select(sql_marginrate):
            exist_rate.append(str(etf[0]))

        # 获取差集
        inexist_rate = list(set(all_etf) ^ set(exist_rate))
        self.logger.info("%s%d%s" % ("etf导入t_MarginRate存在：", len(exist_rate), "个合约"))
        self.logger.info("%s%d%s" % ("etf导入t_MarginRate不存在：", len(inexist_rate), "个合约"))

        # 不存在插入记录
        sql_insert_rate = """INSERT INTO siminfo.t_MarginRate (
                                        SettlementGroupID,
                                        MarginCalcID,
                                        InstrumentID,
                                        ParticipantID
                                    ) VALUES (%s,%s,%s,%s)"""
        sql_insert_params = []
        for etf in etf_list:
            if etf.SecurityID in inexist_rate:
                SGID = self.SettlementGroupID
                sql_insert_params.append((SGID, template[SGID][1], etf.SecurityID, template[SGID][3]))
        mysqlDB.executemany(sql_insert_rate, sql_insert_params)

    # 写入t_MarginRateDetail
    def __t_MarginRateDetail(self, mysqlDB, etf_list):
        # 判断合约是否已存在
        all_etf = []
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
        for etf in etf_list:
            all_etf.append(etf.SecurityID)
            SGID = self.SettlementGroupID
            sql_values = "('" + SGID + \
                         "', '" + template[SGID][1] + \
                         "', '" + template[SGID][2] + \
                         "', '" + etf.SecurityID + \
                         "', '" + template[SGID][7] + \
                         "', '" + template[SGID][8] + \
                         "') "
            sql_marginratedetail = sql_marginratedetail + sql_values + ","
        sql_marginratedetail = sql_marginratedetail[0:-1] + ") "

        for etf in mysqlDB.select(sql_marginratedetail):
            exist_detail.append(str(etf[0]))

        # 获取差集
        inexist_detail = list(set(all_etf) ^ set(exist_detail))
        self.logger.info("%s%d%s" % ("etf导入t_MarginRateDetail存在：", len(exist_detail), "个合约"))
        self.logger.info("%s%d%s" % ("etf导入t_MarginRateDetail不存在：", len(inexist_detail), "个合约"))

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
        for etf in etf_list:
            SGID = self.SettlementGroupID
            # 插入记录
            if etf.SecurityID in inexist_detail:
                sql_insert_params.append((SGID, template[SGID][1], template[SGID][2], template[SGID][3],
                                          template[SGID][4], etf.MarginUnit, etf.SecurityID,
                                          template[SGID][7], template[SGID][8]))
                continue
            # 更新记录
            if etf.SecurityID in exist_detail:
                sql_update_params.append((template[SGID][3], template[SGID][4], etf.MarginUnit,
                                          SGID, template[SGID][1], template[SGID][2],
                                          etf.SecurityID, template[SGID][7], template[SGID][8]))
        mysqlDB.executemany(sql_insert_detail, sql_insert_params)
        mysqlDB.executemany(sql_update_detail, sql_update_params)

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
        path = "%s%s%s%s" % (self.initTemplate['initTemplate'], os.path.sep, tableName, ".json")
        if not os.path.exists(path):
            self.logger.error("文件" + tableName + ".json不存在")
            return None
        f = open(path)
        return json.load(f)


if __name__ == '__main__':
    base_dir, config_names, config_files = parse_conf_args(__file__, config_names=["mysql", "init"])
    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)
    # 启动etf脚本
    trans_etfinfo(context=context, configs=conf)
