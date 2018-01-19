# -*- coding: UTF-8 -*-

import os
import datetime
import json

from utils import parse_args
from utils import load
from utils import mysql
from utils import log
from etf_entity import etfVO


class trans_etfinfo:
    def __init__(self, configs):
        if "Log" in configs:
            self.logger = log.get_logger(category="trans_future",
                                         file_Path=configs["Log"]["file_path"],
                                         console_level=configs["Log"]["console_level"],
                                         file_level=configs["Log"]["file_level"])
        else:
            self.logger = log.get_logger(category="trans_future")

        self.etf_filename = "reff03"
        self.SettlementGroupID = "SG07"
        self.configs = configs
        self.__transform()

    def __transform(self):
        etf_list = self.__check_file()
        if etf_list is None:
            return

        mysqlDB = self.configs['db_instance']
        # ===========处理etf_txt写入t_Instrument表==============
        self.__t_Instrument(mysqlDB=mysqlDB, etf_list=etf_list)
        # ===========判断并写入t_InstrumentProperty表(如果存在不写入)==============
        self.__t_InstrumentProperty(mysqlDB=mysqlDB, etf_list=etf_list)

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
        sql_update_etf = """UPDATE t_Instrument
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
                  " FROM t_InstrumentProperty " + \
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
        sql_Property = """INSERT INTO t_InstrumentProperty (
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


if __name__ == '__main__':
    args = parse_args()

    # 读取参数文件
    conf = load(args.conf)

    # 建立mysql数据库连接
    mysql_instance = mysql(configs=conf)
    conf["db_instance"] = mysql_instance

    # 启动future脚本
    trans_etfinfo(conf)
