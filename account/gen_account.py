#-*- coding: UTF-8 -*-

from utils import Configuration, mysql, log, parse_conf_args


def gen_investors(context, conf):
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))

    logger = log.get_logger(category="GenAccount")

    balance_conf = conf["balance"]
    begin = conf["begin"]
    count = conf["count"]
    end = conf["end"]

    logger.info("[gen %d investors start with %d count %s end %s] begin" % (count, begin, count, end))

    id_list_all = []
    id_list_1000 = []
    id_int = begin

    gen_count = 0
    for i in range(0, count):
        while True:
            if 0 < end < id_int:
                break
            gen_count += 1
            id_str = str(id_int).rjust(8, "0")
            id_int += 1
            if id_str.find("4") < 0:
                id_list_1000.append((id_str,))
                if len(id_list_1000) == 1000:
                    id_list_all.append(id_list_1000)
                    id_list_1000 = []
                break

    if 0 < len(id_list_1000) < 1000:
        id_list_all.append(id_list_1000)

    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        for id_list in id_list_all:
            sql = '''INSERT INTO siminfo.t_investor(investorid, password, investorstatus) VALUES (%s, SUBSTR(CONCAT('', FLOOR(RAND() * 10000000 + RAND() * 10 * 10000000)),1, 8), '9')'''
            cursor.executemany(sql, id_list)

        sql = '''INSERT INTO siminfo.t_investorclient(settlementgroupid, investorid, clientid)
                            SELECT 
                              t2.settlementgroupid,
                              t1.investorid,
                              CASE
                                WHEN t2.exchangeid = 'SHFE' 
                                THEN CONCAT('1', t1.investorid) 
                                WHEN t2.exchangeid = 'CFFEX' 
                                THEN CONCAT('2', t1.investorid) 
                                WHEN t2.exchangeid = 'DCE' 
                                THEN CONCAT('3', t1.investorid) 
                                WHEN t2.exchangeid = 'CZCE' 
                                THEN CONCAT('4', t1.investorid)
                                WHEN t2.exchangeid = 'INE' 
                                THEN CONCAT('5', t1.investorid)
                                WHEN t2.exchangeid = 'SGE' 
                                THEN CONCAT('6', t1.investorid)
                                WHEN t2.exchangeid = 'SZSE' 
                                THEN CONCAT('7', t1.investorid)
                                WHEN t2.exchangeid = 'SSE' AND t2.settlementgrouptype = '2'
                                THEN CONCAT('8', t1.investorid)
                                WHEN t2.exchangeid = 'SSE' AND t2.settlementgrouptype = '4'
                                THEN CONCAT('A', t1.investorid)
                                END AS clientid
                                FROM
                                (SELECT 
                                  investorid,
                                  investorstatus 
                                FROM
                                  siminfo.t_investor 
                                WHERE investorstatus = '9') t1,
                                (SELECT 
                                  settlementgroupid,
                                  exchangeid,
                                  settlementgrouptype 
                                FROM
                                  siminfo.t_settlementgroup) t2 '''
        cursor.execute(sql)

        sql = '''INSERT INTO siminfo.t_client(settlementgroupid, clientid, clientname, identifiedcardtype, identifiedcardno, tradingrole, clienttype, isactive, hedgeflag)
                            SELECT t2.settlementgroupid, t2.clientid, t2.clientid, '', '', '1', '0', '1', '1'
                            FROM siminfo.t_investor t1, siminfo.t_investorclient t2
                            WHERE t1.investorid = t2.investorid AND t1.investorstatus = '9' '''
        cursor.execute(sql)

        sql = '''INSERT INTO siminfo.t_partclient(settlementgroupid, participantid, clientid)
                            SELECT t1.settlementgroupid, t1.participantid, t2.clientid
                            FROM siminfo.t_participant t1, siminfo.t_investorclient t2, siminfo.t_investor t3
                            WHERE t1.settlementgroupid = t2.settlementgroupid AND t2.investorid = t3.investorid AND t3.investorstatus = '9' '''
        cursor.execute(sql)

        config_brokers = ""
        for broker_system_id in balance_conf.keys():
            if broker_system_id != "default":
                broker_system_balance = balance_conf[broker_system_id]
                sql = '''INSERT INTO siminfo.t_investorfund(BrokerSystemID,InvestorID,PreBalance,CurrMargin,CloseProfit,Premium,Deposit,Withdraw,Balance,Available,PreMargin,FuturesMargin,OptionsMargin,PositionProfit,Profit,Interest,Fee,
                                          TotalCollateral,CollateralForMargin,PreAccmulateInterest,AccumulateInterest,AccumulateFee,ForzenDeposit,AccountStatus,InitialAsset,PreMonthAsset,PreWeekAsset,PreAsset,CurrentAsset,PreStockValue,StockValue)
                                    SELECT %s,t2.investorid,%s,0,0,0,0,0,%s,%s,0,0,0,0,0,0,0,0,0,0,0,0,0,'0',%s,%s,%s,%s,%s,0,0
                                    FROM siminfo.t_investor t2
                                    WHERE t2.investorstatus = '9' '''
                cursor.execute(sql, (broker_system_id, broker_system_balance, broker_system_balance, broker_system_balance, broker_system_balance, broker_system_balance, broker_system_balance, broker_system_balance, broker_system_balance))
                config_brokers = "'%s'" % broker_system_id if len(config_brokers) == 0 else "%s,'%s'" % (config_brokers, broker_system_id)

        if len(config_brokers) > 0:
            broker_system_balance = balance_conf["default"]
            sql = '''INSERT INTO siminfo.t_investorfund(BrokerSystemID,InvestorID,PreBalance,CurrMargin,CloseProfit,Premium,Deposit,Withdraw,Balance,Available,PreMargin,FuturesMargin,OptionsMargin,PositionProfit,Profit,Interest,Fee,
                                                      TotalCollateral,CollateralForMargin,PreAccmulateInterest,AccumulateInterest,AccumulateFee,ForzenDeposit,AccountStatus,InitialAsset,PreMonthAsset,PreWeekAsset,PreAsset,CurrentAsset,PreStockValue,StockValue)
                                                SELECT t1.brokersystemid,t2.investorid,%s,0,0,0,0,0,%s,%s,0,0,0,0,0,0,0,0,0,0,0,0,0,'0',%s,%s,%s,%s,%s,0,0
                                                FROM siminfo.t_brokersystem t1, siminfo.t_investor t2
                                                WHERE t2.investorstatus = '9' AND t1.brokersystemid not in(''' + config_brokers +''')'''
            cursor.execute(sql, (broker_system_balance, broker_system_balance, broker_system_balance, broker_system_balance, broker_system_balance, broker_system_balance, broker_system_balance, broker_system_balance))

        sql = '''UPDATE siminfo.t_investor SET investorstatus = '0' WHERE investorstatus = '9' '''
        cursor.execute(sql)

        mysql_conn.commit()

    except Exception as e:
        logger.error("[gen %d investors start with %d count %s end %s] Error: %s" % (count, begin, count, end, e))
        gen_count = 0
    finally:
        mysql_conn.close()

    logger.info("[gen %d investors start with %d count %s end %s, generated %s] end" % (count, begin, count, end, gen_count))


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    gen_investors(context, conf)


if __name__ == "__main__":
    main()
