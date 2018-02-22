# -*- coding: UTF-8 -*-

import json

from utils import Configuration, mysql, log, parse_conf_args, process_assert


def settle_stock(context, conf):
    result_code = 0
    logger = log.get_logger(category="SettleStock")

    settlement_group_id = conf.get("settlementGroupId")
    settlement_id = conf.get("settlementId")

    logger.info("[settle stock %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))
    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        logger.info("[get current trading day]......")
        sql = """SELECT t1.tradingday FROM siminfo.t_tradesystemtradingday t1, siminfo.t_tradesystemsettlementgroup t2 WHERE t1.tradesystemid = t2.tradesystemid and t2.settlementgroupid = %s"""
        cursor.execute(sql, (settlement_group_id,))
        row = cursor.fetchone()

        current_trading_day = str(row[0])
        logger.info("[get current trading day] current_trading_day = %s" % (current_trading_day))

        # 检查结算状态
        logger.info("[check settlement status]......")
        sql = """SELECT 
                      t1.tradingday, t1.settlementgroupid, t1.settlementid, t1.settlementstatus
                    FROM
                      dbclear.t_settlement t1
                    WHERE t1.tradingday = %s
                      AND t1.settlementgroupid = %s
                      AND t1.settlementid = %s for update"""
        cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
        row = cursor.fetchone()

        if row is None:
            logger.error("[settle stock] Error: There is no data for %s-%s." % (settlement_group_id, settlement_id))
            result_code = -1
        elif row[3] != '0':
            logger.error("[settle stock] Error: Settlement for %s-%s has done." % (settlement_group_id, settlement_id))
            result_code = -1
        else:
            #计算结算价 股票中结算价设置为收盘价
            logger.info("[calculate settlement price]......")
            sql = """UPDATE dbclear.t_marketdata t SET t.settlementprice = t.closeprice WHERE t .tradingday = %s AND t.settlementgroupid = %s AND t.settlementid = %s"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))

            #计算交易手续费
            logger.info("[calculate trade trans fee]......")
            sql = """DELETE FROM dbclear.t_clienttransfee WHERE settlementgroupid = %s AND settlementid = %s"""
            cursor.execute(sql, (settlement_group_id, settlement_id))
            sql = """INSERT INTO dbclear.t_clienttransfee(TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, AccountID, ProductGroupID, ProductID, UnderlyingInstrID, InstrumentID, TradeID, OrderSysID, Direction, TradingRole, HedgeFlag, OffsetFlag, Volume, Price, TransFeeRatio, ValueMode, MinFee, MaxFee, TransFee)
                                        SELECT t1.tradingday, t1.settlementgroupid, t1.settlementid, t1.participantid, t1.clientid, t1.accountid, t3.productgroupid, t3.productid, t3.underlyinginstrid, t1.instrumentid, t1.tradeid, t1.ordersysid, t1.direction, t1.tradingrole, t1.hedgeflag, t1.offsetflag, t1.volume, t1.price,
                                                   CASE
                                                     WHEN t1.direction = '0' THEN
                                                      t2.openfeeratio
                                                     WHEN t1.direction = '1' THEN
                                                      t2.closeyesterdayfeeratio
                                                   END AS transfeeratio,
                                                   t2.valuemode,
                                                   CASE
                                                     WHEN t1.direction = '0' THEN
                                                      t2.minopenfee
                                                     WHEN t1.direction = '1' THEN
                                                      t2.minclosefee
                                                   END AS minfee,
                                                   CASE
                                                     WHEN t1.direction = '0' THEN
                                                      t2.maxopenfee
                                                     WHEN t1.direction = '1' THEN
                                                      t2.maxclosefee
                                                   END AS maxfee,
                                                   IF(t2.valuemode='2',
                                                          ROUND((CASE
                                                                  WHEN t1.direction = '0' THEN
                                                                   t2.openfeeratio
                                                                  WHEN t1.direction = '1' THEN
                                                                   t2.closeyesterdayfeeratio
                                                                END) * t1.volume * t3.volumemultiple,
                                                                2),
                                                          ROUND((CASE
                                                                  WHEN t1.direction = '0' THEN
                                                                   t2.openfeeratio
                                                                  WHEN t1.direction = '1' THEN
                                                                   t2.closeyesterdayfeeratio
                                                                END) * t1.price * t1.volume * t3.volumemultiple,
                                                                2)) AS transfee
                                                    FROM dbclear.t_trade t1, dbclear.t_clienttransfeeratio t2, siminfo.t_instrument t3
                                                    WHERE t1.tradingday = t2.tradingday AND t1.settlementgroupid = t2.settlementgroupid AND t1.settlementid = t2.settlementid
                                                    AND t2.participantid = '00000000' AND t2.clientid = '00000000' AND t1.instrumentid = t2.instrumentid
                                                    AND t1.tradingrole = t2.tradingrole AND t1.hedgeflag = t2.hedgeflag AND t1.settlementgroupid = t3.settlementgroupid
                                                    AND t1.instrumentid = t3.instrumentid AND t1.tradingday = %s AND t1.settlementgroupid = %s
                                                    AND t1.settlementid = %s"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            sql = """INSERT INTO dbclear.t_clienttransfee(TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, AccountID, ProductGroupID, ProductID, UnderlyingInstrID, InstrumentID, TradeID, OrderSysID, Direction, TradingRole, HedgeFlag, OffsetFlag, Volume, Price, TransFeeRatio, ValueMode, MinFee, MaxFee, TransFee)
                                        SELECT t1.tradingday, t1.settlementgroupid, t1.settlementid, t1.participantid, t1.clientid, t1.accountid, t3.productgroupid, t3.productid, t3.underlyinginstrid, t1.instrumentid, t1.tradeid, t1.ordersysid, t1.direction, t1.tradingrole, t1.hedgeflag, t1.offsetflag, t1.volume, t1.price,
                                                   CASE
                                                     WHEN t1.direction = '0' THEN
                                                      t2.openfeeratio
                                                     WHEN t1.direction = '1' THEN
                                                      t2.closeyesterdayfeeratio
                                                   END AS transfeeratio,
                                                   t2.valuemode,
                                                   CASE
                                                     WHEN t1.direction = '0' THEN
                                                      t2.minopenfee
                                                     WHEN t1.direction = '1' THEN
                                                      t2.minclosefee
                                                   END AS minfee,
                                                   CASE
                                                     WHEN t1.direction = '0' THEN
                                                      t2.maxopenfee
                                                     WHEN t1.direction = '1' THEN
                                                      t2.maxclosefee
                                                   END AS maxfee,
                                                   IF(t2.valuemode='2',
                                                          ROUND((CASE
                                                                  WHEN t1.direction = '0' THEN
                                                                   t2.openfeeratio
                                                                  WHEN t1.direction = '1' THEN
                                                                   t2.closeyesterdayfeeratio
                                                                END) * t1.volume * t3.volumemultiple,
                                                                2),
                                                          ROUND((CASE
                                                                  WHEN t1.direction = '0' THEN
                                                                   t2.openfeeratio
                                                                  WHEN t1.direction = '1' THEN
                                                                   t2.closeyesterdayfeeratio
                                                                END) * t1.price * t1.volume * t3.volumemultiple,
                                                                2)) AS transfee
                                                    FROM dbclear.t_trade t1, dbclear.t_clienttransfeeratio t2, siminfo.t_instrument t3
                                                    WHERE t1.tradingday = t2.tradingday AND t1.settlementgroupid = t2.settlementgroupid AND t1.settlementid = t2.settlementid
                                                    AND t2.participantid = t1.participantid AND t2.clientid = '00000000' AND t1.instrumentid = t2.instrumentid
                                                    AND t1.tradingrole = t2.tradingrole AND t1.hedgeflag = t2.hedgeflag AND t1.settlementgroupid = t3.settlementgroupid
                                                    AND t1.instrumentid = t3.instrumentid AND t1.tradingday = %s AND t1.settlementgroupid = %s
                                                    AND t1.settlementid = %s
                                                    ON DUPLICATE KEY UPDATE transfeeratio = VALUES(transfeeratio), valuemode = VALUES(valuemode),
                                                            minfee = VALUES(minfee), maxfee = VALUES(maxfee), transfee = VALUES(transfee)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))
            sql = """INSERT INTO dbclear.t_clienttransfee(TradingDay, SettlementGroupID, SettlementID, ParticipantID, ClientID, AccountID, ProductGroupID, ProductID, UnderlyingInstrID, InstrumentID, TradeID, OrderSysID, Direction, TradingRole, HedgeFlag, OffsetFlag, Volume, Price, TransFeeRatio, ValueMode, MinFee, MaxFee, TransFee)
                                        SELECT t1.tradingday, t1.settlementgroupid, t1.settlementid, t1.participantid, t1.clientid, t1.accountid, t3.productgroupid, t3.productid, t3.underlyinginstrid, t1.instrumentid, t1.tradeid, t1.ordersysid, t1.direction, t1.tradingrole, t1.hedgeflag, t1.offsetflag, t1.volume, t1.price,
                                                   CASE
                                                     WHEN t1.direction = '0' THEN
                                                      t2.openfeeratio
                                                     WHEN t1.direction = '1' THEN
                                                      t2.closeyesterdayfeeratio
                                                   END AS transfeeratio,
                                                   t2.valuemode,
                                                   CASE
                                                     WHEN t1.direction = '0' THEN
                                                      t2.minopenfee
                                                     WHEN t1.direction = '1' THEN
                                                      t2.minclosefee
                                                   END AS minfee,
                                                   CASE
                                                     WHEN t1.direction = '0' THEN
                                                      t2.maxopenfee
                                                     WHEN t1.direction = '1' THEN
                                                      t2.maxclosefee
                                                   END AS maxfee,
                                                   IF(t2.valuemode='2',
                                                          ROUND((CASE
                                                                  WHEN t1.direction = '0' THEN
                                                                   t2.openfeeratio
                                                                  WHEN t1.direction = '1' THEN
                                                                   t2.closeyesterdayfeeratio
                                                                END) * t1.volume * t3.volumemultiple,
                                                                2),
                                                          ROUND((CASE
                                                                  WHEN t1.direction = '0' THEN
                                                                   t2.openfeeratio
                                                                  WHEN t1.direction = '1' THEN
                                                                   t2.closeyesterdayfeeratio
                                                                END) * t1.price * t1.volume * t3.volumemultiple,
                                                                2)) AS transfee
                                                    FROM dbclear.t_trade t1, dbclear.t_clienttransfeeratio t2, siminfo.t_instrument t3
                                                    WHERE t1.tradingday = t2.tradingday AND t1.settlementgroupid = t2.settlementgroupid AND t1.settlementid = t2.settlementid
                                                    AND t2.participantid = t1.participantid AND t2.clientid = t1.clientid AND t1.instrumentid = t2.instrumentid
                                                    AND t1.tradingrole = t2.tradingrole AND t1.hedgeflag = t2.hedgeflag AND t1.settlementgroupid = t3.settlementgroupid
                                                    AND t1.instrumentid = t3.instrumentid AND t1.tradingday = %s AND t1.settlementgroupid = %s
                                                    AND t1.settlementid = %s
                                                    ON DUPLICATE KEY UPDATE transfeeratio = VALUES(transfeeratio), valuemode = VALUES(valuemode),
                                                            minfee = VALUES(minfee), maxfee = VALUES(maxfee), transfee = VALUES(transfee)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))

            # 合并客户手续费
            logger.info("[calculate client trans fee]......")
            sql = """INSERT INTO dbclear.t_clientfund(tradingday, settlementgroupid, settlementid, participantid, clientid, accountid, available, transfee, delivfee, positionmargin, profit, stockvalue)
                                SELECT t.tradingday, t.settlementgroupid, t.settlementid, t.participantid, t.clientid, t.accountid, 0,
                                    SUM(CASE WHEN t.calctransfee < t.minfee THEN t.minfee WHEN t.calctransfee > t.maxfee THEN t.minfee ELSE t.calctransfee END) AS transfee, 0, 0, 0, 0
                                    FROM(SELECT tt.tradingday, tt.settlementgroupid, tt.settlementid, tt.participantid, tt.clientid, tt.accountid, tt.ordersysid, tt.minfee, tt.maxfee,
                                          SUM(tt.transfee) AS calctransfee
                                        FROM dbclear.t_clienttransfee tt 
                                        WHERE tt.tradingday = %s AND tt.settlementgroupid = %s AND tt.settlementid = %s
                                        GROUP BY tt.tradingday, tt.settlementgroupid,tt.settlementid, tt.participantid, tt.clientid, tt.accountid, tt.ordersysid, tt.minfee, tt.maxfee ) t 
                                    GROUP BY t.tradingday, t.settlementgroupid, t.settlementid, t.participantid, t.clientid, t.accountid
                                    ON DUPLICATE KEY UPDATE dbclear.t_clientfund.transfee = VALUES(transfee)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))

            # 更新客户可用资金变化
            logger.info("[calculate client available change]......")
            sql = """INSERT INTO dbclear.t_clientfund(tradingday, settlementgroupid, settlementid, participantid, clientid, accountid, available, transfee, delivfee, positionmargin, profit, stockvalue)
                                SELECT t1.tradingday, t1.settlementgroupid, t1.settlementid, t1.participantid, t1.clientid, t1.accountid, SUM(IF(t1.direction = '0', -1 * t1.volume * t1.price, t1.volume * t1.price) * t2.volumemultiple) AS available, 0, 0, 0, 0, 0
                                    FROM dbclear.t_trade t1, siminfo.t_instrument t2
                                    WHERE t1.settlementgroupid = t2.settlementgroupid AND t1.instrumentid = t2.instrumentid
                                    AND t1.tradingday = %s AND t1.settlementgroupid = %s AND t1.settlementid = %s
                                    GROUP BY t1.tradingday, t1.settlementgroupid, t1.settlementid, t1.participantid, t1.clientid, t1.accountid
                                    ON DUPLICATE KEY UPDATE dbclear.t_clientfund.available = VALUES(available)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))

            # 更新客户股票市值
            logger.info("[calculate client stock value]......")
            sql = """INSERT INTO dbclear.t_clientfund(tradingday, settlementgroupid, settlementid, participantid, clientid, accountid, available, transfee, delivfee, positionmargin, profit, stockvalue)
                                            SELECT t1.tradingday, t1.settlementgroupid, t1.settlementid, t1.participantid, t1.clientid, t3.accountid, 0, 0, 0, 0, 0, SUM(t1.position * t2.settlementprice) AS stockvalue
                                            FROM dbclear.t_clientposition t1, dbclear.t_marketdata t2, siminfo.t_account t3
                                            WHERE t1.tradingday = t2.tradingday AND t1.settlementgroupid = t2.settlementgroupid AND t1.settlementid = t2.settlementid
                                                AND t1.instrumentid = t2.instrumentid AND t1.settlementgroupid = t3.settlementgroupid AND t1.participantid = t3.participantid
                                                AND t1.tradingday = %s AND t1.settlementgroupid = %s AND t1.settlementid = %s
                                            GROUP BY t1.tradingday, t1.settlementgroupid, t1.settlementid, t1.participantid, t1.clientid, t3.accountid
                                                ON DUPLICATE KEY UPDATE dbclear.t_clientfund.stockvalue = VALUES(stockvalue)"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))

            # 更新结算状态
            logger.info("[update settlement status]......")
            sql = """UPDATE dbclear.t_settlement SET settlementstatus = '1' WHERE tradingday = %s AND settlementgroupid = %s AND settlementid = %s AND settlementstatus = '0'"""
            cursor.execute(sql, (current_trading_day, settlement_group_id, settlement_id))

        mysql_conn.commit()
    except Exception as e:
        logger.error("[settle stock] Error: %s" % (e))
        result_code = -1
    finally:
        mysql_conn.close()
    logger.info("[settle stock] end")
    return result_code


def main():
    base_dir, config_names, config_files = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    process_assert(settle_stock(context, conf))


if __name__ == "__main__":
    main()