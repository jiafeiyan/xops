# -*- coding: UTF-8 -*-

"""
t_ClearingTradingPart.csv

t_ClientPosition.csv
t_PartPosition.csv

t_Client.csv
t_PartClient.csv

t_Account.csv
t_BaseReserveAccount.csv
t_PartRoleAccount.csv
t_PartTopicSubscribe.csv
t_Participant.csv
t_User.csv
"""

import os
import csv

from utils import log, parse_conf_args, path, Configuration, mysql, csv_tool


class ex_exchange_stock_csv:
    def __init__(self, context, configs):
        self.TradeSystemID = configs.get("tradeSystemID")
        self.SettlementGroupID = configs.get("settlementGroupID")
        self.initialfunds = configs.get("initialfunds")
        log_conf = None if context.get("log") is None else context.get("log").get(configs.get("logId"))
        # 初始化日志
        self.logger = log.get_logger(category="exchange_stock_csv", configs=log_conf)
        if log_conf is None:
            self.logger.warning("exchange_stock_csv未配置Log日志")
        # 初始化数据库连接
        self.mysqlDB = mysql(configs=context.get("mysql")[configs.get("mysqlId")])
        # 初始化生成CSV文件路径
        output = path.convert(context.get("csv")[configs.get("csv")]['exchange'])
        self.csv_path = os.path.join(output, str(configs.get("tradeSystemID")))
        self.__append_extra_content()

    def __append_extra_content(self):
        self.__append_csv("t_Account")
        self.__append_csv("t_BaseReserveAccount")
        self.__append_csv("t_PartRoleAccount")
        self.__append_csv("t_PartTopicSubscribe")
        self.__append_csv("t_Participant")
        self.__append_csv("t_User")
        self.__append_csv("t_Client")
        self.__append_csv("t_PartClient")
        self.__append_csv("t_UserFunctionRight")
        self.__append_csv("t_UserIP")
        self.__append_csv("t_TradingAccount")
        self.__append_csv("t_ClientPosition")
        self.__append_csv("t_PartPosition")
        # 生成机器人报单数据
        self.__gen_robot_csv("order_info")

    def __append_csv(self, table_name):
        table_sqls = dict(
            t_Account=dict(sql="""SELECT 'SG01' AS SettlementGroupID,AccountID,ParticipantID,Currency
                                  FROM siminfo.t_Account WHERE SettlementGroupID=%s""",
                           quoting=True),
            t_BaseReserveAccount=dict(sql="""SELECT t1.TradingDay,'SG01' AS SettlementGroupID,'1' AS SettlementID,ParticipantID,AccountID,Reserve
                                                FROM siminfo.t_BaseReserveAccount t,siminfo.t_TradeSystemTradingDay t1
                                                WHERE t.SettlementGroupID = %s and t1.TradeSystemID = %s""",
                                      params=(self.SettlementGroupID, self.TradeSystemID),
                                      quoting=True),
            t_PartRoleAccount=dict(sql="""SELECT t1.TradingDay,'SG01' AS SettlementGroupID,'1' AS SettlementID,ParticipantID,TradingRole,AccountID
                                            FROM siminfo.t_PartRoleAccount t,siminfo.t_TradeSystemTradingDay t1
                                            WHERE t.SettlementGroupID = %s AND t1.TradeSystemID = %s""",
                                   params=(self.SettlementGroupID, self.TradeSystemID),
                                   quoting=True),
            t_PartTopicSubscribe=dict(sql="""SELECT DISTINCT ParticipantID,ParticipantType,TopicID
                                            FROM siminfo.t_PartTopicSubscribe t where t.SettlementGroupID = %s""",
                                      quoting=True),
            t_Participant=dict(sql="""SELECT ParticipantID,ParticipantName,ParticipantAbbr,MemberType,IsActive
                                      FROM siminfo.t_Participant t WHERE t.SettlementGroupID = %s""",
                               quoting=True),
            t_User=dict(sql="""SELECT DISTINCT ParticipantID,UserID,UserType,Password,IsActive
                               FROM siminfo.t_User WHERE SettlementGroupID = %s""",
                        quoting=True),
            t_Client=dict(sql="""SELECT ClientID,ClientName,IdentifiedCardType,IdentifiedCardNo,
                                        TradingRole,ClientType,IsActive,HedgeFlag
                                  FROM siminfo.t_Client WHERE SettlementGroupID = %s""",
                          quoting=True),
            t_PartClient=dict(sql="""SELECT ClientID,ParticipantID 
                                     FROM siminfo.t_PartClient WHERE SettlementGroupID=%s""",
                              quoting=True),
            t_UserFunctionRight=dict(sql="""SELECT DISTINCT UserID,FunctionCode
                                            FROM siminfo.t_UserFunctionRight where UserID in (%s, %s)""",
                                     params=('R000101', 'R000102'),
                                     quoting=True),
            t_UserIP=dict(sql="""SELECT DISTINCT UserID,IPAddress,IPMask
                                              FROM siminfo.t_UserIP WHERE SettlementGroupID=%s""",
                          quoting=True),
            t_TradingAccount=dict(sql="""SELECT t1.TradingDay,'SG01' AS SettlementGroupID,'1' AS SettlementID,
                                            PreBalance,CurrMargin,CloseProfit,Premium,Deposit,Withdraw,
                                            Balance,Available,AccountID,FrozenMargin,FrozenPremium
                                            FROM siminfo.t_TradingAccount t,siminfo.t_TradeSystemTradingDay t1
                                            WHERE t.SettlementGroupID = %s and t1.TradeSystemID = %s""",
                                  params=(self.SettlementGroupID, self.TradeSystemID),
                                  quoting=True),
            t_ClientPosition=dict(sql="""SELECT
                                        t2.TradingDay,
                                        'SG01' AS SettlementGroupID,
                                        '1' AS SettlementID,
                                        '1' AS HedgeFlag,
                                        '3' AS PosiDirection,
                                        %s AS YdPosition,
                                        '0' AS Position,
                                        '0' AS LongFrozen,
                                        '0' AS ShortFrozen,
                                        '0' AS YdLongFrozen,
                                        '0' AS YdShortFrozen,
                                        '0' AS BuyTradeVolume,
                                        '0' AS SellTradeVolume,
                                        '0' AS PositionCost,
                                        '0' AS YdPositionCost,
                                        '0' AS UseMargin,
                                        '0' AS FrozenMargin,
                                        '0' AS LongFrozenMargin,
                                        '0' AS ShortFrozenMargin,
                                        '0' AS FrozenPremium,
                                        InstrumentID,
                                        t3.ParticipantID,
                                        t3.ClientID 
                                    FROM
                                        siminfo.t_instrument t,
                                        siminfo.t_tradesystemsettlementgroup t1,
                                        siminfo.t_tradesystemtradingday t2,
                                        siminfo.t_partclient t3 
                                    WHERE
                                        t.SettlementGroupID = t1.SettlementGroupID 
                                        AND t1.TradeSystemID = t2.TradeSystemID 
                                        AND t3.SettlementGroupID = %s 
                                        AND t1.TradeSystemID = %s""",
                                  params=(self.initialfunds, self.SettlementGroupID, self.TradeSystemID)),
            t_PartPosition=dict(sql="""select 
                                          t2.TradingDay,
                                            'SG01' AS SettlementGroupID,
                                            '1' as SettlementID,
                                            '1' as HedgeFlag,
                                            '3' as PosiDirection,
                                            %s as YdPosition,
                                            '0' as Position,
                                            '0' as LongFrozen,
                                            '0' as ShortFrozen,
                                            '0' as YdLongFrozen,
                                            '0' as YdShortFrozen,
                                            t.InstrumentID,
                                            t3.ParticipantID,
                                            '1' as TradingRole 
                                        FROM
                                            siminfo.t_instrument t,
                                            siminfo.t_tradesystemsettlementgroup t1,
                                            siminfo.t_tradesystemtradingday t2,
                                            siminfo.t_participant t3 
                                        WHERE
                                            t.SettlementGroupID = t1.SettlementGroupID 
                                            AND t1.TradeSystemID = t2.TradeSystemID 
                                            AND t3.SettlementGroupID = %s
                                            AND t1.TradeSystemID = %s""",
                                    params=(self.initialfunds, self.SettlementGroupID, self.TradeSystemID)),
        )

        csv_data = self.mysqlDB.select(table_sqls[table_name]["sql"],
                                       (self.SettlementGroupID,) if "params" not in table_sqls[table_name] else
                                       table_sqls[table_name]['params'])
        # 追加到原始csv文件中
        self.__handle_csv(table_name, csv_data, table_sqls[table_name].get('quoting'))

    def __handle_csv(self, table_name, data_set, quoting=None):
        self.logger.info("%s%s%s" % ("开始追加 [", table_name, ".csv] 数据"))
        _path = "%s%s%s%s" % (str(self.csv_path), os.path.sep, table_name, '.csv')
        if not os.path.exists(_path):
            self.logger.error("%s%s%s" % ("文件", table_name, ".csv不存在！"))
        else:
            with open(_path, "ab+") as target:
                if quoting:
                    writer = csv.writer(target, quoting=csv.QUOTE_ALL)
                else:
                    writer = csv.writer(target)
                writer.writerows(csv_tool.covert_to_gbk(data_set))
            self.logger.info("%s%s%s" % ("追加 [", table_name, "] 数据完成"))

    def __gen_robot_csv(self, table_name):
        sql = """SELECT t.SettlementGroupID,t.InstrumentID,t1.PreClosePrice,t2.ValueMode,
                                t2.LowerValue,t2.UpperValue,t.PriceTick ,t4.VolumeMultiple
                    FROM siminfo.t_instrumentproperty t,siminfo.t_marketdata t1,
                            siminfo.t_pricebanding t2,siminfo.t_instrument t4,
                            siminfo.t_tradesystemsettlementgroup t5
                    WHERE t.InstrumentID = t1.InstrumentID 
                            AND t.InstrumentID = t2.InstrumentID 
                            AND t.SettlementGroupID = t1.SettlementGroupID 
                            AND t.SettlementGroupID = t2.SettlementGroupID
                            AND t.InstrumentID = t4.InstrumentID 
                            AND t.SettlementGroupID = t4.SettlementGroupID
                            and t.SettlementGroupID = t5.SettlementGroupID
                            and t5.TradeSystemID = %s"""
        columns = dict(columns=("SettlementGroupID", "InstrumentID", "PreClosePrice", "ValueMode", "LowerValue", "UpperValue", "PriceTick", "VolumeMultiple"))
        csv_data = self.mysqlDB.select(sql, (self.TradeSystemID,))
        # 生成csv文件
        self.__produce_csv(table_name, columns, csv_data)

    # 生成csv文件
    def __produce_csv(self, table_name, columns, csv_data):
        self.logger.info("%s%s%s" % ("开始生成 ", table_name, ".csv"))
        _path = "%s%s%s%s" % (str(self.csv_path), os.path.sep, table_name, '.csv')
        # 如果不存在目录则先创建
        if not os.path.exists(str(self.csv_path)):
            os.makedirs(str(self.csv_path))
        with open(_path, 'wb') as csvfile:
            if "quoting" in columns and columns['quoting']:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            else:
                writer = csv.writer(csvfile)
            writer.writerow(csv_tool.covert_to_gbk(columns['columns']))
            writer.writerows(csv_tool.covert_to_gbk(csv_data))
        self.logger.info("%s%s%s" % ("生成 ", table_name, ".csv 文件完成"))


if __name__ == '__main__':
    base_dir, config_names, config_files, add_ons = parse_conf_args(__file__, config_names=["mysql", "log", "csv"])
    context, conf = Configuration.load(base_dir=base_dir, config_names=config_names, config_files=config_files)
    # 启动脚本
    ex_exchange_stock_csv(context=context, configs=conf)
