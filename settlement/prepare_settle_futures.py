# -*- coding: UTF-8 -*-

import os
import json
import csv

from utils import mysql, log, Configuration, parse_conf_args, path, process_assert


def prepare_settle_future(context, conf):
    result_code = 0
    logger = log.get_logger(category="PrepareSettleFuture")

    trade_system_id = conf.get("tradeSystemId")
    settlement_id = conf.get("settlementId")

    base_dir = conf.get("baseDataHome")

    data_target_dir = os.path.join(base_dir, trade_system_id, settlement_id)

    data_target_dir = path.convert(data_target_dir)

    # 下场文件导入数据库
    logger.info("[load csv to database with %s] begin" % json.dumps(conf, encoding="UTF-8", ensure_ascii=False))
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))
    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        logger.info("[get current trading day]......")
        sql = """SELECT t1.tradingday FROM siminfo.t_tradesystemtradingday t1 WHERE t1.tradesystemid = %s"""
        cursor.execute(sql, (trade_system_id,))
        row = cursor.fetchone()

        current_trading_day = str(row[0])
        logger.info("[get current trading day] current_trading_day = %s" % (current_trading_day))

        sql = """SELECT 
                      t1.tradingday 
                    FROM
                      dbclear.t_settlement t1,
                      siminfo.t_tradesystemsettlementgroup t3 
                    WHERE t1.tradingday = %s
                      AND t1.settlementgroupid = t3.settlementgroupid 
                      AND t3.tradesystemid = %s
                      AND t1.settlementid = %s Limit 1 """
        cursor.execute(sql, (current_trading_day, trade_system_id, settlement_id))
        row = cursor.fetchone()

        if row is not None:
            logger.error("[load data to dbclear] Error: Data for %s-%s is existed." % (trade_system_id, settlement_id))
        else:
            logger.info("[generate settlement info]......")
            sql = """INSERT INTO dbclear.t_settlement(tradingday, settlementgroupid, settlementid, settlementstatus)
                                SELECT %s, settlementgroupid, %s, '0'
                                FROM siminfo.t_tradesystemsettlementgroup
                                WHERE tradesystemid = %s"""
            cursor.execute(sql, (current_trading_day, settlement_id, trade_system_id))

            logger.info("[load ClientPosition.csv to dbclear]......")
            sql = """DELETE FROM dbclear.t_ClientPosition WHERE tradingday = '%s' AND SettlementGroupID = 'TS-%s' AND SettlementID = '%s'""" % (
            current_trading_day, trade_system_id, settlement_id)
            cursor.execute(sql)
            csv_path = os.path.join(data_target_dir, "ClientPosition.csv")
            csv_path = csv_path.replace("\\", "/")
            sql = """LOAD DATA LOCAL INFILE '%s'
                             INTO TABLE dbclear.t_ClientPosition
                             CHARACTER SET utf8
                             fields terminated by ','
                             IGNORE 1 LINES
                             SET TradingDay = '%s', SettlementGroupID = 'TS-%s', SettlementID = '%s'""" % (
            csv_path, current_trading_day, trade_system_id, settlement_id)
            cursor.execute(sql)
            sql = """UPDATE 
                              dbclear.t_ClientPosition t1,
                              (SELECT 
                                t1.clientid,
                                t1.settlementgroupid 
                              FROM
                                siminfo.t_investorclient t1,
                                siminfo.t_tradesystemsettlementgroup t2 
                              WHERE t2.tradesystemid = '%s'
                                AND t1.settlementgroupid = t2.settlementgroupid) t2
                                SET t1.settlementgroupid = t2.settlementgroupid
                                WHERE t1.tradingday = '%s' AND t1.clientid = t2.clientid AND t1.settlementgroupid = 'TS-%s' AND t1.settlementid = '%s'""" % (
            trade_system_id, current_trading_day, trade_system_id, settlement_id)
            cursor.execute(sql)

            logger.info("[load PartPosition.csv to dbclear]......")
            sql = """DELETE FROM dbclear.t_PartPosition WHERE tradingday = '%s' AND SettlementGroupID = 'TS-%s' AND SettlementID = '%s'""" % (
            current_trading_day, trade_system_id, settlement_id)
            cursor.execute(sql)
            csv_path = os.path.join(data_target_dir, "PartPosition.csv")
            csv_path = csv_path.replace("\\", "/")
            sql = """LOAD DATA LOCAL INFILE '%s'
                                     INTO TABLE dbclear.t_PartPosition
                                     CHARACTER SET utf8
                                     fields terminated by ','
                                     IGNORE 1 LINES
                                     SET TradingDay = '%s', SettlementGroupID = 'TS-%s', SettlementID = '%s'""" % (
            csv_path, current_trading_day, trade_system_id, settlement_id)
            cursor.execute(sql)
            sql = """UPDATE 
                              dbclear.t_PartPosition t1,
                              (SELECT 
                                t1.participantid,
                                t1.settlementgroupid 
                              FROM
                                siminfo.t_participant t1,
                                siminfo.t_tradesystemsettlementgroup t2 
                              WHERE t2.tradesystemid = '%s'
                                AND t1.settlementgroupid = t2.settlementgroupid) t2
                                SET t1.settlementgroupid = t2.settlementgroupid
                                WHERE t1.tradingday = '%s' AND t1.participantid = t2.participantid AND t1.settlementgroupid = 'TS-%s' AND t1.settlementid = '%s'""" % (
            trade_system_id, current_trading_day, trade_system_id, settlement_id)
            cursor.execute(sql)

            logger.info("[load MarketData.csv to dbclear]......")
            sql = """DELETE FROM dbclear.t_MarketData WHERE tradingday = '%s' AND SettlementGroupID = 'TS-%s' AND SettlementID = '%s'""" % (
            current_trading_day, trade_system_id, settlement_id)
            cursor.execute(sql)
            csv_path = os.path.join(data_target_dir, "MarketData.csv")
            csv_path = csv_path.replace("\\", "/")
            sql = """LOAD DATA LOCAL INFILE '%s'
                                     INTO TABLE dbclear.t_MarketData
                                     CHARACTER SET utf8
                                     fields terminated by ','
                                     IGNORE 1 LINES
                                     (TradingDay,SettlementGroupID,SettlementID,LastPrice,PreSettlementPrice,PreClosePrice,PreOpenInterest,OpenPrice,HighestPrice,LowestPrice,Volume,Turnover,OpenInterest,ClosePrice,SettlementPrice,UpperLimitPrice,LowerLimitPrice,PreDelta,CurrDelta,UpdateTime,UpdateMillisec,InstrumentID)
                                     SET TradingDay = '%s', SettlementGroupID = 'TS-%s', SettlementID = '%s'""" % (
            csv_path, current_trading_day, trade_system_id, settlement_id)
            cursor.execute(sql)
            sql = """UPDATE 
                              dbclear.t_MarketData t1,
                              (SELECT 
                                t1.instrumentid,
                                t1.settlementgroupid 
                              FROM
                                siminfo.t_instrument t1,
                                siminfo.t_tradesystemsettlementgroup t2 
                              WHERE t2.tradesystemid = '%s'
                                AND t1.settlementgroupid = t2.settlementgroupid) t2
                                SET t1.settlementgroupid = t2.settlementgroupid
                                WHERE t1.tradingday = '%s' AND t1.instrumentid = t2.instrumentid AND t1.settlementgroupid = 'TS-%s' AND t1.settlementid = '%s'""" % (
            trade_system_id, current_trading_day, trade_system_id, settlement_id)
            cursor.execute(sql)

            logger.info("[load Order.csv to dbclear]......")
            sql = """DELETE FROM dbclear.t_Order WHERE tradingday = '%s' AND SettlementGroupID = 'TS-%s' AND SettlementID = '%s'""" % (
            current_trading_day, trade_system_id, settlement_id)
            cursor.execute(sql)
            csv_path = os.path.join(data_target_dir, "Order.csv")
            csv_path = csv_path.replace("\\", "/")
            sql = """LOAD DATA LOCAL INFILE '%s'
                                     INTO TABLE dbclear.t_Order
                                     CHARACTER SET utf8
                                     fields terminated by ','
                                     IGNORE 1 LINES
                                     SET TradingDay = '%s', SettlementGroupID = 'TS-%s', SettlementID = '%s'""" % (
            csv_path, current_trading_day, trade_system_id, settlement_id)
            cursor.execute(sql)
            sql = """UPDATE 
                              dbclear.t_Order t1,
                              (SELECT 
                                t1.clientid,
                                t1.settlementgroupid 
                              FROM
                                siminfo.t_investorclient t1,
                                siminfo.t_tradesystemsettlementgroup t2 
                              WHERE t2.tradesystemid = '%s'
                                AND t1.settlementgroupid = t2.settlementgroupid) t2
                                SET t1.settlementgroupid = t2.settlementgroupid
                                WHERE t1.tradingday = '%s' AND t1.clientid = t2.clientid AND t1.settlementgroupid = 'TS-%s' AND t1.settlementid = '%s'""" % (
            trade_system_id, current_trading_day, trade_system_id, settlement_id)
            cursor.execute(sql)

            logger.info("[load Trade.csv to dbclear]......")
            sql = """DELETE FROM dbclear.t_Trade WHERE tradingday = '%s' AND SettlementGroupID = 'TS-%s' AND SettlementID = '%s'""" % (
            current_trading_day, trade_system_id, settlement_id)
            cursor.execute(sql)
            csv_path = os.path.join(data_target_dir, "Trade.csv")
            csv_path = csv_path.replace("\\", "/")
            sql = """LOAD DATA LOCAL INFILE '%s'
                                     INTO TABLE dbclear.t_Trade
                                     CHARACTER SET utf8
                                     fields terminated by ','
                                     IGNORE 1 LINES
                                     SET TradingDay = '%s', SettlementGroupID = 'TS-%s', SettlementID = '%s'""" % (
            csv_path, current_trading_day, trade_system_id, settlement_id)
            cursor.execute(sql)
            sql = """UPDATE 
                              dbclear.t_Trade t1,
                              (SELECT 
                                t1.clientid,
                                t1.settlementgroupid 
                              FROM
                                siminfo.t_investorclient t1,
                                siminfo.t_tradesystemsettlementgroup t2 
                              WHERE t2.tradesystemid = '%s'
                                AND t1.settlementgroupid = t2.settlementgroupid) t2
                                SET t1.settlementgroupid = t2.settlementgroupid
                                WHERE t1.tradingday = '%s' AND t1.clientid = t2.clientid AND t1.settlementgroupid = 'TS-%s' AND t1.settlementid = '%s'""" % (
            trade_system_id, current_trading_day, trade_system_id, settlement_id)
            cursor.execute(sql)

            # 加载交易手续费率
            logger.info("[load ClientTransFeeRatio to dbclear]......")
            sql = """DELETE FROM dbclear.t_clienttransfeeratio WHERE tradingday = '%s' AND SettlementGroupID in (SELECT settlementgroupid FROM siminfo.t_tradesystemsettlementgroup WHERE tradesystemid = %s) AND SettlementID = '%s'""" % (
            current_trading_day, trade_system_id, settlement_id)
            cursor.execute(sql)
            sql = """INSERT INTO dbclear.t_clienttransfeeratio(tradingday, settlementgroupid, settlementid, participantid, clientid, instrumentid, tradingrole, hedgeflag, openfeeratio, closeyesterdayfeeratio, closetodayfeeratio,valuemode,minopenfee,maxopenfee,minclosefee,maxclosefee)
                                SELECT %s AS tradingday, 
                                        t1.settlementgroupid,
                                        %s AS settlementid,
                                        IFNULL(t2.participantid, t3.participantid),
                                        IFNULL(t2.clientid, t3.clientid),
                                        t1.instrumentid,
                                        IFNULL(t2.tradingrole, t3.tradingrole),
                                        IFNULL(t2.hedgeflag, t3.hedgeflag),
                                        IFNULL(t2.openfeeratio, t3.openfeeratio),
                                        IFNULL(t2.closeyesterdayfeeratio, t3.closeyesterdayfeeratio),
                                        IFNULL(t2.closetodayfeeratio, t3.closetodayfeeratio),
                                        IFNULL(t2.valuemode, t3.valuemode),
                                        IFNULL(t2.minopenfee, t3.minopenfee),
                                        IFNULL(t2.maxopenfee, t3.maxopenfee),
                                        IFNULL(t2.minclosefee, t3.minclosefee),
                                        IFNULL(t2.maxclosefee, t3.maxclosefee)
                                    FROM siminfo.t_instrument t1
                                    LEFT JOIN siminfo.t_transfeeratedetail t2
                                        ON(t1.settlementgroupid = t2.settlementgroupid AND t1.instrumentid = t2.instrumentid)
                                    LEFT JOIN siminfo.t_transfeeratedetail t3
                                        ON(t1.settlementgroupid = t3.settlementgroupid AND t3.instrumentid = '00000000')
                                        WHERE t1.settlementgroupid IN (SELECT settlementgroupid FROM siminfo.t_tradesystemsettlementgroup WHERE tradesystemid = %s)"""
            cursor.execute(sql, (current_trading_day, settlement_id, trade_system_id))

            # 加载客户资金表数据
            logger.info("[load ClientFund to dbclear]......")
            sql = """DELETE FROM dbclear.t_clientfund WHERE tradingday = %s AND settlementgroupid IN (SELECT settlementgroupid FROM siminfo.t_tradesystemsettlementgroup WHERE tradesystemid = %s) AND settlementid = %s"""
            cursor.execute(sql, (current_trading_day, trade_system_id, settlement_id))
            sql = """INSERT INTO dbclear.t_clientfund (TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, AccountID, Available, TransFee, DelivFee, PositionMargin, Profit, StockValue) 
                                SELECT %s, t1.settlementgroupid, %s, t1.participantid, t1.clientid, t1.accountid, 0, 0, 0, 0, 0, 0
                                FROM siminfo.t_clientfund t1
                                WHERE t1.settlementgroupid IN (SELECT settlementgroupid FROM siminfo.t_tradesystemsettlementgroup WHERE tradesystemid = %s)"""
            cursor.execute(sql, (current_trading_day, settlement_id, trade_system_id))

            # 更新结算价
            logger.info("[update future settlementprice to dbclear]......")
            sql = """update dbclear.t_marketdata t, siminfo.t_tradesystemsettlementgroup t2 
                    set t.SettlementPrice = %s where t.InstrumentID = %s
                    and t.TradingDay = %s and t.SettlementID = %s and t.SettlementGroupID = t2.SettlementGroupID
                    and t2.TradeSystemID = %s"""
            params = []
            marketdata = [row for row in csv.DictReader(open(os.path.join(data_target_dir, "future_depthmarketdata.csv")))]
            for data in marketdata:
                params.append((data['SettlementPrice'], data['InstrumentID'], current_trading_day, settlement_id, trade_system_id))
            cursor.executemany(sql, params)
        mysql_conn.commit()
    except Exception as e:
        logger.error(
            "[load data to dbclear with %s] Error: %s" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False), e))
        result_code = -1
    finally:
        mysql_conn.close()
    logger.info("[load csv to database with %s] end" % json.dumps(conf, encoding="UTF-8", ensure_ascii=False))
    return result_code


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["hosts:hosts", "mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    process_assert(prepare_settle_future(context, conf))


if __name__ == "__main__":
    main()
