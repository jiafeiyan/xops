-- ******************************
-- 创建交易系统柜台系统对应关系表
-- ******************************
create table sync.t_TradeSystemBrokerSystem
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,BrokerSystemID   varchar(8) binary  not null COMMENT '柜台系统代码'
	  ,PRIMARY KEY (TradeSystemID,BrokerSystemID)
) COMMENT='交易系统柜台系统对应关系';



-- ******************************
-- 创建柜台系统会员对应关系表
-- ******************************
create table sync.t_BrokerSystemParticipant
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	  ,PRIMARY KEY (TradingDay,ParticipantID)
) COMMENT='柜台系统会员对应关系';



-- ******************************
-- 创建交易所表
-- ******************************
create table sync.t_Exchange
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,ExchangeID   varchar(8) binary  not null COMMENT '交易所代码'
	,ExchangeName   varchar(30) binary  not null COMMENT '交易所名称'
	  ,PRIMARY KEY (TradeSystemID,ExchangeID)
) COMMENT='交易所';



-- ******************************
-- 创建结算组表
-- ******************************
create table sync.t_SettlementGroup
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementGroupName   varchar(20) binary  not null COMMENT '结算组名称'
	,ExchangeID   varchar(8) binary  not null COMMENT '交易所代码'
	,SettlementGroupType   char(1) binary  not null COMMENT '结算组类型'
	,Currency   varchar(3) binary  not null COMMENT '币种'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID)
) COMMENT='结算组';



-- ******************************
-- 创建业务参数表表
-- ******************************
create table sync.t_BusinessConfig
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,FunctionCode   varchar(24) binary  not null COMMENT '功能代码'
	,OperationType   varchar(24) binary  not null COMMENT '操作类型'
	,Description   varchar(400) binary   COMMENT '功能描述'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,FunctionCode)
) COMMENT='业务参数表';



-- ******************************
-- 创建资金账户表
-- ******************************
create table sync.t_Account
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,AccountID   varchar(12) binary  not null COMMENT '资金帐号'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,Currency   varchar(3) binary  not null COMMENT '币种'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,AccountID)
) COMMENT='资金账户';



-- ******************************
-- 创建基本准备金账户表
-- ******************************
create table sync.t_BaseReserveAccount
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,AccountID   varchar(12) binary  not null COMMENT '资金帐号'
	,Reserve 	   decimal(19,3)   not null COMMENT '基本准备金'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,AccountID)
) COMMENT='基本准备金账户';



-- ******************************
-- 创建交易资金账户信息表
-- ******************************
create table sync.t_TradingAccount
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,PreBalance 	   decimal(19,3)   not null COMMENT '上次结算准备金'
	,CurrMargin 	   decimal(19,3)   not null COMMENT '当前保证金总额'
	,CloseProfit 	   decimal(19,3)   not null COMMENT '平仓盈亏'
	,Premium 	   decimal(19,3)   not null COMMENT '期权权利金收支'
	,Deposit 	   decimal(19,3)   not null COMMENT '入金金额'
	,Withdraw 	   decimal(19,3)   not null COMMENT '出金金额'
	,Balance 	   decimal(19,3)   not null COMMENT '期货结算准备金'
	,Available 	   decimal(19,3)   not null COMMENT '可提资金'
	,AccountID   varchar(12) binary  not null COMMENT '资金帐号'
	,FrozenMargin 	   decimal(19,3)   not null COMMENT '冻结的保证金'
	,FrozenPremium 	   decimal(19,3)   not null COMMENT '冻结的权利金'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,AccountID)
) COMMENT='交易资金账户信息';



-- ******************************
-- 创建结算交易会员关系表
-- ******************************
create table sync.t_ClearingTradingPart
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,ClearingPartID   varchar(10) binary   COMMENT '结算会员'
	,ParticipantID   varchar(10) binary   COMMENT '交易会员'
	  ,PRIMARY KEY (TradeSystemID,ClearingPartID,ParticipantID)
) COMMENT='结算交易会员关系';



-- ******************************
-- 创建会员表
-- ******************************
create table sync.t_Participant
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ParticipantName   varchar(50) binary  not null COMMENT '会员名称'
	,ParticipantAbbr   varchar(8) binary  not null COMMENT '会员简称'
	,MemberType   char(1) binary  not null COMMENT '会员类型'
	,IsActive   INTEGER   not null COMMENT '是否活跃'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,ParticipantID)
) COMMENT='会员';



-- ******************************
-- 创建客户信息表
-- ******************************
create table sync.t_Client
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	,ClientName   varchar(80) binary  not null COMMENT '客户名称'
	,IdentifiedCardType   varchar(15) binary   COMMENT '证件类型'
	,IdentifiedCardNo   varchar(50) binary   COMMENT '证件号码'
	,TradingRole   char(1) binary  not null COMMENT '交易角色'
	,ClientType   char(1) binary  not null COMMENT '客户类型'
	,IsActive   INTEGER   not null COMMENT '是否活跃'
	,HedgeFlag   char(1) binary  not null COMMENT '客户交易类型'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,ClientID)
) COMMENT='客户信息';



-- ******************************
-- 创建会员客户关系表
-- ******************************
create table sync.t_PartClient
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,ClientID,ParticipantID)
) COMMENT='会员客户关系';



-- ******************************
-- 创建会员产品角色表
-- ******************************
create table sync.t_PartProductRole
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ProductID   varchar(8) binary  not null COMMENT '产品代码'
	,TradingRole   char(1) binary  not null COMMENT '交易角色'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,ParticipantID,ProductID,TradingRole)
) COMMENT='会员产品角色';



-- ******************************
-- 创建会员产品交易权限表
-- ******************************
create table sync.t_PartProductRight
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ProductID   varchar(8) binary  not null COMMENT '产品代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,TradingRight   char(1) binary  not null COMMENT '交易权限'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,ProductID,ParticipantID)
) COMMENT='会员产品交易权限';



-- ******************************
-- 创建会员账户关系表
-- ******************************
create table sync.t_PartRoleAccount
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,TradingRole   char(1) binary  not null COMMENT '交易角色'
	,AccountID   varchar(12) binary  not null COMMENT '资金帐号'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,ParticipantID,TradingRole)
) COMMENT='会员账户关系';



-- ******************************
-- 创建客户产品交易权限表
-- ******************************
create table sync.t_ClientProductRight
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ProductID   varchar(8) binary  not null COMMENT '产品代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	,TradingRight   char(1) binary  not null COMMENT '交易权限'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,ProductID,ClientID)
) COMMENT='客户产品交易权限';



-- ******************************
-- 创建会员合约持仓表
-- ******************************
create table sync.t_PartPosition
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,TradingDay   varchar(8) binary  not null COMMENT '交易日'
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
	  ,PRIMARY KEY (TradeSystemID,TradingDay,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,InstrumentID,ParticipantID,TradingRole)
) COMMENT='会员合约持仓';



-- ******************************
-- 创建客户合约持仓表
-- ******************************
create table sync.t_ClientPosition
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,TradingDay   varchar(8) binary  not null COMMENT '交易日'
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
	  ,PRIMARY KEY (TradeSystemID,TradingDay,SettlementGroupID,SettlementID,HedgeFlag,PosiDirection,InstrumentID,ParticipantID,ClientID)
) COMMENT='客户合约持仓';



-- ******************************
-- 创建交易用户表
-- ******************************
create table sync.t_User
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,UserID   varchar(15) binary  not null COMMENT '交易用户代码'
	,UserType   char(1) binary  not null COMMENT '交易用户类型'
	,Password   varchar(40) binary  not null COMMENT '密码'
	,IsActive   INTEGER   not null COMMENT '交易员权限'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,UserID)
) COMMENT='交易用户';



-- ******************************
-- 创建用户功能权限表
-- ******************************
create table sync.t_UserFunctionRight
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,UserID   varchar(15) binary  not null COMMENT '交易用户代码'
	,FunctionCode   varchar(24) binary  not null COMMENT '功能代码'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,UserID,FunctionCode)
) COMMENT='用户功能权限';



-- ******************************
-- 创建交易员IP地址表
-- ******************************
create table sync.t_UserIP
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,UserID   varchar(15) binary  not null COMMENT '交易用户代码'
	,IPAddress   varchar(15) binary  not null COMMENT 'IP地址'
	,IPMask   varchar(15) binary  not null COMMENT 'IP地址掩码'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,UserID,IPAddress)
) COMMENT='交易员IP地址';



-- ******************************
-- 创建交易合约表
-- ******************************
create table sync.t_Instrument
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ProductID   varchar(8) binary  not null COMMENT '产品代码'
	,ProductGroupID   varchar(8) binary  not null COMMENT '产品组代码'
	,UnderlyingInstrID   varchar(30) binary   COMMENT '基础商品代码'
	,ProductClass   char(1) binary  not null COMMENT '产品类型'
	,PositionType   char(1) binary  not null COMMENT '持仓类型'
	,UnderlyingType   char(1) binary   COMMENT '标的类型'
	,StrikeType   char(1) binary   COMMENT '行权类型'
	,StrikePrice 	   decimal(16,6)    COMMENT '执行价'
	,OptionsType   char(1) binary   COMMENT '期权类型'
	,VolumeMultiple   INTEGER   not null COMMENT '合约数量乘数'
	,UnderlyingMultiple 	   decimal(9,3)   not null COMMENT '合约基础商品乘数'
	,TotalEquity 	   decimal(19,3)    COMMENT '股票总股本数'
	,CirculationEquity 	   decimal(19,3)    COMMENT '股票流通股本数'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ExchInstrumentID   varchar(30) binary   COMMENT '交易所合约代码'
	,InstrumentName   varchar(20) binary  not null COMMENT '合约名称'
	,DeliveryYear   INTEGER   not null COMMENT '交割年份'
	,DeliveryMonth   INTEGER   not null COMMENT '交割月'
	,AdvanceMonth   varchar(3) binary  not null COMMENT '提前月份'
	,IsTrading   INTEGER   not null COMMENT '当前是否交易'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,InstrumentID)
) COMMENT='交易合约';



-- ******************************
-- 创建合约和合约组关系表
-- ******************************
create table sync.t_InstrumentGroup
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,InstrumentGroupID   varchar(30) binary  not null COMMENT '合约组代码'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,InstrumentID)
) COMMENT='合约和合约组关系';



-- ******************************
-- 创建合约属性表
-- ******************************
create table sync.t_CurrInstrumentProperty
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,CreateDate   varchar(8) binary  not null COMMENT '创建日'
	,OpenDate   varchar(8) binary  not null COMMENT '上市日'
	,ExpireDate   varchar(8) binary  not null COMMENT '到期日'
	,StartDelivDate   varchar(8) binary  not null COMMENT '开始交割日'
	,EndDelivDate   varchar(8) binary  not null COMMENT '最后交割日'
	,StrikeDate   varchar(8) binary   COMMENT '期权行权日'
	,BasisPrice 	   decimal(16,6)   not null COMMENT '挂牌基准价'
	,MaxMarketOrderVolume    bigInt(10)    not null COMMENT '市价单最大下单量'
	,MinMarketOrderVolume    bigInt(10)    not null COMMENT '市价单最小下单量'
	,MaxLimitOrderVolume    bigInt(10)    not null COMMENT '限价单最大下单量'
	,MinLimitOrderVolume    bigInt(10)    not null COMMENT '限价单最小下单量'
	,PriceTick 	   decimal(16,6)   not null COMMENT '最小变动价位'
	,AllowDelivPersonOpen   INTEGER   not null COMMENT '交割月自然人开仓'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,InstLifePhase   char(1) binary  not null COMMENT '合约生命周期状态'
	,IsFirstTradingDay   INTEGER   not null COMMENT '是否首交易日'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,InstrumentID)
) COMMENT='合约属性';



-- ******************************
-- 创建当前合约保证金率表
-- ******************************
create table sync.t_CurrMarginRate
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,MarginCalcID   varchar(4) binary  not null COMMENT '保证金算法代码'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,InstrumentID,ParticipantID)
) COMMENT='当前合约保证金率';



-- ******************************
-- 创建当前合约保证金率的详细内容表
-- ******************************
create table sync.t_CurrMarginRateDetail
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,TradingRole   char(1) binary  not null COMMENT '交易角色'
	,HedgeFlag   char(1) binary  not null COMMENT '投机套保标志'
	,ValueMode   char(1) binary  not null COMMENT '取值方式'
	,LongMarginRatio 	   decimal(22,6)   not null COMMENT '多头保证金率'
	,ShortMarginRatio 	   decimal(22,6)   not null COMMENT '空头保证金率'
	,AdjustRatio1 	   decimal(22,6)    COMMENT '保证金率调整参数1'
	,AdjustRatio2 	   decimal(22,6)    COMMENT '保证金率调整参数2'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,TradingRole,HedgeFlag,InstrumentID,ParticipantID,ClientID)
) COMMENT='当前合约保证金率的详细内容';



-- ******************************
-- 创建当前合约价格绑定表
-- ******************************
create table sync.t_CurrPriceBanding
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,PriceLimitType   char(1) binary  not null COMMENT '限价类型'
	,ValueMode   char(1) binary  not null COMMENT '取值方式'
	,RoundingMode   char(1) binary  not null COMMENT '舍入方式'
	,UpperValue 	   decimal(16,6)   not null COMMENT '上限'
	,LowerValue 	   decimal(16,6)   not null COMMENT '下限'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,TradingSegmentSN   INTEGER   not null COMMENT '交易阶段编号'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,InstrumentID,TradingSegmentSN)
) COMMENT='当前合约价格绑定';



-- ******************************
-- 创建当前合约交易阶段属性表
-- ******************************
create table sync.t_CurrTradingSegmentAttr
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,TradingSegmentSN   INTEGER   not null COMMENT '交易阶段编号'
	,TradingSegmentName   varchar(20) binary   COMMENT '交易阶段名称'
	,StartTime   varchar(8) binary  not null COMMENT '起始时间'
	,InstrumentStatus   char(1) binary  not null COMMENT '合约交易状态'
	,DayOffset   INTEGER    default '0' not null COMMENT '日期偏移量'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,TradingSegmentSN,InstrumentID)
) COMMENT='当前合约交易阶段属性';



-- ******************************
-- 创建市场表
-- ******************************
create table sync.t_Market
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,MarketID   varchar(8) binary  not null COMMENT '市场代码'
	,MarketName   varchar(20) binary  not null COMMENT '市场名称'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,MarketID)
) COMMENT='市场';



-- ******************************
-- 创建市场行情表
-- ******************************
create table sync.t_MarketData
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
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
	  ,PRIMARY KEY (TradeSystemID,TradingDay,SettlementGroupID,InstrumentID)
) COMMENT='市场行情';



-- ******************************
-- 创建市场产品关联表
-- ******************************
create table sync.t_MarketProduct
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,MarketID   varchar(8) binary  not null COMMENT '市场代码'
	,ProductID   varchar(8) binary  not null COMMENT '产品代码'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,MarketID,ProductID)
) COMMENT='市场产品关联';



-- ******************************
-- 创建市场产品组关联表
-- ******************************
create table sync.t_MarketProductGroup
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,MarketID   varchar(8) binary  not null COMMENT '市场代码'
	,ProductGroupID   varchar(8) binary  not null COMMENT '产品组代码'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,MarketID,ProductGroupID)
) COMMENT='市场产品组关联';



-- ******************************
-- 创建行情主题表
-- ******************************
create table sync.t_MarketDataTopic
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,TopicID   INTEGER   not null COMMENT '主题代码'
	,TopicName   varchar(60) binary  not null COMMENT '主题名称'
	,MarketID   varchar(8) binary  not null COMMENT '市场代码'
	,SnapShotFeq   INTEGER   not null COMMENT '采样频率'
	,MarketDataDepth   INTEGER   not null COMMENT '市场行情深度'
	,DelaySeconds   INTEGER   not null COMMENT '延迟秒数'
	,MarketDataMode   char(1) binary  not null COMMENT '行情模式'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,TopicID)
) COMMENT='行情主题';



-- ******************************
-- 创建会员订阅市场表
-- ******************************
create table sync.t_PartTopicSubscribe
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '参与者代码'
	,ParticipantType   char(1) binary  not null COMMENT '参与者类型'
	,TopicID   INTEGER   not null COMMENT '主题代码'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,ParticipantID,TopicID)
) COMMENT='会员订阅市场';



-- ******************************
-- 创建行情发布状态表
-- ******************************
create table sync.t_MdPubStatus
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ProductID   varchar(8) binary  not null COMMENT '产品代码'
	,InstrumentStatus   char(1) binary  not null COMMENT '合约交易状态'
	,MdPubStatus   char(1) binary  not null COMMENT '行情发布状态'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID,ProductID,InstrumentStatus)
) COMMENT='行情发布状态';



