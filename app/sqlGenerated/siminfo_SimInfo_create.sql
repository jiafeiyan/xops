-- ******************************
-- 创建交易系统表
-- ******************************
create table siminfo.t_TradeSystem
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,TradeSystemName   varchar(20) binary  not null COMMENT '交易系统名称'
	  ,PRIMARY KEY (TradeSystemID)
) COMMENT='交易系统';



-- ******************************
-- 创建柜台系统表
-- ******************************
create table siminfo.t_BrokerSystem
(
	BrokerSystemID   varchar(8) binary  not null COMMENT '柜台系统代码'
	,BrokerSystemName   varchar(20) binary  not null COMMENT '柜台系统名称'
	  ,PRIMARY KEY (BrokerSystemID)
) COMMENT='柜台系统';



-- ******************************
-- 创建交易系统柜台系统对应关系表
-- ******************************
create table siminfo.t_TradeSystemBrokerSystem
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,BrokerSystemID   varchar(8) binary  not null COMMENT '柜台系统代码'
	  ,PRIMARY KEY (TradeSystemID,BrokerSystemID)
) COMMENT='交易系统柜台系统对应关系';



-- ******************************
-- 创建柜台系统结算组对应关系表
-- ******************************
create table siminfo.t_BrokerSystemSettlementGroup
(
	BrokerSystemID   varchar(8) binary  not null COMMENT '柜台系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	  ,PRIMARY KEY (BrokerSystemID,SettlementGroupID)
) COMMENT='柜台系统结算组对应关系';



-- ******************************
-- 创建交易所表
-- ******************************
create table siminfo.t_Exchange
(
	ExchangeID   varchar(8) binary  not null COMMENT '交易所代码'
	,ExchangeName   varchar(30) binary  not null COMMENT '交易所名称'
	  ,PRIMARY KEY (ExchangeID)
) COMMENT='交易所';



-- ******************************
-- 创建交易系统交易日表
-- ******************************
create table siminfo.t_TradeSystemTradingDay
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,TradingDay   varchar(8) binary  not null COMMENT '交易日'
	  ,PRIMARY KEY (TradeSystemID)
) COMMENT='交易系统交易日';



-- ******************************
-- 创建结算组表
-- ******************************
create table siminfo.t_SettlementGroup
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementGroupName   varchar(20) binary  not null COMMENT '结算组名称'
	,ExchangeID   varchar(8) binary  not null COMMENT '交易所代码'
	,SettlementGroupType   char(1) binary  not null COMMENT '结算组类型'
	,Currency   varchar(3) binary  not null COMMENT '币种'
	  ,PRIMARY KEY (SettlementGroupID)
) COMMENT='结算组';



-- ******************************
-- 创建交易系统结算组关系表
-- ******************************
create table siminfo.t_TradeSystemSettlementGroup
(
	TradeSystemID   varchar(8) binary  not null COMMENT '交易系统代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	  ,PRIMARY KEY (TradeSystemID,SettlementGroupID)
) COMMENT='交易系统结算组关系';



-- ******************************
-- 创建赛事活动表
-- ******************************
create table siminfo.t_Activity
(
	ActivityID   varchar(8) binary  not null COMMENT '赛事活动代码'
	,ActivityName   varchar(20) binary  not null COMMENT '赛事活动名称'
	,ActivityType   varchar(4) binary  not null COMMENT '赛事活动类型'
	,ActivityStatus   char(1) binary  not null COMMENT '赛事活动状态'
	,InitialBalance 	   decimal(19,3)    default '100000' not null COMMENT '初始资金'
	,CreateDate   varchar(8) binary  not null COMMENT '创建日期'
	,CreateTime   varchar(8) binary  not null COMMENT '创建时间'
	,BeginDate   varchar(8) binary   COMMENT '开始日期'
	,EndDate   varchar(8) binary   COMMENT '结束日期'
	,UpdateDate   varchar(8) binary  not null COMMENT '最后修改日期'
	,UpdateTime   varchar(8) binary  not null COMMENT '最后修改时间'
	  ,PRIMARY KEY (ActivityID)
) COMMENT='赛事活动';



-- ******************************
-- 创建赛事活动结算组关系表
-- ******************************
create table siminfo.t_ActivitySettlementGroup
(
	ActivityID   varchar(8) binary  not null COMMENT '赛事活动代码'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	  ,PRIMARY KEY (ActivityID,SettlementGroupID)
) COMMENT='赛事活动结算组关系';



-- ******************************
-- 创建赛事活动投资者关系表
-- ******************************
create table siminfo.t_ActivityInvestor
(
	ID    bigInt(10)  auto_increment    not null COMMENT '自增ID'
	,ActivityID   varchar(8) binary  not null COMMENT '赛事活动代码'
	,InvestorID   varchar(10) binary  not null COMMENT '投资者代码'
	,JoinDate   varchar(8) binary   COMMENT '参与日期'
	,JoinStatus   char(1) binary   default '0'  COMMENT '参与状态'
	  ,PRIMARY KEY (ID,ActivityID,InvestorID)
) COMMENT='赛事活动投资者关系';



-- ******************************
-- 创建赛事活动可排名投资者表
-- ******************************
create table siminfo.t_ActivityRankableInvestor
(
	ActivityID   varchar(8) binary  not null COMMENT '赛事活动代码'
	,InvestorID   varchar(10) binary   default '0' not null COMMENT '投资者代码'
	,OpenID   varchar(20) binary   COMMENT '投资者开户使用的身份认证代码'
	  ,PRIMARY KEY (ActivityID,InvestorID,OpenID)
) COMMENT='赛事活动可排名投资者';



-- ******************************
-- 创建日历表
-- ******************************
create table siminfo.t_TradingCalendar
(
	Day   varchar(8) binary  not null COMMENT '日期'
	,Wrk   INTEGER   not null COMMENT '工作日'
	,Tra   INTEGER   not null COMMENT '交易日'
	,Sun   INTEGER   not null COMMENT '周日'
	,Mon   INTEGER   not null COMMENT '周一'
	,Tue   INTEGER   not null COMMENT '周二'
	,Wed   INTEGER   not null COMMENT '周三'
	,Thu   INTEGER   not null COMMENT '周四'
	,Fri   INTEGER   not null COMMENT '周五'
	,Sat   INTEGER   not null COMMENT '周六'
	,Bom   INTEGER   not null COMMENT '月初'
	,Eom   INTEGER   not null COMMENT '月末'
	,Spr   INTEGER   not null COMMENT '春节'
	,Hol   INTEGER   not null COMMENT '法定假日'
	  ,PRIMARY KEY (Day)
) COMMENT='日历';



-- ******************************
-- 创建交易资金账户信息表
-- ******************************
create table siminfo.t_TradingAccount
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
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
	  ,PRIMARY KEY (SettlementGroupID,AccountID)
) COMMENT='交易资金账户信息';



-- ******************************
-- 创建会员表
-- ******************************
create table siminfo.t_Participant
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ParticipantName   varchar(50) binary  not null COMMENT '会员名称'
	,ParticipantAbbr   varchar(8) binary  not null COMMENT '会员简称'
	,MemberType   char(1) binary  not null COMMENT '会员类型'
	,IsActive   INTEGER   not null COMMENT '是否活跃'
	  ,PRIMARY KEY (SettlementGroupID,ParticipantID)
) COMMENT='会员';



-- ******************************
-- 创建客户表
-- ******************************
create table siminfo.t_Client
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	,ClientName   varchar(80) binary  not null COMMENT '客户名称'
	,IdentifiedCardType   varchar(15) binary   COMMENT '证件类型'
	,IdentifiedCardNo   varchar(50) binary   COMMENT '证件号码'
	,TradingRole   char(1) binary  not null COMMENT '交易角色'
	,ClientType   char(1) binary  not null COMMENT '客户类型'
	,IsActive   INTEGER   not null COMMENT '是否活跃'
	,HedgeFlag   char(1) binary  not null COMMENT '客户交易类型'
	  ,PRIMARY KEY (SettlementGroupID,ClientID)
) COMMENT='客户';



-- ******************************
-- 创建会员客户关系表
-- ******************************
create table siminfo.t_PartClient
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	  ,PRIMARY KEY (SettlementGroupID,ClientID,ParticipantID)
) COMMENT='会员客户关系';



-- ******************************
-- 创建投资者信息表
-- ******************************
create table siminfo.t_Investor
(
	InvestorID   varchar(10) binary  not null COMMENT '投资者代码'
	,InvestorName   varchar(20) binary   COMMENT '投资者名称'
	,OpenID   varchar(20) binary   COMMENT '投资者开户使用的身份认证代码'
	,Password   varchar(40) binary  not null COMMENT '投资者登录密码'
	,InvestorStatus   char(1) binary  not null COMMENT '投资者状态'
	  ,PRIMARY KEY (InvestorID)
) COMMENT='投资者信息';


-- 创建投资者信息表的认证代码索引
create  index IDX_Investor_OpenIDIndex on siminfo.t_Investor
(
	OpenID asc
);


-- ******************************
-- 创建投资者客户关系表
-- ******************************
create table siminfo.t_InvestorClient
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,InvestorID   varchar(10) binary  not null COMMENT '投资者代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	  ,PRIMARY KEY (SettlementGroupID,InvestorID,ClientID)
) COMMENT='投资者客户关系';


-- 创建投资者客户关系表的投资者客户关系客户代码索引
create  index IDX_InvestorClient_InvestorClientClientIDIndex on siminfo.t_InvestorClient
(
	ClientID asc
);


-- ******************************
-- 创建投资者赛事评估信息表
-- ******************************
create table siminfo.t_ActivityInvestorEvaluation
(
	ActivityID   varchar(8) binary  not null COMMENT '赛事活动代码'
	,InvestorID   varchar(10) binary  not null COMMENT '投资者代码'
	,InitialAsset 	   decimal(19,3)   not null COMMENT '期初资产'
	,PreAsset 	   decimal(19,3)   not null COMMENT '昨资产'
	,CurrentAsset 	   decimal(19,3)   not null COMMENT '当前资产'
	,TotalReturnRate 	   decimal(22,6)   not null COMMENT '总收益率'
	,ReturnRateOf1Day 	   decimal(22,6)   not null COMMENT '日收益率'
	,RankingStatus   char(1) binary   default '0' not null COMMENT '是否参与排名'
	,PreRanking    bigInt(10)     default '0' not null COMMENT '总收益率昨排名'
	,Ranking    bigInt(10)     default '0' not null COMMENT '总收益率排名'
	  ,PRIMARY KEY (ActivityID,InvestorID)
) COMMENT='投资者赛事评估信息';



-- ******************************
-- 创建交易用户表
-- ******************************
create table siminfo.t_User
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,UserID   varchar(15) binary  not null COMMENT '交易用户代码'
	,UserType   char(1) binary  not null COMMENT '交易用户类型'
	,Password   varchar(40) binary  not null COMMENT '密码'
	,IsActive   INTEGER   not null COMMENT '交易员权限'
	  ,PRIMARY KEY (SettlementGroupID,UserID)
) COMMENT='交易用户';



-- ******************************
-- 创建用户功能权限表
-- ******************************
create table siminfo.t_UserFunctionRight
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,UserID   varchar(15) binary  not null COMMENT '交易用户代码'
	,FunctionCode   varchar(24) binary  not null COMMENT '功能代码'
	  ,PRIMARY KEY (SettlementGroupID,UserID,FunctionCode)
) COMMENT='用户功能权限';



-- ******************************
-- 创建交易员IP地址表
-- ******************************
create table siminfo.t_UserIP
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,UserID   varchar(15) binary  not null COMMENT '交易用户代码'
	,IPAddress   varchar(15) binary  not null COMMENT 'IP地址'
	,IPMask   varchar(15) binary  not null COMMENT 'IP地址掩码'
	  ,PRIMARY KEY (SettlementGroupID,UserID,IPAddress)
) COMMENT='交易员IP地址';



-- ******************************
-- 创建结算交易会员关系表
-- ******************************
create table siminfo.t_ClearingTradingPart
(
	ClearingPartID   varchar(10) binary   COMMENT '结算会员'
	,ParticipantID   varchar(10) binary   COMMENT '交易会员'
	  ,PRIMARY KEY (ClearingPartID,ParticipantID)
) COMMENT='结算交易会员关系';



-- ******************************
-- 创建产品组表
-- ******************************
create table siminfo.t_ProductGroup
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ProductGroupID   varchar(8) binary  not null COMMENT '产品组代码'
	,ProductGroupName   varchar(20) binary  not null COMMENT '产品组名称'
	,CommodityID   varchar(8) binary  not null COMMENT '商品代码'
	  ,PRIMARY KEY (SettlementGroupID,ProductGroupID)
) COMMENT='产品组';



-- ******************************
-- 创建产品表
-- ******************************
create table siminfo.t_Product
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ProductID   varchar(16) binary  not null COMMENT '产品代码'
	,ProductGroupID   varchar(8) binary  not null COMMENT '产品组代码'
	,ProductName   varchar(20) binary  not null COMMENT '产品名称'
	,ProductClass   char(1) binary  not null COMMENT '产品类型'
	  ,PRIMARY KEY (SettlementGroupID,ProductID)
) COMMENT='产品';



-- ******************************
-- 创建产品属性表
-- ******************************
create table siminfo.t_ProductProperty
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ProductID   varchar(16) binary  not null COMMENT '产品代码'
	,ProductLifePhase   char(1) binary  not null COMMENT '产品生命周期状态'
	,TradingModel   char(1) binary  not null COMMENT '交易模式'
	,OptionsLimitRatio 	   decimal(22,6)    COMMENT '期权限仓系数'
	,OptionsMgRatio 	   decimal(22,6)    COMMENT '期权保证金调整系数'
	,SettlePriceSeconds   INTEGER   not null COMMENT '结算取样时间'
	  ,PRIMARY KEY (SettlementGroupID,ProductID)
) COMMENT='产品属性';



-- ******************************
-- 创建合约和合约组关系表
-- ******************************
create table siminfo.t_InstrumentGroup
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,InstrumentGroupID   varchar(30) binary  not null COMMENT '合约组代码'
	  ,PRIMARY KEY (SettlementGroupID,InstrumentID)
) COMMENT='合约和合约组关系';



-- ******************************
-- 创建合约表
-- ******************************
create table siminfo.t_Instrument
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ProductID   varchar(16) binary  not null COMMENT '产品代码'
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
	  ,PRIMARY KEY (SettlementGroupID,InstrumentID)
) COMMENT='合约';



-- ******************************
-- 创建合约属性表
-- ******************************
create table siminfo.t_InstrumentProperty
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
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
	  ,PRIMARY KEY (SettlementGroupID,InstrumentID)
) COMMENT='合约属性';



-- ******************************
-- 创建证券权益表
-- ******************************
create table siminfo.t_SecurityProfit
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SecurityID   varchar(30) binary  not null COMMENT '证券代码'
	,SecurityType   varchar(4) binary  not null COMMENT '证券类型'
	,SecurityMarketID   char(1) binary  not null COMMENT '证券市场代码'
	,ProfitType   varchar(4) binary  not null COMMENT '权益类型'
	,DJDate   varchar(8) binary   COMMENT '登记日期'
	,CQDate   varchar(8) binary   COMMENT '除权日期'
	,EndDate   varchar(8) binary   COMMENT '结束日期'
	,DZDate   varchar(8) binary   COMMENT '到账日期'
	,BeforeRate 	   decimal(22,8)   not null COMMENT '税前收益'
	,AfterRate 	   decimal(22,8)   not null COMMENT '税后收益'
	,Price 	   decimal(19,3)   not null COMMENT '价格'
	  ,PRIMARY KEY (SettlementGroupID,SecurityID,SecurityType,SecurityMarketID,ProfitType)
) COMMENT='证券权益';



-- ******************************
-- 创建行情发布状态表
-- ******************************
create table siminfo.t_MdPubStatus
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ProductID   varchar(16) binary  not null COMMENT '产品代码'
	,InstrumentStatus   char(1) binary  not null COMMENT '合约交易状态'
	,MdPubStatus   char(1) binary  not null COMMENT '行情发布状态'
	  ,PRIMARY KEY (SettlementGroupID,ProductID,InstrumentStatus)
) COMMENT='行情发布状态';



-- ******************************
-- 创建市场表
-- ******************************
create table siminfo.t_Market
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,MarketID   varchar(8) binary  not null COMMENT '市场代码'
	,MarketName   varchar(20) binary  not null COMMENT '市场名称'
	  ,PRIMARY KEY (SettlementGroupID,MarketID)
) COMMENT='市场';



-- ******************************
-- 创建市场产品关联表
-- ******************************
create table siminfo.t_MarketProduct
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,MarketID   varchar(8) binary  not null COMMENT '市场代码'
	,ProductID   varchar(16) binary  not null COMMENT '产品代码'
	  ,PRIMARY KEY (SettlementGroupID,MarketID,ProductID)
) COMMENT='市场产品关联';



-- ******************************
-- 创建市场产品组关联表
-- ******************************
create table siminfo.t_MarketProductGroup
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,MarketID   varchar(8) binary  not null COMMENT '市场代码'
	,ProductGroupID   varchar(8) binary  not null COMMENT '产品组代码'
	  ,PRIMARY KEY (SettlementGroupID,MarketID,ProductGroupID)
) COMMENT='市场产品组关联';



-- ******************************
-- 创建行情主题表
-- ******************************
create table siminfo.t_MarketDataTopic
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,TopicID   INTEGER   not null COMMENT '主题代码'
	,TopicName   varchar(60) binary  not null COMMENT '主题名称'
	,MarketID   varchar(8) binary  not null COMMENT '市场代码'
	,SnapShotFeq   INTEGER   not null COMMENT '采样频率'
	,MarketDataDepth   INTEGER   not null COMMENT '市场行情深度'
	,DelaySeconds   INTEGER   not null COMMENT '延迟秒数'
	,MarketDataMode   char(1) binary  not null COMMENT '行情模式'
	  ,PRIMARY KEY (SettlementGroupID,TopicID)
) COMMENT='行情主题';



-- ******************************
-- 创建会员订阅主题表
-- ******************************
create table siminfo.t_PartTopicSubscribe
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '参与者代码'
	,ParticipantType   char(1) binary  not null COMMENT '参与者类型'
	,TopicID   INTEGER   not null COMMENT '主题代码'
	  ,PRIMARY KEY (SettlementGroupID,ParticipantID,TopicID)
) COMMENT='会员订阅主题';



-- ******************************
-- 创建会员账户关系表
-- ******************************
create table siminfo.t_PartRoleAccount
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,TradingRole   char(1) binary  not null COMMENT '交易角色'
	,AccountID   varchar(12) binary  not null COMMENT '资金帐号'
	  ,PRIMARY KEY (SettlementGroupID,ParticipantID,TradingRole)
) COMMENT='会员账户关系';



-- ******************************
-- 创建会员产品角色表
-- ******************************
create table siminfo.t_PartProductRole
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ProductID   varchar(16) binary  not null COMMENT '产品代码'
	,TradingRole   char(1) binary  not null COMMENT '交易角色'
	  ,PRIMARY KEY (SettlementGroupID,ParticipantID,ProductID,TradingRole)
) COMMENT='会员产品角色';



-- ******************************
-- 创建会员产品交易权限表
-- ******************************
create table siminfo.t_PartProductRight
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ProductID   varchar(16) binary  not null COMMENT '产品代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,TradingRight   char(1) binary  not null COMMENT '交易权限'
	  ,PRIMARY KEY (SettlementGroupID,ProductID,ParticipantID)
) COMMENT='会员产品交易权限';



-- ******************************
-- 创建客户产品交易权限表
-- ******************************
create table siminfo.t_ClientProductRight
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ProductID   varchar(16) binary  not null COMMENT '产品代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	,TradingRight   char(1) binary  not null COMMENT '交易权限'
	  ,PRIMARY KEY (SettlementGroupID,ProductID,ClientID)
) COMMENT='客户产品交易权限';



-- ******************************
-- 创建合约交易阶段属性表
-- ******************************
create table siminfo.t_TradingSegmentAttr
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,TradingSegmentSN   INTEGER   not null COMMENT '交易阶段编号'
	,TradingSegmentName   varchar(20) binary   COMMENT '交易阶段名称'
	,StartTime   varchar(8) binary  not null COMMENT '起始时间'
	,InstrumentStatus   char(1) binary  not null COMMENT '合约交易状态'
	,DayOffset   INTEGER    default '0' not null COMMENT '日期偏移量'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	  ,PRIMARY KEY (SettlementGroupID,TradingSegmentSN,InstrumentID)
) COMMENT='合约交易阶段属性';



-- ******************************
-- 创建合约价格绑定表
-- ******************************
create table siminfo.t_PriceBanding
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,PriceLimitType   char(1) binary  not null COMMENT '限价类型'
	,ValueMode   char(1) binary  not null COMMENT '取值方式'
	,RoundingMode   char(1) binary  not null COMMENT '舍入方式'
	,UpperValue 	   decimal(16,6)   not null COMMENT '上限'
	,LowerValue 	   decimal(16,6)   not null COMMENT '下限'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,TradingSegmentSN   INTEGER   not null COMMENT '交易阶段编号'
	  ,PRIMARY KEY (SettlementGroupID,InstrumentID,TradingSegmentSN)
) COMMENT='合约价格绑定';



-- ******************************
-- 创建合约保证金率表
-- ******************************
create table siminfo.t_MarginRate
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,MarginCalcID   varchar(4) binary  not null COMMENT '保证金算法代码'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	  ,PRIMARY KEY (SettlementGroupID,InstrumentID,ParticipantID)
) COMMENT='合约保证金率';



-- ******************************
-- 创建合约保证金率的详细内容表
-- ******************************
create table siminfo.t_MarginRateDetail
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
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
	  ,PRIMARY KEY (SettlementGroupID,TradingRole,HedgeFlag,InstrumentID,ParticipantID,ClientID)
) COMMENT='合约保证金率的详细内容';



-- ******************************
-- 创建合约交易手续费率的详细内容表
-- ******************************
create table siminfo.t_TransFeeRateDetail
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
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
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	  ,PRIMARY KEY (SettlementGroupID,TradingRole,HedgeFlag,InstrumentID,ParticipantID,ClientID)
) COMMENT='合约交易手续费率的详细内容';



-- ******************************
-- 创建合约交割手续费率的详细内容表
-- ******************************
create table siminfo.t_DelivFeeRateDetail
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ValueMode   char(1) binary  not null COMMENT '取值方式'
	,DelivFeeRatio 	   decimal(22,6)   not null COMMENT '交割手续费率'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	  ,PRIMARY KEY (SettlementGroupID,InstrumentID,ParticipantID,ClientID)
) COMMENT='合约交割手续费率的详细内容';



-- ******************************
-- 创建市场行情表
-- ******************************
create table siminfo.t_MarketData
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
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
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,InstrumentID)
) COMMENT='市场行情';



-- ******************************
-- 创建帐户定义表
-- ******************************
create table siminfo.t_Account
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,AccountID   varchar(12) binary  not null COMMENT '资金帐号'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,Currency   varchar(3) binary  not null COMMENT '币种'
	  ,PRIMARY KEY (SettlementGroupID,AccountID)
) COMMENT='帐户定义';



-- ******************************
-- 创建基本准备金账户表
-- ******************************
create table siminfo.t_BaseReserveAccount
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,AccountID   varchar(12) binary  not null COMMENT '资金帐号'
	,Reserve 	   decimal(19,3)   not null COMMENT '基本准备金'
	  ,PRIMARY KEY (SettlementGroupID,AccountID)
) COMMENT='基本准备金账户';



-- ******************************
-- 创建业务配置参数表表
-- ******************************
create table siminfo.t_BusinessConfig
(
	SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,FunctionCode   varchar(24) binary  not null COMMENT '功能代码'
	,OperationType   varchar(24) binary  not null COMMENT '操作类型'
	,Description   varchar(400) binary   COMMENT '功能描述'
	  ,PRIMARY KEY (SettlementGroupID,FunctionCode)
) COMMENT='业务配置参数表';



-- ******************************
-- 创建客户资金表
-- ******************************
create table siminfo.t_ClientFund
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



-- ******************************
-- 创建投资者资金表
-- ******************************
create table siminfo.t_InvestorFund
(
	BrokerSystemID   varchar(8) binary  not null COMMENT '柜台系统代码'
	,InvestorID   varchar(10) binary  not null COMMENT '投资者代码'
	,PreBalance 	   decimal(19,3)   not null COMMENT '上次结算准备金'
	,CurrMargin 	   decimal(19,3)   not null COMMENT '当前保证金总额'
	,CloseProfit 	   decimal(19,3)   not null COMMENT '平仓盈亏'
	,Premium 	   decimal(19,3)   not null COMMENT '期权权利金收支'
	,Deposit 	   decimal(19,3)   not null COMMENT '入金金额'
	,Withdraw 	   decimal(19,3)   not null COMMENT '出金金额'
	,Balance 	   decimal(19,3)   not null COMMENT '期货结算准备金'
	,Available 	   decimal(19,3)   not null COMMENT '可提资金'
	,PreMargin 	   decimal(19,3)   not null COMMENT '上次保证金总额'
	,FuturesMargin 	   decimal(19,3)   not null COMMENT '期货保证金'
	,OptionsMargin 	   decimal(19,3)   not null COMMENT '期权保证金'
	,PositionProfit 	   decimal(19,3)   not null COMMENT '持仓盈亏'
	,Profit 	   decimal(19,3)   not null COMMENT '当日盈亏'
	,Interest 	   decimal(19,3)   not null COMMENT '利息收入'
	,Fee 	   decimal(19,3)   not null COMMENT '手续费'
	,TotalCollateral 	   decimal(19,3)   not null COMMENT '总质押金额'
	,CollateralForMargin 	   decimal(19,3)   not null COMMENT '用质押抵的保证金金额'
	,PreAccmulateInterest 	   decimal(19,3)   not null COMMENT '上次资金利息积数'
	,AccumulateInterest 	   decimal(19,3)   not null COMMENT '资金利息积数'
	,AccumulateFee 	   decimal(19,3)   not null COMMENT '质押手续费积数'
	,ForzenDeposit 	   decimal(19,3)   not null COMMENT '冻结资金'
	,AccountStatus   char(1) binary  not null COMMENT '帐户状态'
	,PreStockValue 	   decimal(19,3)   not null COMMENT '昨股票市值'
	,StockValue 	   decimal(19,3)   not null COMMENT '股票市值'
	  ,PRIMARY KEY (BrokerSystemID,InvestorID)
) COMMENT='投资者资金';



-- ******************************
-- 创建会员资金表
-- ******************************
create table siminfo.t_PartFund
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,AccountID   varchar(12) binary  not null COMMENT '资金帐号'
	,Available 	   decimal(19,3)   not null COMMENT '可用资金'
	,TransFee 	   decimal(19,3)   not null COMMENT '交易手续费'
	,DelivFee 	   decimal(19,3)   not null COMMENT '交割手续费'
	,PositionMargin 	   decimal(19,3)   not null COMMENT '持仓保证金'
	,Profit 	   decimal(19,3)   not null COMMENT '盈亏'
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,SettlementID,InstrumentID,ParticipantID,AccountID)
) COMMENT='会员资金';



-- ******************************
-- 创建客户合约持仓表
-- ******************************
create table siminfo.t_ClientPosition
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
create table siminfo.t_ClientPositionForSecurityProfit
(
	DJDate   varchar(8) binary  not null COMMENT '登记日期'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
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
	  ,PRIMARY KEY (DJDate,SettlementGroupID,HedgeFlag,PosiDirection,InstrumentID,ParticipantID,ClientID)
) COMMENT='客户分红股票持仓';



-- ******************************
-- 创建会员合约持仓表
-- ******************************
create table siminfo.t_PartPosition
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
-- 创建期货合约持仓明细表
-- ******************************
create table siminfo.t_FuturePositionDtl
(
	TradingDay   varchar(8) binary  not null COMMENT '交易日'
	,SettlementGroupID   varchar(8) binary  not null COMMENT '结算组代码'
	,SettlementID   INTEGER   not null COMMENT '结算编号'
	,InstrumentID   varchar(30) binary  not null COMMENT '合约代码'
	,ParticipantID   varchar(10) binary  not null COMMENT '会员代码'
	,ClientID   varchar(10) binary  not null COMMENT '客户代码'
	,HedgeFlag   char(1) binary  not null COMMENT '投机套保标志'
	,Direction   char(1) binary  not null COMMENT '买卖方向'
	,OpenDate   varchar(8) binary  not null COMMENT '开仓日期'
	,TradeID   varchar(12) binary  not null COMMENT '成交编号'
	,Volume    bigInt(10)     COMMENT '开仓手数'
	,OpenPrice 	   decimal(16,6)    COMMENT '开仓价格'
	,TradeType   char(1) binary  not null COMMENT '成交类型'
	,CombInstrumentID   varchar(30) binary   COMMENT '组合合约代码'
	,ExchangeID   varchar(8) binary  not null COMMENT '交易所代码'
	,CloseProfitByDate 	   decimal(19,3)    COMMENT '逐日平仓盈亏'
	,CloseProfitByTrade 	   decimal(19,3)    COMMENT '逐笔平仓盈亏'
	,PositionProfitByDate 	   decimal(19,3)    COMMENT '逐日持仓盈亏'
	,PositionProfitByTrade 	   decimal(19,3)    COMMENT '逐笔持仓盈亏'
	,Margin 	   decimal(19,3)    COMMENT '保证金'
	,ExchMargin 	   decimal(19,3)    COMMENT '交易所保证金'
	,MarginRateByMoney 	   decimal(22,6)   not null COMMENT '保证金率'
	,MarginRateByVolume 	   decimal(22,6)   not null COMMENT '逐笔保证金'
	,LastSettlementPrice 	   decimal(16,6)    COMMENT '昨结算'
	,SettlementPrice 	   decimal(16,6)    COMMENT '结算价'
	,CloseVolume    bigInt(10)     COMMENT '平仓手数'
	,CloseAmount 	   decimal(19,3)    COMMENT '平仓金额'
	  ,PRIMARY KEY (TradingDay,SettlementGroupID,SettlementID,InstrumentID,ParticipantID,ClientID,HedgeFlag,Direction,OpenDate,TradeID,TradeType)
) COMMENT='期货合约持仓明细';



