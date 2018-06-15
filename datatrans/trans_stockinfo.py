# -*- coding: UTF-8 -*-

import os
import json
import codecs

from utils import parse_conf_args, Configuration, path, mysql, log
from stock_entity import stockVO
from xml.dom.minidom import parse
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
        # 股票文件
        self.stock_filename = {
            "SG01": ["cpxx%m%d.txt"],
            "SG02": ["securities_%y%m%d.xml", "cashauctionparams_%y%m%d.xml"]
        }
        # DBF文件
        self.dbf_file = ["PAR_QY_INFO%y%m%d.dbf"]
        self.__transform()

    def __transform(self):
        mysqlDB = self.mysqlDB
        # 查询当前交易日
        sql = """SELECT tradingday FROM siminfo.t_tradesystemtradingday WHERE tradesystemid = %s"""
        fc = mysqlDB.select(sql, ('0001',))
        current_trading_day = fc[0][0]
        self.TradingDay = current_trading_day
        self.logger.info("[trans_stockinfo] current_trading_day = %s" % current_trading_day)

        # 读取txt文件(‘ES’表示股票；‘EU’表示基金；‘D’表示债券； ‘RWS’表示权证；‘FF’表示期货。（参考ISO10962），集合资产管理计划、债券预发行取‘D’)
        stock_list = self.__check_file()
        # 读取dbf文件【PAR_QY_INFO.dbf】
        par_qy_info = self.__check_dbf()
        if stock_list is not None:
            for settlement_group in stock_list:
                self.logger.info("==========trans %s 数据===========" % settlement_group)
                stock_data = stock_list[settlement_group]
                # ===========处理stock_dbf写入t_Instrument表==============
                self.__t_Instrument(mysqlDB=mysqlDB, settlement_group=settlement_group, stock_data=stock_data)

                # ===========处理stock_dbf写入t_TradingSegmentAttr表==============
                self.__t_TradingSegmentAttr(mysqlDB=mysqlDB, settlement_group=settlement_group, stock_data=stock_data)

                # ===========处理stock_dbf写入t_MarginRate表==============
                self.__t_MarginRate(mysqlDB=mysqlDB, settlement_group=settlement_group, stock_data=stock_data)

                # ===========处理stock_dbf写入t_MarginRateDetail表==============
                self.__t_MarginRateDetail(mysqlDB=mysqlDB, settlement_group=settlement_group, stock_data=stock_data)

                # ===========处理stock_dbf写入t_PriceBanding表==============
                self.__t_PriceBanding(mysqlDB=mysqlDB, settlement_group=settlement_group, stock_data=stock_data)

                # ===========写入t_InstrumentProperty表==============
                self.__t_InstrumentProperty(mysqlDB=mysqlDB, settlement_group=settlement_group, stock_data=stock_data)

                # ===========写入t_MarketData表==============
                self.__t_MarketData(mysqlDB=mysqlDB, settlement_group=settlement_group, stock_data=stock_data)

        if par_qy_info is not None:
            # ===========处理info_dbf写入t_SecurityProfit表===========
            self.__t_SecurityProfit(mysqlDB=mysqlDB, settlement_group={"1": "SG01", "2": "SG02"}, dbf=par_qy_info)

    def __t_Instrument(self, mysqlDB, settlement_group, stock_data):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_Instrument where SettlementGroupID = %s ", (settlement_group,))
            sql_insert_instrument = """INSERT INTO siminfo.t_Instrument (
                                       SettlementGroupID,ProductID,
                                       ProductGroupID,UnderlyingInstrID,
                                       ProductClass,PositionType,
                                       StrikePrice,OptionsType,
                                       VolumeMultiple,UnderlyingMultiple,
                                       TotalEquity,CirculationEquity,
                                       InstrumentID,InstrumentName,
                                       DeliveryYear,DeliveryMonth,AdvanceMonth
                                   )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            sql_insert_params = []
            if settlement_group == 'SG01':
                ProductID = 'ZQ_SH'
                ProductGroupID = 'ZQ'
            if settlement_group == 'SG02':
                ProductID = 'ZQ_SZ'
                ProductGroupID = 'ZQ'
            for stock in stock_data:
                sql_insert_params.append((settlement_group,
                                          ProductID,
                                          ProductGroupID,
                                          ProductID,
                                          "4", "2", None, "0",
                                          1, 1, 0, 0,
                                          stock.ZQDM, stock.ZWMC,
                                          2099, 12, "012"))
            cursor.executemany(sql_insert_instrument, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_Instrument完成")

    def __t_TradingSegmentAttr(self, mysqlDB, settlement_group, stock_data):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_TradingSegmentAttr where SettlementGroupID = %s ",
                           (settlement_group,))
            # 加载模版文件
            SegmentAttr = self.__loadJSON(tableName='t_TradingSegmentAttr')
            if SegmentAttr is None or settlement_group not in SegmentAttr:
                self.logger.error("SegmentAttr is None or settlement_group not in SegmentAttr")
                return
            sql_insert_segment = """INSERT INTO siminfo.t_TradingSegmentAttr(SettlementGroupID,TradingSegmentSN,
                                            TradingSegmentName,StartTime,InstrumentStatus,DayOffset,InstrumentID)
                                VALUES(%s,%s,%s,%s,%s,%s,%s)"""
            sql_insert_params = []
            for stock in stock_data:
                for attr in SegmentAttr[settlement_group]:
                    sql_insert_params.append((settlement_group, attr[1], attr[2], attr[3], attr[4], '0', stock.ZQDM))
            cursor.executemany(sql_insert_segment, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_TradingSegmentAttr完成")

    def __t_MarginRate(self, mysqlDB, settlement_group, stock_data):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_MarginRate where SettlementGroupID = %s ", (settlement_group,))
            # 获取模板文件
            template = self.__loadJSON(tableName='t_MarginRate')
            if template is None:
                self.logger.error("t_MarginRate template is None")
                return
            sql_insert_rate = """INSERT INTO siminfo.t_MarginRate (
                                SettlementGroupID,
                                MarginCalcID,
                                InstrumentID,
                                ParticipantID
                            ) VALUES (%s,%s,%s,%s)"""
            sql_insert_params = []
            for stock in stock_data:
                sql_insert_params.append(
                    (settlement_group, template[settlement_group][1], stock.ZQDM, template[settlement_group][3]))
            cursor.executemany(sql_insert_rate, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_MarginRate完成")

    def __t_MarginRateDetail(self, mysqlDB, settlement_group, stock_data):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_MarginRateDetail where SettlementGroupID = %s ", (settlement_group,))
            # 获取模板文件
            template = self.__loadJSON(tableName='t_MarginRateDetail')
            if template is None:
                self.logger.error("t_MarginRateDetail template is None")
                return
            sql_insert_detail = """INSERT INTO siminfo.t_MarginRateDetail (
                                    SettlementGroupID,TradingRole,HedgeFlag,
                                    ValueMode,LongMarginRatio,ShortMarginRatio,
                                    InstrumentID,ParticipantID,ClientID
                                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            sql_insert_params = []
            for stock in stock_data:
                sql_insert_params.append((settlement_group, template[settlement_group][1],
                                          template[settlement_group][2], template[settlement_group][3],
                                          template[settlement_group][4], template[settlement_group][5],
                                          stock.ZQDM, template[settlement_group][9], template[settlement_group][10]))
            cursor.executemany(sql_insert_detail, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_MarginRateDetail完成")

    def __t_PriceBanding(self, mysqlDB, settlement_group, stock_data):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_PriceBanding where SettlementGroupID = %s ", (settlement_group,))
            # 获取模板文件
            template = self.__loadJSON(tableName='t_PriceBanding')
            if template is None:
                self.logger.error("t_PriceBanding template is None")
                return
            sql_insert_price = """INSERT INTO siminfo.t_PriceBanding (
                                    SettlementGroupID,PriceLimitType,ValueMode,RoundingMode,
                                    UpperValue,LowerValue,InstrumentID,TradingSegmentSN
                                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
            sql_insert_params = []
            for stock in stock_data:
                if stock.ZDFXZLX in ('1', '2'):
                    sql_insert_params.append((settlement_group, template[settlement_group][1],
                                        stock.ZDFXZLX, template[settlement_group][3],
                                        stock.ZFSXJG, stock.DFXXJG,
                                        stock.ZQDM, template[settlement_group][7]))
                else:
                    if float(stock.ZFSXJG) == 0 or float(stock.DFXXJG) == 0:
                        sql_insert_params.append((settlement_group, template[settlement_group][1],
                                                  '1', template[settlement_group][3],
                                                  template[settlement_group][4], template[settlement_group][5],
                                                  stock.ZQDM, template[settlement_group][7]))
                    else:
                        ZFSXJG = float(stock.ZFSXJG) - float(stock.QSPJ)
                        DFXXJG = float(stock.QSPJ) - float(stock.DFXXJG)
                        sql_insert_params.append((settlement_group, template[settlement_group][1],
                                                  '2', template[settlement_group][3],
                                                  ZFSXJG, DFXXJG,
                                                  stock.ZQDM, template[settlement_group][7]))
            cursor.executemany(sql_insert_price, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_PriceBanding完成")

    def __t_InstrumentProperty(self, mysqlDB, settlement_group, stock_data):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_InstrumentProperty where SettlementGroupID = %s ",
                           (settlement_group,))
            sql_Property = """INSERT INTO siminfo.t_InstrumentProperty (
                                 SettlementGroupID,CreateDate,OpenDate,ExpireDate,StartDelivDate,
                                 EndDelivDate,BasisPrice,MaxMarketOrderVolume,MinMarketOrderVolume,
                                 MaxLimitOrderVolume,MinLimitOrderVolume,PriceTick,
                                 AllowDelivPersonOpen,InstrumentID,InstLifePhase
                                 )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            sql_params = []
            for stock in stock_data:
                sql_params.append((settlement_group, '99991219', stock.SSRQ,
                                   '99991219', '99991219', '99991219', 0, 1000000, 1,
                                   1000000, 1, 0.01 if stock.JGDW is None else stock.JGDW, 0, stock.ZQDM, 1))
            cursor.executemany(sql_Property, sql_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_InstrumentProperty完成")

    def __t_MarketData(self, mysqlDB, settlement_group, stock_data):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_MarketData where SettlementGroupID = %s ", (settlement_group,))
            sql_insert_market = """INSERT INTO siminfo.t_MarketData (
                                            TradingDay,SettlementGroupID,LastPrice,PreSettlementPrice,
                                            PreClosePrice,UnderlyingClosePx,PreOpenInterest,OpenPrice,
                                            HighestPrice,LowestPrice,Volume,Turnover,
                                            OpenInterest,ClosePrice,SettlementPrice,
                                            UpperLimitPrice,LowerLimitPrice,PreDelta,
                                            CurrDelta,UpdateTime,UpdateMillisec,InstrumentID
                                   )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            sql_insert_params = []
            for stock in stock_data:
                sql_insert_params.append((self.TradingDay, settlement_group, None, stock.QSPJ,
                                          stock.QSPJ, None, '0', None,
                                          None, None, None, None,
                                          None, None, None,
                                          None, None, None,
                                          None, stock.GXSJ, "100", stock.ZQDM))
            cursor.executemany(sql_insert_market, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_MarketData完成")

    # 读取处理PAR_QY_INFO文件
    def __t_SecurityProfit(self, mysqlDB, settlement_group, dbf):
        mysql_conn = mysqlDB.get_cnx()
        mysql_conn.start_transaction()
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("delete from siminfo.t_SecurityProfit where SettlementGroupID in " + str(tuple([str(i) for i in settlement_group.values()])))
            sql_insert_qy_info = """INSERT INTO siminfo.t_SecurityProfit (
                                               SettlementGroupID,SecurityID,
                                               SecurityType,SecurityMarketID,
                                               ProfitType,DJDate,
                                               CQDate,EndDate,
                                               DZDate,BeforeRate,
                                               AfterRate,Price
                                           )VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            sql_insert_params = []
            for info in dbf:
                if str(info['SCDM']) in settlement_group:
                    settlement_group_id = settlement_group[str(info['SCDM'])]
                    sql_insert_params.append((settlement_group_id, info['ZQDM'],
                                          info['ZQLX'], info['SCDM'], info['QYKIND'],
                                          info['DJDATE'], info['CQDATE'], info['ENDDATE'],
                                          info['DZDATE'], info['BEFORERATE'],
                                          info['AFTERRATE'], info['PRICE']))
            cursor.executemany(sql_insert_qy_info, sql_insert_params)
            mysql_conn.commit()
        finally:
            mysql_conn.close()
        self.logger.info("写入t_SecurityProfit完成")

    def __check_file(self):
        env_dist = os.environ
        # 判断环境变量是否存在HOME配置
        if 'HOME' not in env_dist:
            self.logger.error("HOME not in environment variable")
            return None
        # 获取文件路径
        catalog = env_dist['HOME']
        # 文件路径
        catalog = '%s%s%s%s%s' % (catalog, os.path.sep, 'sim_data', os.path.sep, self.TradingDay)
        stock_data = dict()
        # 遍历导入文件
        for sgid in self.stock_filename:
            stock_path = self.stock_filename.get(sgid)
            for index, enum_file in enumerate(stock_path):
                stock_path[index] = '%s%s%s' % (catalog, os.path.sep, enum_file.replace("%y", self.TradingDay[0:4]).replace("%m", self.TradingDay[4:6]).replace("%d", self.TradingDay[6:8]),)
                # 判断文件是否存在
                if not os.path.exists(stock_path[index]):
                    self.logger.error("%s%s" % (stock_path[index], " is not exists"))
                    return None
            if sgid == 'SG01':
                # 读取txt文件
                stock_file = codecs.open(stock_path[0], encoding='gbk')
                stock_data.update({sgid: self.__txt_to_stock(stock_file, ("ES", "ASH", "510050", "510300", "511010", "510900"))})
            if sgid == 'SG02':
                # 读取xml文件
                stock_data.update({sgid: self.__xml_to_stock(stock_path)})
        return stock_data

    def __check_dbf(self):
        env_dist = os.environ
        # 判断环境变量是否存在HOME配置
        if 'HOME' not in env_dist:
            self.logger.error("HOME not in environment variable")
            return None
        # 获取文件路径
        catalog = env_dist['HOME']
        catalog = '%s%s%s%s%s' % (catalog, os.path.sep, 'sim_data', os.path.sep, self.TradingDay)
        par_qy_info = '%s%s%s' % (catalog, os.path.sep, self.dbf_file[0].replace("%y", self.TradingDay[0:4]).replace("%m", self.TradingDay[4:6]).replace("%d", self.TradingDay[6:8]))
        # 判断PAR_QY_INFOYYYYMMDD.dbf文件是否存在，不存在设置为空
        if not os.path.exists(par_qy_info):
            self.logger.error("%s%s" % (par_qy_info, " is not exists"))
            par_qy_info = None
        if par_qy_info is not None:
            par_qy_info = self.__loadDBF(par=par_qy_info)
        return par_qy_info

    def __loadDBF(self, par):
        # 加载 PAR_QY_INFO 数据
        info = DBF(filename=par, encoding='GBK')
        info.load()
        return info.records

    def __xml_to_stock(self, xml):
        security_file = xml[0]
        market_file = xml[1]

        DOMTree = parse(security_file)
        collection = DOMTree.documentElement
        Security = collection.getElementsByTagName("Security")
        stock_list = dict()
        for se in Security:
            zqdm = se.getElementsByTagName("SecurityID")[0].childNodes[0].data.strip()
            SecurityType = se.getElementsByTagName("SecurityType")[0].childNodes[0].data.strip()
            if int(SecurityType) in (1, 2, 3, 16, 17):
                stock = stockVO(None)
                stock.ZQDM = zqdm
                stock.ZWMC = se.getElementsByTagName("Symbol")[0].childNodes[0].data.strip()
                stock.QSPJ = se.getElementsByTagName("PrevClosePx")[0].childNodes[0].data.strip()
                stock.ZQLB = se.getElementsByTagName("SecurityType")[0].childNodes[0].data.strip()
                stock.SSRQ = se.getElementsByTagName("ListDate")[0].childNodes[0].data.strip()
                stock_list.update({zqdm: stock})

        DOMTree = parse(market_file)
        collection = DOMTree.documentElement
        Security = collection.getElementsByTagName("Security")

        for se in Security:
            zqdm = se.getElementsByTagName("SecurityID")[0].childNodes[0].data.strip()
            stock = stock_list.get(zqdm)
            if stock is not None:
                stock.ZDFXZLX = \
                se.getElementsByTagName("PriceLimitSetting")[0].getElementsByTagName("Setting")[1].getElementsByTagName(
                    "LimitType")[0].childNodes[0].data.strip()
                stock.ZFSXJG = \
                se.getElementsByTagName("PriceLimitSetting")[0].getElementsByTagName("Setting")[1].getElementsByTagName(
                    "LimitUpRate")[0].childNodes[0].data.strip()
                stock.DFXXJG = \
                se.getElementsByTagName("PriceLimitSetting")[0].getElementsByTagName("Setting")[1].getElementsByTagName(
                    "LimitDownRate")[0].childNodes[0].data.strip()
                stock.BSLDW = \
                se.getElementsByTagName("BuyQtyUnit")[0].childNodes[0].data.strip()
                stock.JGDW = \
                se.getElementsByTagName("PriceTick")[0].childNodes[0].data.strip()
                stock_list.update({zqdm: stock})
        return stock_list.values()

    def __txt_to_stock(self, txt, stock_filter):
        stock_list = []
        for lines in txt:
            VO = stockVO(lines.split("|"))
            if stock_filter is None:
                stock_list.append(VO)
            elif VO.ZQLB in stock_filter and VO.ZQZLB in stock_filter:
                stock_list.append(VO)
            elif VO.ZQDM in stock_filter:
                stock_list.append(VO)
        return stock_list

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
    # 启动stock脚本
    trans_stockinfo(context=context, configs=conf)
