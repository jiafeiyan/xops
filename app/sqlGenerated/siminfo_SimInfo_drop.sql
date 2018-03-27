-- 删除交易系统表
drop table IF EXISTS siminfo.t_TradeSystem;

-- 删除柜台系统表
drop table IF EXISTS siminfo.t_BrokerSystem;

-- 删除交易系统柜台系统对应关系表
drop table IF EXISTS siminfo.t_TradeSystemBrokerSystem;

-- 删除柜台系统结算组对应关系表
drop table IF EXISTS siminfo.t_BrokerSystemSettlementGroup;

-- 删除交易所表
drop table IF EXISTS siminfo.t_Exchange;

-- 删除交易系统交易日表
drop table IF EXISTS siminfo.t_TradeSystemTradingDay;

-- 删除结算组表
drop table IF EXISTS siminfo.t_SettlementGroup;

-- 删除交易系统结算组关系表
drop table IF EXISTS siminfo.t_TradeSystemSettlementGroup;

-- 删除赛事活动表
drop table IF EXISTS siminfo.t_Activity;

-- 删除赛事活动结算组关系表
drop table IF EXISTS siminfo.t_ActivitySettlementGroup;

-- 删除赛事活动投资者关系表
drop table IF EXISTS siminfo.t_ActivityInvestor;

-- 删除赛事活动可排名投资者表
drop table IF EXISTS siminfo.t_ActivityRankableInvestor;

-- 删除日历表
drop table IF EXISTS siminfo.t_TradingCalendar;

-- 删除交易资金账户信息表
drop table IF EXISTS siminfo.t_TradingAccount;

-- 删除会员表
drop table IF EXISTS siminfo.t_Participant;

-- 删除客户表
drop table IF EXISTS siminfo.t_Client;

-- 删除会员客户关系表
drop table IF EXISTS siminfo.t_PartClient;

-- 删除投资者信息表
-- drop index siminfo.IDX_Investor_OpenIDIndex;
drop table IF EXISTS siminfo.t_Investor;

-- 删除投资者客户关系表
-- drop index siminfo.IDX_InvestorClient_InvestorClientClientIDIndex;
drop table IF EXISTS siminfo.t_InvestorClient;

-- 删除投资者赛事评估信息表
drop table IF EXISTS siminfo.t_ActivityInvestorEvaluation;

-- 删除交易用户表
drop table IF EXISTS siminfo.t_User;

-- 删除用户功能权限表
drop table IF EXISTS siminfo.t_UserFunctionRight;

-- 删除交易员IP地址表
drop table IF EXISTS siminfo.t_UserIP;

-- 删除结算交易会员关系表
drop table IF EXISTS siminfo.t_ClearingTradingPart;

-- 删除产品组表
drop table IF EXISTS siminfo.t_ProductGroup;

-- 删除产品表
drop table IF EXISTS siminfo.t_Product;

-- 删除产品属性表
drop table IF EXISTS siminfo.t_ProductProperty;

-- 删除合约和合约组关系表
drop table IF EXISTS siminfo.t_InstrumentGroup;

-- 删除合约表
drop table IF EXISTS siminfo.t_Instrument;

-- 删除合约属性表
drop table IF EXISTS siminfo.t_InstrumentProperty;

-- 删除证券权益表
drop table IF EXISTS siminfo.t_SecurityProfit;

-- 删除行情发布状态表
drop table IF EXISTS siminfo.t_MdPubStatus;

-- 删除市场表
drop table IF EXISTS siminfo.t_Market;

-- 删除市场产品关联表
drop table IF EXISTS siminfo.t_MarketProduct;

-- 删除市场产品组关联表
drop table IF EXISTS siminfo.t_MarketProductGroup;

-- 删除行情主题表
drop table IF EXISTS siminfo.t_MarketDataTopic;

-- 删除会员订阅主题表
drop table IF EXISTS siminfo.t_PartTopicSubscribe;

-- 删除会员账户关系表
drop table IF EXISTS siminfo.t_PartRoleAccount;

-- 删除会员产品角色表
drop table IF EXISTS siminfo.t_PartProductRole;

-- 删除会员产品交易权限表
drop table IF EXISTS siminfo.t_PartProductRight;

-- 删除客户产品交易权限表
drop table IF EXISTS siminfo.t_ClientProductRight;

-- 删除合约交易阶段属性表
drop table IF EXISTS siminfo.t_TradingSegmentAttr;

-- 删除合约价格绑定表
drop table IF EXISTS siminfo.t_PriceBanding;

-- 删除合约保证金率表
drop table IF EXISTS siminfo.t_MarginRate;

-- 删除合约保证金率的详细内容表
drop table IF EXISTS siminfo.t_MarginRateDetail;

-- 删除合约交易手续费率的详细内容表
drop table IF EXISTS siminfo.t_TransFeeRateDetail;

-- 删除合约交割手续费率的详细内容表
drop table IF EXISTS siminfo.t_DelivFeeRateDetail;

-- 删除市场行情表
drop table IF EXISTS siminfo.t_MarketData;

-- 删除帐户定义表
drop table IF EXISTS siminfo.t_Account;

-- 删除基本准备金账户表
drop table IF EXISTS siminfo.t_BaseReserveAccount;

-- 删除业务配置参数表表
drop table IF EXISTS siminfo.t_BusinessConfig;

-- 删除客户资金表
drop table IF EXISTS siminfo.t_ClientFund;

-- 删除投资者资金表
drop table IF EXISTS siminfo.t_InvestorFund;

-- 删除会员资金表
drop table IF EXISTS siminfo.t_PartFund;

-- 删除客户合约持仓表
drop table IF EXISTS siminfo.t_ClientPosition;

-- 删除客户分红股票持仓表
drop table IF EXISTS siminfo.t_ClientPositionForSecurityProfit;

-- 删除会员合约持仓表
drop table IF EXISTS siminfo.t_PartPosition;

