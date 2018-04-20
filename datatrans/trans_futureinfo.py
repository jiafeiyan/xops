# -*- coding: UTF-8 -*-

import os
import datetime
import json
import csv

from utils import parse_conf_args, Configuration, path, mysql, log


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
        self.file_instrument = "future_instrument.csv"
        self.file_marketdata = "future_depthmarketdata.csv"
        self.file_product = "future_product.csv"
        self.file_marginrate = "future_marginrate.csv"
        # 交易所和结算组对应关系
        self.exchange_conf = self.__get_exchange()
        self.__transform()

    # 通过交易所查询结算组代码
    def __get_exchange(self):
        sql = """select ExchangeID, t.SettlementGroupID from siminfo.t_settlementgroup t, siminfo.t_tradesystemsettlementgroup t1
                  where t.SettlementGroupID = t1.SettlementGroupID and t1.TradeSystemID = %s and t.SettlementGroupID != %s"""
        res = self.mysqlDB.select(sql, ('0002', 'SG09'))
        exchange_conf = dict()
        for row in res:
            exchange_conf.update({str(row[0]): str(row[1])})
        return exchange_conf

    def __transform(self):
        mysqlDB = self.mysqlDB
        # 查询当前交易日
        sql = """SELECT tradingday FROM siminfo.t_tradesystemtradingday WHERE tradesystemid = %s"""
        fc = mysqlDB.select(sql, ('0002',))
        current_trading_day = fc[0][0]
        self.TradingDay = current_trading_day
        self.logger.info("[trans_futureinfo] current_trading_day = %s" % current_trading_day)

        # 读取csv文件
        csvs = self.__check_file()
        if csvs is None:
            return

        if csvs[0] is not None:
            # ===========处理instrument.csv写入t_Instrument表==============
            self.__t_Instrument(mysqlDB=mysqlDB, csv_file=csvs[0])

            # ===========处理instrument.csv写入t_TradingSegmentAttr表==============
            self.__t_TradingSegmentAttr(mysqlDB=mysqlDB, csv_file=csvs[0])

            # ===========处理instrument.csv写入t_MarginRate表==============
            self.__t_MarginRate(mysqlDB=mysqlDB, csv_file=csvs[0])

            # ===========判断并写入t_InstrumentProperty表==============
            self.__t_InstrumentProperty(mysqlDB=mysqlDB, csv_file=csvs[0])

            # ===========判断并写入t_TransFeeRateDetail表==============
            self.__t_TransFeeRateDetail(mysqlDB=mysqlDB, csv_file=csvs[0])

        if csvs[1] is not None and csvs[3] is not None:
            # ===========处理instrument.csv写入t_MarginRateDetail表==============
            self.__t_MarginRateDetail(mysqlDB, csvs[1], csvs[3])

        if csvs[2] is not None:
            # ===========写入t_MarketData表 ==============
            self.__t_MarketData(mysqlDB=mysqlDB, csv_file=csvs[2])

            # ===========写入t_PriceBanding表==============
            self.__t_PriceBanding(mysqlDB=mysqlDB, csv_file=csvs[2])

    def __t_Instrument(self, mysqlDB, csv_file):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            # 删除期货交易所下所有数据
            cursor.execute("delete from siminfo.t_Instrument where SettlementGroupID in "
                           + str(tuple([str(i) for i in self.exchange_conf.values()])))
            sql_insert_futures = """INSERT INTO siminfo.t_Instrument(
                                               SettlementGroupID,ProductID,
                                               ProductGroupID,UnderlyingInstrID,
                                               ProductClass,PositionType,PositionDateType,
                                               StrikePrice,OptionsType,
                                               VolumeMultiple,UnderlyingMultiple,
                                               InstrumentID,InstrumentName,
                                               DeliveryYear,DeliveryMonth,AdvanceMonth
                                           )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, %s)"""
            sql_insert_params = []
            for future in csv_file:
                # 去除组合合约
                if "&" in future["ProductID"]:
                    continue
                SGID = self.exchange_conf[future["ExchangeID"]]
                ProductID = future["ProductID"]
                ProductClass = future["ProductClass"]

                UnderlyingInstrID = None
                # 判断是否为期权
                if ProductClass == '2':
                    UnderlyingInstrID = future["UnderlyingInstrID"]

                OptionsType = future["OptionsType"]
                # 期权类型为空改为0
                if OptionsType == '':
                    OptionsType = '0'

                DeliveryYear = future["DeliveryYear"]
                DeliveryMonth = future["DeliveryMonth"]
                # 计算期权交割年月
                if ProductClass == '2' and DeliveryYear == '1':
                    DeliveryYear = "%s%s" % (str(datetime.datetime.now().year)[0:3], future["UnderlyingInstrID"][-3:-2])
                    if int(DeliveryYear) < datetime.datetime.now().year:
                        DeliveryYear = "%s%s" % (str(int(str(datetime.datetime.now().year)[0:3]) + 1), future["UnderlyingInstrID"][-3:-2])
                    DeliveryMonth = future["UnderlyingInstrID"][-2:]
                sql_insert_params.append((SGID, ProductID,
                                          ProductID, UnderlyingInstrID,
                                          ProductClass, future["PositionType"], future["PositionDateType"],
                                          future["StrikePrice"], OptionsType,
                                          future["VolumeMultiple"],
                                          "0" if future["UnderlyingMultiple"] is None else future["UnderlyingMultiple"],
                                          future["InstrumentID"],
                                          future["InstrumentName"].decode(encoding='gbk', errors='ignore').encode(
                                              encoding='utf8'),
                                          DeliveryYear, DeliveryMonth, "012"))
            cursor.executemany(sql_insert_futures, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_Instrument完成")
        # 导入完成后写入产品表
        self.__init_product()

    def __init_product(self):
        mysql_conn = self.mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_ClientProductRight where SettlementGroupID in "
                           + str(tuple([str(i) for i in self.exchange_conf.values()])))
            cursor.execute("delete from siminfo.t_MarketProduct where SettlementGroupID in "
                           + str(tuple([str(i) for i in self.exchange_conf.values()])))
            cursor.execute("delete from siminfo.t_MdPubStatus where SettlementGroupID in "
                           + str(tuple([str(i) for i in self.exchange_conf.values()])))
            cursor.execute("delete from siminfo.t_PartProductRight where SettlementGroupID in "
                           + str(tuple([str(i) for i in self.exchange_conf.values()])))
            cursor.execute("delete from siminfo.t_PartProductRole where SettlementGroupID in "
                           + str(tuple([str(i) for i in self.exchange_conf.values()])))
            cursor.execute("delete from siminfo.t_Product where SettlementGroupID in "
                           + str(tuple([str(i) for i in self.exchange_conf.values()])))
            cursor.execute("delete from siminfo.t_ProductGroup where SettlementGroupID in "
                           + str(tuple([str(i) for i in self.exchange_conf.values()])))
            # t_ClientProductRight
            self.logger.info("产品类型导入t_ClientProductRight")
            cursor.execute("")
            sql = """INSERT into siminfo.t_ClientProductRight(
                           SELECT SettlementGroupID,ProductID,'00000000' AS ClientID,'0' AS TradingRight 
                           FROM siminfo.t_instrument 
                           WHERE SettlementGroupID in """ + str(tuple([str(i) for i in self.exchange_conf.values()])) + """
                           GROUP BY SettlementGroupID,ProductID)"""
            cursor.execute(sql)
            # t_MarketProduct
            self.logger.info("产品类型导入t_MarketProduct")
            sql = """INSERT into siminfo.t_MarketProduct(
                           SELECT t.SettlementGroupID, t1.MarketID, t.ProductID 
                           FROM siminfo.t_instrument t,siminfo.t_market t1 
                           WHERE t.SettlementGroupID = t1.SettlementGroupID 
                               AND t.SettlementGroupID in """ + str(
                tuple([str(i) for i in self.exchange_conf.values()])) + """
                           GROUP BY t.SettlementGroupID,t.ProductID,t1.MarketID)"""
            cursor.execute(sql)
            # t_MdPubStatus
            self.logger.info("产品类型导入t_MdPubStatus")
            sql = """INSERT into siminfo.t_MdPubStatus(
                           SELECT SettlementGroupID,ProductID,'3' AS InstrumentStatus,'0' AS MdPubStatus 
                           FROM siminfo.t_instrument 
                           WHERE SettlementGroupID in """ + str(tuple([str(i) for i in self.exchange_conf.values()])) + """
                           GROUP BY SettlementGroupID,ProductID)"""
            cursor.execute(sql)
            # t_PartProductRight
            self.logger.info("产品类型导入t_PartProductRight")
            sql = """INSERT INTO siminfo.t_PartProductRight(
                           SELECT SettlementGroupID,ProductID,'00000000' AS ParticipantID,'0' AS TradingRight 
                           FROM siminfo.t_instrument 
                           WHERE SettlementGroupID in """ + str(tuple([str(i) for i in self.exchange_conf.values()])) + """
                           GROUP BY SettlementGroupID,ProductID)"""
            cursor.execute(sql)
            # t_PartProductRole
            self.logger.info("产品类型导入t_PartProductRole")
            sql = """INSERT INTO siminfo.t_PartProductRole(
                           SELECT SettlementGroupID,'00000000' AS ParticipantID,ProductID,'1' AS TradingRole 
                           FROM siminfo.t_instrument 
                           WHERE SettlementGroupID in """ + str(tuple([str(i) for i in self.exchange_conf.values()])) + """
                           GROUP BY SettlementGroupID,ProductID)"""
            cursor.execute(sql)
            # t_Product
            self.logger.info("产品类型导入t_Product")
            sql = """INSERT INTO siminfo.t_Product(
                           SELECT SettlementGroupID, ProductID, ProductGroupID, '' AS ProductName,'' AS ProductClass 
                           FROM siminfo.t_instrument 
                           WHERE SettlementGroupID in """ + str(tuple([str(i) for i in self.exchange_conf.values()])) + """
                           GROUP BY SettlementGroupID,ProductID,ProductGroupID)"""
            cursor.execute(sql)
            # t_ProductGroup
            self.logger.info("产品类型导入t_ProductGroup")
            sql = """INSERT INTO siminfo.t_ProductGroup(
                           SELECT SettlementGroupID,ProductGroupID,'' AS ProductGroupName,ProductGroupID as CommodityID
                           FROM siminfo.t_instrument 
                           WHERE SettlementGroupID in """ + str(tuple([str(i) for i in self.exchange_conf.values()])) + """
                           GROUP BY SettlementGroupID,ProductGroupID,ProductGroupID)"""
            cursor.execute(sql)
            mysql_conn.commit()
        finally:
            mysql_conn.close()

    def __t_TradingSegmentAttr(self, mysqlDB, csv_file):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            # 删除期货交易所下所有数据
            cursor.execute("delete from siminfo.t_TradingSegmentAttr where SettlementGroupID in  " + str(
                tuple([str(i) for i in self.exchange_conf.values()])))
            sql_insert_segment = """INSERT INTO siminfo.t_TradingSegmentAttr (
                                                SettlementGroupID,TradingSegmentSN,
                                                TradingSegmentName,StartTime,
                                                InstrumentStatus,DayOffset,InstrumentID
                                            ) VALUES (%s,%s,%s,%s,%s,%s,%s)"""
            sql_insert_params = []
            #  加载交易时间段数据
            segment_attr = self.__loadJSON(tableName='t_TradingSegmentAttr')
            if segment_attr is None:
                self.logger.error("t_TradingSegmentAttr不存在")
                return
            for future in csv_file:
                if "&" in future["ProductID"]:
                    continue
                SGID = self.exchange_conf[future["ExchangeID"]]

                # 判断结算组是否存在
                if SGID in segment_attr:
                    params = self.__get_segment_attr(attr=segment_attr[SGID],
                                                     product=future["ProductID"],
                                                     instrument=future["InstrumentID"])
                    sql_insert_params += params
            cursor.executemany(sql_insert_segment, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_TradingSegmentAttr完成")

    # 通过产品代码生成目标合约的交易时间段
    def __get_segment_attr(self, attr, product, instrument):
        future = attr['future']
        all_trading_time = attr['tradingTime']
        exist_trading_time = []
        # 获取当前模版存在的产品代码
        for segment in future:
            if product in future[segment]:
                exist_trading_time.append(segment)
        # 如果模版里面没有该产品，则取该结算组白天交易时间段
        params = []
        if len(exist_trading_time) == 0:
            for segment in all_trading_time["day"]:
                params.append((segment[0], segment[1], segment[2], segment[3], segment[4], segment[5], instrument))
        else:
            segment_list = []
            for exist in exist_trading_time:
                segment_list += all_trading_time[exist]
            for segment in segment_list:
                params.append((segment[0], segment[1], segment[2], segment[3], segment[4], segment[5], instrument))
        return params

    def __t_MarginRate(self, mysqlDB, csv_file):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            # 获取模板文件
            template = self.__loadJSON(tableName='t_MarginRate')
            if template is None:
                self.logger.error("t_MarginRate template is None")
                return
            cursor = mysql_conn.cursor()
            # 删除期货交易所下所有数据
            cursor.execute("delete from siminfo.t_MarginRate where SettlementGroupID in "
                           + str(tuple([str(i) for i in self.exchange_conf.values()])))

            sql_insert_rate = """INSERT INTO siminfo.t_MarginRate (
                                                 SettlementGroupID,
                                                 MarginCalcID,
                                                 InstrumentID,
                                                 ParticipantID
                                             ) VALUES (%s,%s,%s,%s)"""
            sql_insert_params = []
            for future in csv_file:
                if "&" in future["ProductID"]:
                    continue
                SGID = self.exchange_conf[future["ExchangeID"]]
                if SGID in template:
                    sql_insert_params.append((SGID, template[SGID][1], future["InstrumentID"], template[SGID][3]))
            cursor.executemany(sql_insert_rate, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_MarginRate完成")

    def __t_MarginRateDetail(self, mysqlDB, *args):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            # 产品文件
            products = args[0]
            # 通过产品文件将产品和结算组挂接
            product_sgid = dict()
            for product in products:
                product_sgid[product['ProductID']] = self.exchange_conf[str(product['ExchangeID']).upper()]
            # 保证金率文件
            marginrate = args[1]
            # 删除期货交易所下所有数据
            cursor.execute("delete from siminfo.t_MarginRateDetail where SettlementGroupID in "
                           + str(tuple([str(i) for i in self.exchange_conf.values()])))
            sql_insert_detail = """INSERT INTO siminfo.t_MarginRateDetail (
                                        SettlementGroupID,TradingRole,HedgeFlag,
                                        ValueMode,LongMarginRatio,ShortMarginRatio,
                                        InstrumentID,ParticipantID,ClientID
                                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            sql_insert_params = []
            for future in marginrate:
                for k, v in product_sgid.iteritems():
                    if k == filter(lambda x: x not in '0123456789', str(future['InstrumentID'])):
                        sql_insert_params.append((v, '1', future['HedgeFlag'], '1',
                                                  future['LongMarginRatioByMoney'], future['ShortMarginRatioByMoney'],
                                                  future['InstrumentID'], '00000000', '00000000'))
                        break
            cursor.executemany(sql_insert_detail, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_MarginRateDetail完成")

    def __t_TransFeeRateDetail(self, mysqlDB, csv_file):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            # 获取模板文件
            template = self.__loadJSON(tableName='t_TransFeeRateDetail')
            if template is None:
                self.logger.error("t_TransFeeRateDetail template is None")
                return
            cursor = mysql_conn.cursor()
            # 删除期货交易所下所有数据
            cursor.execute("delete from siminfo.t_transfeeratedetail where SettlementGroupID in "
                           + str(tuple([str(i) for i in self.exchange_conf.values()])))
            sql_insert_detail = """insert into siminfo.t_transfeeratedetail(
                                    SettlementGroupID,TradingRole,HedgeFlag,ValueMode,OpenFeeRatio,
                                    CloseYesterdayFeeRatio,CloseTodayFeeRatio,MinOpenFee,MinCloseFee,
                                    MaxOpenFee,MaxCloseFee,InstrumentID,ParticipantID,
                                    ClientID) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            sql_insert_params = []
            for future in csv_file:
                if "&" in future["ProductID"]:
                    continue
                SGID = self.exchange_conf[future["ExchangeID"]]
                if SGID in template:
                    sql_insert_params.append(
                    self.__get_trans_fee_rate_detail(attr=template[SGID],
                                                  product=future["ProductID"],
                                                  instrument=future["InstrumentID"]))
            cursor.executemany(sql_insert_detail, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_TransFeeRateDetail完成")

    # 通过产品代码生成目标合约的保证金率
    def __get_trans_fee_rate_detail(self, attr, product, instrument):
        template = attr["template"]
        trans_fee = attr["transFee"]
        # 判断产品代码是否存在于模版
        if product in trans_fee.keys():
            params = (template[0], template[1], template[2], trans_fee[product][1],
                      trans_fee[product][0], trans_fee[product][0], trans_fee[product][0],
                      template[7], template[8], template[9], template[10], instrument, template[12],
                      template[13])
        else:
            params = (template[0], template[1], template[2], template[3], template[4], template[5], template[6],
                      template[7], template[8], template[9], template[10], instrument, template[12],
                      template[13])
        return params

    def __t_PriceBanding(self, mysqlDB, csv_file):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            # 获取模板文件
            template = self.__loadJSON(tableName='t_PriceBanding')
            if template is None:
                self.logger.error("t_PriceBanding template is None")
                return
            cursor = mysql_conn.cursor()
            # 删除期货交易所下所有数据
            cursor.execute("delete from siminfo.t_PriceBanding where SettlementGroupID in "
                           + str(tuple([str(i) for i in self.exchange_conf.values()])))
            sql_insert_price = """INSERT INTO siminfo.t_PriceBanding (
                                SettlementGroupID,PriceLimitType,ValueMode,RoundingMode,
                                UpperValue,LowerValue,InstrumentID,TradingSegmentSN
                            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
            sql_insert_params = []
            for future in csv_file:
                SGID = self.exchange_conf[future["ExchangeID"]]
                if float(future["PreSettlementPrice"]) != 0:
                    if SGID == 'SG06':
                        sql_insert_params.append((SGID, template[SGID][1], template[SGID][2], template[SGID][3],
                                                  template[SGID][4], template[SGID][5], future["InstrumentID"],
                                                  template[SGID][7]))
                    else:
                        DailyPriceUpLimit = float(future['UpperLimitPrice']) - float(future['PreSettlementPrice'])
                        DailyPriceDownLimit = float(future['PreSettlementPrice']) - float(future['LowerLimitPrice'])
                        sql_insert_params.append((SGID, template[SGID][1], "2", template[SGID][3],
                                                  DailyPriceUpLimit, DailyPriceDownLimit, future["InstrumentID"],
                                                  template[SGID][7]))
            cursor.executemany(sql_insert_price, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_PriceBanding完成")

    def __t_InstrumentProperty(self, mysqlDB, csv_file):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_InstrumentProperty where SettlementGroupID in "
                           + str(tuple([str(i) for i in self.exchange_conf.values()])))
            sql_Property = """INSERT INTO siminfo.t_InstrumentProperty (
                             SettlementGroupID,CreateDate,OpenDate,ExpireDate,StartDelivDate,
                             EndDelivDate,BasisPrice,MaxMarketOrderVolume,MinMarketOrderVolume,
                             MaxLimitOrderVolume,MinLimitOrderVolume,PriceTick,
                             AllowDelivPersonOpen,InstrumentID,InstLifePhase
                             )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            sql_params = []
            for future in csv_file:
                if "&" in future["ProductID"]:
                    continue
                SGID = self.exchange_conf[future["ExchangeID"]]
                ProductID = future["ProductID"]
                sql_params.append((SGID, future["CreateDate"], future["OpenDate"], future["ExpireDate"],
                                   future["StartDelivDate"], future["EndDelivDate"], 0,
                                   future["MaxMarketOrderVolume"],
                                   future["MinMarketOrderVolume"],
                                   future["MaxLimitOrderVolume"],
                                   future["MinLimitOrderVolume"],
                                   future["PriceTick"],
                                   0, future["InstrumentID"], 1))
            cursor.executemany(sql_Property, sql_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_InstrumentProperty完成")

    def __t_MarketData(self, mysqlDB, csv_file):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_MarketData where SettlementGroupID in "
                           + str(tuple([str(i) for i in self.exchange_conf.values()])))
            sql_insert = """INSERT INTO siminfo.t_MarketData (
                                    TradingDay,SettlementGroupID,LastPrice,PreSettlementPrice,
                                    PreClosePrice,PreOpenInterest,OpenPrice,
                                    HighestPrice,LowestPrice,Volume,Turnover,
                                    OpenInterest,ClosePrice,SettlementPrice,
                                    UpperLimitPrice,LowerLimitPrice,PreDelta,
                                    CurrDelta,UpdateTime,UpdateMillisec,InstrumentID
                               )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            sql_params = []
            for future in csv_file:
                SGID = self.exchange_conf[future["ExchangeID"]]
                sql_params.append(
                    (self.TradingDay, SGID, None, future["PreSettlementPrice"], future["PreClosePrice"],
                     future["PreOpenInterest"], None,
                     None, None, None, None,
                     None, None, None,
                     None, None, future["PreDelta"],
                     None, "15:15:00", "100", future["InstrumentID"]))
            cursor.executemany(sql_insert, sql_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_MarketData完成")

    def __check_file(self, file_name=None):
        env_dist = os.environ
        # 判断环境变量是否存在HOME配置
        if 'HOME' not in env_dist:
            self.logger.error("HOME not in environment variable")
            return None
        # 获取文件路径
        catalog = env_dist['HOME']
        catalog = '%s%s%s%s%s' % (catalog, os.path.sep, 'sim_data', os.path.sep, self.TradingDay)
        # 合约信息
        instrument = '%s%s%s' % (catalog, os.path.sep, self.file_instrument)
        # 产品信息
        product = '%s%s%s' % (catalog, os.path.sep, self.file_product)
        # 行情信息
        depthmarketdata = '%s%s%s' % (catalog, os.path.sep, self.file_marketdata)
        # 保证金率
        marginrate = '%s%s%s' % (catalog, os.path.sep, self.file_marginrate)
        # 判断instrument.csv文件是否存在，不存在设置为空
        if not os.path.exists(instrument):
            self.logger.error("%s%s" % (instrument, " is not exists"))
            instrument = None
        # 判断product.csv文件是否存在，不存在设置为空
        if not os.path.exists(product):
            self.logger.error("%s%s" % (product, " is not exists"))
            product = None
        # 判断depthmarketdata.csv文件是否存在，不存在设置为空
        if not os.path.exists(depthmarketdata):
            self.logger.error("%s%s" % (depthmarketdata, " is not exists"))
            depthmarketdata = None
        # 判断marginrate.csv文件是否存在，不存在设置为空
        if not os.path.exists(marginrate):
            self.logger.error("%s%s" % (marginrate, " is not exists"))
            marginrate = None
        # 读取CSV文件
        if file_name is None:
            return self.__loadCSV(instrument), self.__loadCSV(product), \
                   self.__loadCSV(depthmarketdata), self.__loadCSV(marginrate)
        elif file_name == 'instrument':
            return self.__loadCSV(instrument)
        elif file_name == 'product':
            return self.__loadCSV(product)
        elif file_name == 'depthmarketdata':
            return self.__loadCSV(depthmarketdata)
        elif file_name == 'marginrate':
            return self.__loadCSV(marginrate)

    def __loadCSV(self, csv_file):
        if csv_file is None:
            return None
        else:
            return [row for row in csv.DictReader(open(csv_file))]

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
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql", "log", "init"])
    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)
    # 启动future脚本
    trans_futureinfo(context=context, configs=conf)
