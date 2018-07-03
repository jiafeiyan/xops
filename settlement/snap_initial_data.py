# -*- coding: UTF-8 -*-

import json

from utils import log, mysql, Configuration, parse_conf_args, process_assert


def snap_data(context, conf):
    result_code = 0
    logger = log.get_logger(category="SnapInitialData")

    broker_system_id = conf.get("brokerSystemId")

    logger.info("[snap initial data %s] begin" % (json.dumps(conf, encoding="UTF-8", ensure_ascii=False)))
    mysql_pool = mysql(configs=context.get("mysql").get(conf.get("mysqlId")))
    mysql_conn = mysql_pool.get_cnx()
    mysql_conn.set_charset_collation('utf8')
    try:
        mysql_conn.start_transaction()

        cursor = mysql_conn.cursor()

        logger.info("[get current trading day]......")
        sql = """SELECT 
                              DISTINCT t1.tradingday 
                            FROM
                              siminfo.t_tradesystemtradingday t1,
                              siminfo.t_tradesystemsettlementgroup t2,
                              siminfo.t_brokersystemsettlementgroup t3 
                            WHERE t1.tradesystemid = t2.tradesystemid 
                              AND t2.settlementgroupid = t3.settlementgroupid 
                              AND t3.brokersystemid = %s"""
        cursor.execute(sql, (broker_system_id,))
        row = cursor.fetchone()

        current_trading_day = str(row[0])
        logger.info("[get current trading day] current_trading_day = %s" % (current_trading_day))

        logger.info("[snap investor fund]......")
        sql = """INSERT INTO snap.t_s_investorfund (
                        TradingDay,	BrokerSystemID,	InvestorID,	PreBalance,	CurrMargin,	CloseProfit,	Premium,	Deposit,	Withdraw,	Balance,	Available,	PreMargin,	FuturesMargin,	OptionsMargin,	PositionProfit,	Profit,	Interest,	Fee,	TotalCollateral,	CollateralForMargin,	PreAccmulateInterest,	AccumulateInterest,	AccumulateFee,	ForzenDeposit,	AccountStatus,	InitialAsset,	PreMonthAsset,	PreWeekAsset,	PreAsset,	CurrentAsset,	PreStockValue,	StockValue 
                    ) SELECT %s,BrokerSystemID,InvestorID,PreBalance,CurrMargin,CloseProfit,Premium,Deposit,Withdraw,Balance,Available,PreMargin,FuturesMargin,OptionsMargin,PositionProfit,Profit,Interest,Fee,TotalCollateral,CollateralForMargin,PreAccmulateInterest,AccumulateInterest,AccumulateFee,ForzenDeposit,AccountStatus,InitialAsset,PreMonthAsset,PreWeekAsset,PreAsset,CurrentAsset,PreStockValue,StockValue 
                    FROM siminfo.t_investorfund WHERE BrokerSystemID = %s"""
        cursor.execute(sql, (current_trading_day, broker_system_id,))

        logger.info("[snap client position]......")
        sql = """insert into snap.t_s_clientposition (TradingDay,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,YdPosition,Position,LongFrozen,ShortFrozen,YdLongFrozen,YdShortFrozen,BuyTradeVolume,SellTradeVolume,PositionCost,YdPositionCost,UseMargin,FrozenMargin,LongFrozenMargin,ShortFrozenMargin,FrozenPremium,InstrumentID,ParticipantID,ClientID)
                        select %s,t.SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,YdPosition,Position,LongFrozen,ShortFrozen,YdLongFrozen,YdShortFrozen,BuyTradeVolume,SellTradeVolume,PositionCost,YdPositionCost,UseMargin,FrozenMargin,LongFrozenMargin,ShortFrozenMargin,FrozenPremium,InstrumentID,ParticipantID,ClientID
                        from siminfo.t_clientposition t, siminfo.t_brokersystemsettlementgroup t1 WHERE t.SettlementGroupID = t1.SettlementGroupID and t1.BrokerSystemID = %s and t.TradingDay = %s"""
        cursor.execute(sql, (current_trading_day, broker_system_id, current_trading_day))

        logger.info("[snap future position dtl]......")
        sql = """insert into snap.t_s_futurepositiondtl (TradingDay,SettlementGroupID,SettlementID,InstrumentID,ParticipantID,ClientID,HedgeFlag,Direction,OpenDate,TradeID,Volume,OpenPrice,TradeType,CombInstrumentID,ExchangeID,CloseProfitByDate,CloseProfitByTrade,PositionProfitByDate,PositionProfitByTrade,Margin,ExchMargin,MarginRateByMoney,MarginRateByVolume,LastSettlementPrice,SettlementPrice,CloseVolume,CloseAmount)
                        select %s,t.SettlementGroupID,SettlementID,InstrumentID,ParticipantID,ClientID,HedgeFlag,Direction,OpenDate,TradeID,Volume,OpenPrice,TradeType,CombInstrumentID,ExchangeID,CloseProfitByDate,CloseProfitByTrade,PositionProfitByDate,PositionProfitByTrade,Margin,ExchMargin,MarginRateByMoney,MarginRateByVolume,LastSettlementPrice,SettlementPrice,CloseVolume,CloseAmount
                        from siminfo.t_futurepositiondtl t, siminfo.t_brokersystemsettlementgroup t1 WHERE t.SettlementGroupID = t1.SettlementGroupID and t1.BrokerSystemID = %s and t.TradingDay = %s"""
        cursor.execute(sql, (current_trading_day, broker_system_id, current_trading_day))

        mysql_conn.commit()
    except Exception as e:
        logger.error("[snap initial data] Error: %s" % e)
        result_code = -1
    finally:
        mysql_conn.close()
    logger.info("[snap initial data] end")
    return result_code


def main():
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql"])

    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)

    process_assert(snap_data(context, conf))


if __name__ == "__main__":
    main()