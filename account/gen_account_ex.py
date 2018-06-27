# -*- coding: UTF-8 -*-

from utils import Configuration, mysql, log, parse_conf_args


def gen_investors(context, conf):
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))

    logger = log.get_logger(category="GenAccount")

    balance_conf = conf["balance"]
    settlementgroupid = conf["settlementgroupid"]
    logger.info("[gen investors %s] begin", balance_conf)

    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        config_brokers = ""
        for broker_system_id in balance_conf.keys():
            if broker_system_id != "default":
                broker_system_balance = balance_conf[broker_system_id]
                sql = '''INSERT INTO siminfo.t_investorfund(BrokerSystemID,InvestorID,PreBalance,CurrMargin,CloseProfit,Premium,Deposit,Withdraw,Balance,Available,PreMargin,FuturesMargin,OptionsMargin,PositionProfit,Profit,Interest,Fee,
                                          TotalCollateral,CollateralForMargin,PreAccmulateInterest,AccumulateInterest,AccumulateFee,ForzenDeposit,AccountStatus,InitialAsset,PreMonthAsset,PreWeekAsset,PreAsset,CurrentAsset,PreStockValue,StockValue)
                                    SELECT %s,t2.investorid,%s,0,0,0,0,0,%s,%s,0,0,0,0,0,0,0,0,0,0,0,0,0,'0',%s,%s,%s,%s,%s,0,0
                                    FROM siminfo.t_investor t2 '''
                cursor.execute(sql, (
                    broker_system_id, broker_system_balance, broker_system_balance, broker_system_balance,
                    broker_system_balance, broker_system_balance, broker_system_balance, broker_system_balance,
                    broker_system_balance))
                config_brokers = "'%s'" % broker_system_id if len(config_brokers) == 0 else "%s,'%s'" % (
                    config_brokers, broker_system_id)

        for sgid in settlementgroupid:
            # siminfo.t_partclient;
            sql = """insert into siminfo.t_partclient(SettlementGroupID, ClientID, ParticipantID)
                      select %s, ClientID, ParticipantID from siminfo.t_partclient where SettlementGroupID = %s"""
            cursor.execute(sql, (settlementgroupid.get(sgid), sgid))
            # siminfo.t_client;
            sql = """insert into siminfo.t_client(SettlementGroupID,ClientID,ClientName,IdentifiedCardType,IdentifiedCardNo,TradingRole,ClientType,IsActive,HedgeFlag)
                        select %s,ClientID,ClientName,IdentifiedCardType,IdentifiedCardNo,TradingRole,ClientType,IsActive,HedgeFlag from siminfo.t_client where SettlementGroupID = %s"""
            cursor.execute(sql, (settlementgroupid.get(sgid), sgid))
            # siminfo.t_investorclient;
            sql = """insert into siminfo.t_investorclient(SettlementGroupID, InvestorID, ClientID)
                      select %s, InvestorID, ClientID from siminfo.t_investorclient where SettlementGroupID = %s"""
            cursor.execute(sql, (settlementgroupid.get(sgid), sgid))

        mysql_conn.commit()

    except Exception as e:
        logger.error(e)
    finally:
        mysql_conn.close()

    logger.info("[gen investors %s] end", balance_conf)


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    gen_investors(context, conf)


if __name__ == "__main__":
    main()
