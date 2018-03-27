-- ******************************
-- 创建结算会话表
-- ******************************
create table dbclear.t_Settlement
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,SettlementStatus   char(1) binary  not null COMMENT '结算状态'
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,SettlementID)
) COMMENT='结算会话';



-- ******************************
-- 创建会员合约持仓表
-- ******************************
create table dbclear.t_PartPosition
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,HedgeFlag   char(1) binary  not null COMMENT '投机套保标志'
	,PosiDirection   char(1) binary  not null COMMENT '持仓多空方向'
	,YdPosition    bigInt(10)    not null COMMENT '上日持仓'
	,Position    bigInt(10)    not null COMMENT '今日持仓'
	,LongFrozen    bigInt(10)    not null COMMENT '多头冻结'
	,ShortFrozen    bigInt(10)    not null COMMENT '空头冻结'
	,YdLongFrozen    bigInt(10)    not null COMMENT '昨日多头冻结'
	,YdShortFrozen    bigInt(10)    not null COMMENT '昨日空头冻结'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,TradingRole   char(1) binary  not null COMMENT '交易角色'
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,InstrumentID,ParticipantID,TradingRole)
) COMMENT='会员合约持仓';



-- ******************************
-- 创建客户合约持仓表
-- ******************************
create table dbclear.t_ClientPosition
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,HedgeFlag   char(1) binary  not null COMMENT '投机套保标志'
	,PosiDirection   char(1) binary  not null COMMENT '持仓多空方向'
	,YdPosition    bigInt(10)    not null COMMENT '上日持仓'
	,Position    bigInt(10)    not null COMMENT '今日持仓'
	,LongFrozen    bigInt(10)    not null COMMENT '多头冻结'
	,ShortFrozen    bigInt(10)    not null COMMENT '空头冻结'
	,YdLongFrozen    bigInt(10)    not null COMMENT '昨日多头冻结'
	,YdShortFrozen    bigInt(10)    not null COMMENT '昨日空头冻结'
	,BuyTradeVolume    bigInt(10)    not null COMMENT '当日买成交量'
	,SellTradeVolume    bigInt(10)    not null COMMENT '当日卖成交量'
	,PositionCost 	   decimal(19,3)   not null COMMENT '持仓成本'
	,YdPositionCost 	   decimal(19,3)   not null COMMENT '昨日持仓成本'
	,UseMargin 	   decimal(19,3)   not null COMMENT '占用的保证金'
	,FrozenMargin 	   decimal(19,3)   not null COMMENT '冻结的保证金'
	,LongFrozenMargin 	   decimal(19,3)   not null COMMENT '多头冻结的保证金'
	,ShortFrozenMargin 	   decimal(19,3)   not null COMMENT '空头冻结的保证金'
	,FrozenPremium 	   decimal(19,3)   not null COMMENT '冻结的权利金'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,InstrumentID,ParticipantID,ClientID)
) COMMENT='客户合约持仓';



-- ******************************
-- 创建客户分红股票持仓表
-- ******************************
create table dbclear.t_ClientPositionForSecurityProfit
(
	DJDate   varchar(8) binary  not null COMMENT '登记日期'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,HedgeFlag   char(1) binary  not null COMMENT '投机套保标志'
	,PosiDirection   char(1) binary  not null COMMENT '持仓多空方向'
	,YdPosition    bigInt(10)    not null COMMENT '上日持仓'
	,Position    bigInt(10)    not null COMMENT '今日持仓'
	,LongFrozen    bigInt(10)    not null COMMENT '多头冻结'
	,ShortFrozen    bigInt(10)    not null COMMENT '空头冻结'
	,YdLongFrozen    bigInt(10)    not null COMMENT '昨日多头冻结'
	,YdShortFrozen    bigInt(10)    not null COMMENT '昨日空头冻结'
	,BuyTradeVolume    bigInt(10)    not null COMMENT '当日买成交量'
	,SellTradeVolume    bigInt(10)    not null COMMENT '当日卖成交量'
	,PositionCost 	   decimal(19,3)   not null COMMENT '持仓成本'
	,YdPositionCost 	   decimal(19,3)   not null COMMENT '昨日持仓成本'
	,UseMargin 	   decimal(19,3)   not null COMMENT '占用的保证金'
	,FrozenMargin 	   decimal(19,3)   not null COMMENT '冻结的保证金'
	,LongFrozenMargin 	   decimal(19,3)   not null COMMENT '多头冻结的保证金'
	,ShortFrozenMargin 	   decimal(19,3)   not null COMMENT '空头冻结的保证金'
	,FrozenPremium 	   decimal(19,3)   not null COMMENT '冻结的权利金'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	  ,PRIMARY KEY (DJDate,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,InstrumentID,ParticipantID,ClientID)
) COMMENT='客户分红股票持仓';



-- ******************************
-- 创建市场行情表
-- ******************************
create table dbclear.t_MarketData
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,LastPrice 	   decimal(16,6)    COMMENT '最新价'
	,PreSettlementPrice 	   decimal(16,6)    COMMENT '昨结算'
	,PreClosePrice 	   decimal(16,6)    COMMENT '昨收盘'
	,UnderlyingClosePx 	   decimal(16,6)    COMMENT '标的昨收盘'
	,PreOpenInterest 	   decimal(19,3)   not null COMMENT '昨持仓量'
	,OpenPrice 	   decimal(16,6)    COMMENT '今开盘'
	,HighestPrice 	   decimal(16,6)    COMMENT '最高价'
	,LowestPrice 	   decimal(16,6)    COMMENT '最低价'
	,Volume    bigInt(10)     COMMENT '数量'
	,Turnover 	   decimal(19,3)    COMMENT '成交金额'
	,OpenInterest 	   decimal(19,3)    COMMENT '持仓量'
	,ClosePrice 	   decimal(16,6)    COMMENT '今收盘'
	,SettlementPrice 	   decimal(16,6)    COMMENT '今结算'
	,UpperLimitPrice 	   decimal(16,6)    COMMENT '涨停板价'
	,LowerLimitPrice 	   decimal(16,6)    COMMENT '跌停板价'
	,PreDelta 	   decimal(22,6)    COMMENT '昨虚实度'
	,CurrDelta 	   decimal(22,6)    COMMENT '今虚实度'
	,UpdateTime   varchar(8) binary   COMMENT '最后修改时间'
	,UpdateMillisec   INTEGER    COMMENT '最后修改毫秒'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,SettlementID,InstrumentID)
) COMMENT='市场行情';



-- ******************************
-- 创建成交表
-- ******************************
create table dbclear.t_Trade
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,TradeID   varchar(12) binary  not null COMMENT '成交编号'
	,Direction   char(1) binary  not null COMMENT '买卖方向'
	,OrderSysID   varchar(12) binary   COMMENT '报单编号'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	,TradingRole   char(1) binary  not null COMMENT '交易角色'
	,AccountID   varchar(12) binary  not null COMMENT '资金帐号'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,OffsetFlag   char(1) binary  not null COMMENT '开平标志'
	,HedgeFlag   char(1) binary  not null COMMENT '投机套保标志'
	,Price 	   decimal(16,6)   not null COMMENT '价格'
	,Volume    bigInt(10)    not null COMMENT '数量'
	,TradeTime   varchar(8) binary  not null COMMENT '成交时间'
	,TradeType   char(1) binary  not null COMMENT '成交类型'
	,PriceSource   char(1) binary  not null COMMENT '成交价来源'
	,UserID   varchar(15) binary   COMMENT '交易用户代码'
	,OrderLocalID   varchar(12) binary   COMMENT '本地报单编号'
	,ClearingPartID   varchar(10) binary  not null COMMENT '结算会员编号'
	,BusinessUnit   varchar(20) binary   COMMENT '业务单元'
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,SettlementID,TradeID,Direction)
) COMMENT='成交';



-- ******************************
-- 创建报单表
-- ******************************
create table dbclear.t_Order
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,OrderSysID   varchar(12) binary  not null COMMENT '报单编号'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	,UserID   varchar(15) binary  not null COMMENT '交易用户代码'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,OrderPriceType   char(1) binary  not null COMMENT '报单价格条件'
	,Direction   char(1) binary  not null COMMENT '买卖方向'
	,CombOffsetFlag   varchar(4) binary  not null COMMENT '组合开平标志'
	,CombHedgeFlag   varchar(4) binary  not null COMMENT '组合投机套保标志'
	,LimitPrice 	   decimal(16,6)    COMMENT '价格'
	,VolumeTotalOriginal    bigInt(10)    not null COMMENT '数量'
	,TimeCondition   char(1) binary  not null COMMENT '有效期类型'
	,GTDDate   varchar(8) binary   COMMENT 'GTD日期'
	,VolumeCondition   char(1) binary  not null COMMENT '成交量类型'
	,MinVolume    bigInt(10)     COMMENT '最小成交量'
	,ContingentCondition   char(1) binary  not null COMMENT '触发条件'
	,StopPrice 	   decimal(16,6)    COMMENT '止损价'
	,ForceCloseReason   char(1) binary   COMMENT '强平原因'
	,OrderLocalID   varchar(12) binary   COMMENT '本地报单编号'
	,IsAutoSuspend   INTEGER   not null COMMENT '自动挂起标志'
	,OrderSource   char(1) binary  not null COMMENT '报单来源'
	,OrderStatus   char(1) binary  not null COMMENT '报单状态'
	,OrderType   char(1) binary  not null COMMENT '报单类型'
	,VolumeTraded    bigInt(10)    not null COMMENT '今成交数量'
	,VolumeTotal    bigInt(10)    not null COMMENT '剩余数量'
	,InsertDate   varchar(8) binary  not null COMMENT '报单日期'
	,InsertTime   varchar(8) binary  not null COMMENT '插入时间'
	,ActiveTime   varchar(8) binary   COMMENT '激活时间'
	,SuspendTime   varchar(8) binary   COMMENT '挂起时间'
	,UpdateTime   varchar(8) binary   COMMENT '最后修改时间'
	,CancelTime   varchar(8) binary   COMMENT '撤销时间'
	,ActiveUserID   varchar(15) binary   COMMENT '最后修改交易用户代码'
	,Priority    bigInt(10)    not null COMMENT '优先权'
	,TimeSortID    bigInt(10)    not null COMMENT '按时间排队的序号'
	,ClearingPartID   varchar(10) binary  not null COMMENT '结算会员编号'
	,BusinessUnit   varchar(20) binary   COMMENT '业务单元'
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,SettlementID,OrderSysID)
) COMMENT='报单';



-- ******************************
-- 创建客户合约交割持仓表
-- ******************************
create table dbclear.t_ClientDelivPosition
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,HedgeFlag   char(1) binary  not null COMMENT '投机套保标志'
	,PosiDirection   char(1) binary  not null COMMENT '持仓多空方向'
	,YdPosition    bigInt(10)    not null COMMENT '上日持仓'
	,Position    bigInt(10)    not null COMMENT '今日持仓'
	,LongFrozen    bigInt(10)    not null COMMENT '多头冻结'
	,ShortFrozen    bigInt(10)    not null COMMENT '空头冻结'
	,YdLongFrozen    bigInt(10)    not null COMMENT '昨日多头冻结'
	,YdShortFrozen    bigInt(10)    not null COMMENT '昨日空头冻结'
	,BuyTradeVolume    bigInt(10)    not null COMMENT '当日买成交量'
	,SellTradeVolume    bigInt(10)    not null COMMENT '当日卖成交量'
	,PositionCost 	   decimal(19,3)   not null COMMENT '持仓成本'
	,YdPositionCost 	   decimal(19,3)   not null COMMENT '昨日持仓成本'
	,UseMargin 	   decimal(19,3)   not null COMMENT '占用的保证金'
	,FrozenMargin 	   decimal(19,3)   not null COMMENT '冻结的保证金'
	,LongFrozenMargin 	   decimal(19,3)   not null COMMENT '多头冻结的保证金'
	,ShortFrozenMargin 	   decimal(19,3)   not null COMMENT '空头冻结的保证金'
	,FrozenPremium 	   decimal(19,3)   not null COMMENT '冻结的权利金'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,InstrumentID,ParticipantID,ClientID)
) COMMENT='客户合约交割持仓';



-- ******************************
-- 创建客户交割手续费表
-- ******************************
create table dbclear.t_ClientDelivFee
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	,AccountID   varchar(12) binary  not null COMMENT '资金帐号'
	,ProductGroupID   varchar(8) binary  not null COMMENT '产品组代码'
	,ProductID   varchar(8) binary  not null COMMENT '产品代码'
	,UnderlyingInstrID   varchar(30) binary   COMMENT '基础商品代码'
	,Position    bigInt(10)    not null COMMENT '交割持仓量'
	,ValueMode   char(1) binary  not null COMMENT '取值方式'
	,DelivFeeRatio 	   decimal(22,6)   not null COMMENT '交割手续费率'
	,MinFee 	   decimal(19,3)   not null COMMENT '最低费用'
	,MaxFee 	   decimal(19,3)   not null COMMENT '最高费用'
	,Price 	   decimal(16,6)   not null COMMENT '交割价格'
	,DelivFee 	   decimal(19,3)   not null COMMENT '交割手续费'
	,Tax 	   decimal(19,3)    default '0' not null COMMENT '税费等'
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,SettlementID,InstrumentID,ParticipantID,ClientID,AccountID,ProductGroupID,ProductID)
) COMMENT='客户交割手续费';



-- ******************************
-- 创建交割合约表
-- ******************************
create table dbclear.t_DelivInstrument
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,SettlementID,InstrumentID)
) COMMENT='交割合约';



-- ******************************
-- 创建客户合约持仓保证金表
-- ******************************
create table dbclear.t_ClientPositionMargin
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	,AccountID   varchar(12) binary  not null COMMENT '资金帐号'
	,ProductGroupID   varchar(8) binary  not null COMMENT '产品组代码'
	,ProductID   varchar(8) binary  not null COMMENT '产品代码'
	,UnderlyingInstrID   varchar(30) binary   COMMENT '基础商品代码'
	,TradingRole   char(1) binary  not null COMMENT '交易角色'
	,HedgeFlag   char(1) binary  not null COMMENT '投机套保标志'
	,ValueMode   char(1) binary  not null COMMENT '取值方式'
	,MarginRatio 	   decimal(22,6)   not null COMMENT '保证金率'
	,PosiDirection   char(1) binary  not null COMMENT '持仓多空方向'
	,Position    bigInt(10)    not null COMMENT '今日持仓'
	,SettlementPrice 	   decimal(16,6)    COMMENT '今结算'
	,PositionMargin 	   decimal(19,3)   not null COMMENT '占用的保证金'
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,SettlementID,InstrumentID,ParticipantID,ClientID,AccountID,ProductGroupID,ProductID,TradingRole,HedgeFlag,PosiDirection)
) COMMENT='客户合约持仓保证金';



-- ******************************
-- 创建客户合约成交盈亏表
-- ******************************
create table dbclear.t_ClientTradeProfit
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	,AccountID   varchar(12) binary  not null COMMENT '资金帐号'
	,TradeID   varchar(12) binary  not null COMMENT '成交编号'
	,Direction   char(1) binary  not null COMMENT '买卖方向'
	,OffsetFlag   char(1) binary  not null COMMENT '开平标志'
	,Price 	   decimal(16,6)   not null COMMENT '价格'
	,Volume    bigInt(10)    not null COMMENT '数量'
	,Profit 	   decimal(19,3)   not null COMMENT '盈亏'
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,SettlementID,InstrumentID,ParticipantID,ClientID,AccountID,TradeID,Direction,OffsetFlag)
) COMMENT='客户合约成交盈亏';



-- ******************************
-- 创建客户合约持仓盈亏表
-- ******************************
create table dbclear.t_ClientPositionProfit
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	,HedgeFlag   char(1) binary  not null COMMENT '投机套保标志'
	,PosiDirection   char(1) binary  not null COMMENT '持仓多空方向'
	,PositionCost 	   decimal(19,3)   not null COMMENT '持仓成本'
	,SettlementPositionCost 	   decimal(19,3)   not null COMMENT '今结算持仓成本'
	,PositionProfit 	   decimal(19,3)   not null COMMENT '持仓盈亏'
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,SettlementID,InstrumentID,ParticipantID,ClientID,HedgeFlag,PosiDirection)
) COMMENT='客户合约持仓盈亏';



-- ******************************
-- 创建客户合约交易手续费率表
-- ******************************
create table dbclear.t_ClientTransFeeRatio
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	,TradingRole   char(1) binary  not null COMMENT '交易角色'
	,HedgeFlag   char(1) binary  not null COMMENT '投机套保标志'
	,ValueMode   char(1) binary  not null COMMENT '取值方式'
	,OpenFeeRatio 	   decimal(22,6)   not null COMMENT '开仓手续费率'
	,CloseYesterdayFeeRatio 	   decimal(22,6)   not null COMMENT '平昨手续费率'
	,CloseTodayFeeRatio 	   decimal(22,6)   not null COMMENT '平今手续费率'
	,MinOpenFee 	   decimal(19,3)    default '0' not null COMMENT '最低开仓费用'
	,MinCloseFee 	   decimal(19,3)    default '0' not null COMMENT '最低平仓费用'
	,MaxOpenFee 	   decimal(19,3)    default '0' not null COMMENT '最高开仓费用'
	,MaxCloseFee 	   decimal(19,3)    default '0' not null COMMENT '最高平仓费用'
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,SettlementID,InstrumentID,ParticipantID,ClientID,TradingRole,HedgeFlag)
) COMMENT='客户合约交易手续费率';



-- ******************************
-- 创建客户合约交易手续费表
-- ******************************
create table dbclear.t_ClientTransFee
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	,AccountID   varchar(12) binary  not null COMMENT '资金帐号'
	,ProductGroupID   varchar(8) binary  not null COMMENT '产品组代码'
	,ProductID   varchar(8) binary  not null COMMENT '产品代码'
	,UnderlyingInstrID   varchar(30) binary   COMMENT '基础商品代码'
	,TradeID   varchar(12) binary  not null COMMENT '成交编号'
	,OrderSysID   varchar(12) binary  not null COMMENT '报单编号'
	,Direction   char(1) binary  not null COMMENT '买卖方向'
	,TradingRole   char(1) binary  not null COMMENT '交易角色'
	,HedgeFlag   char(1) binary  not null COMMENT '投机套保标志'
	,OffsetFlag   char(1) binary  not null COMMENT '开平标志'
	,ValueMode   char(1) binary  not null COMMENT '取值方式'
	,TransFeeRatio 	   decimal(22,6)   not null COMMENT '交易手续费率'
	,MinFee 	   decimal(19,3)   not null COMMENT '最低费用'
	,MaxFee 	   decimal(19,3)   not null COMMENT '最高费用'
	,Price 	   decimal(16,6)   not null COMMENT '价格'
	,Volume    bigInt(10)    not null COMMENT '数量'
	,TransFee 	   decimal(19,3)   not null COMMENT '交易手续费'
	,Tax 	   decimal(19,3)    default '0' not null COMMENT '税费等'
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,SettlementID,InstrumentID,ParticipantID,ClientID,AccountID,ProductGroupID,ProductID,TradeID,OrderSysID,Direction,TradingRole,HedgeFlag,OffsetFlag)
) COMMENT='客户合约交易手续费';



-- ******************************
-- 创建客户资金表
-- ******************************
create table dbclear.t_ClientFund
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	,AccountID   varchar(12) binary  not null COMMENT '资金帐号'
	,Available 	   decimal(19,3)   not null COMMENT '可用资金'
	,TransFee 	   decimal(19,3)   not null COMMENT '交易手续费'
	,DelivFee 	   decimal(19,3)   not null COMMENT '交割手续费'
	,PositionMargin 	   decimal(19,3)   not null COMMENT '持仓保证金'
	,Profit 	   decimal(19,3)   not null COMMENT '盈亏'
	,StockValue 	   decimal(19,3)   not null COMMENT '市值'
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,SettlementID,ParticipantID,ClientID,AccountID)
) COMMENT='客户资金';



