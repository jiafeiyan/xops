-- 删除交易系统表
drop table IF EXISTS snap.t_S_TradeSystem;

-- 删除柜台系统表
drop table IF EXISTS snap.t_S_BrokerSystem;

-- 删除交易系统柜台系统对应关系表
drop table IF EXISTS snap.t_S_TradeSystemBrokerSystem;

-- 删除柜台系统结算组对应关系表
drop table IF EXISTS snap.t_S_BrokerSystemSettlementGroup;

-- 删除交易所表
drop table IF EXISTS snap.t_S_Exchange;

-- 删除结算组表
drop table IF EXISTS snap.t_S_SettlementGroup;

-- 删除交易系统结算组关系表
drop table IF EXISTS snap.t_S_TradeSystemSettlementGroup;

-- 删除赛事活动表
drop table IF EXISTS snap.t_S_Activity;

-- 删除赛事活动结算组关系表
drop table IF EXISTS snap.t_S_ActivitySettlementGroup;

-- 删除赛事活动投资者关系表
drop table IF EXISTS snap.t_S_ActivityInvestor;

-- 删除交易资金账户信息表
drop table IF EXISTS snap.t_S_TradingAccount;

-- 删除会员表
drop table IF EXISTS snap.t_S_Participant;

-- 删除客户表
drop table IF EXISTS snap.t_S_Client;

-- 删除会员客户关系表
drop table IF EXISTS snap.t_S_PartClient;

-- 删除投资者信息表
drop table IF EXISTS snap.t_S_Investor;

-- 删除投资者客户关系表
drop table IF EXISTS snap.t_S_InvestorClient;

-- 删除投资者赛事评估信息表
drop table IF EXISTS snap.t_S_ActivityInvestorEvaluation;

-- 删除交易用户表
drop table IF EXISTS snap.t_S_User;

-- 删除用户功能权限表
drop table IF EXISTS snap.t_S_UserFunctionRight;

-- 删除交易员IP地址表
drop table IF EXISTS snap.t_S_UserIP;

-- 删除结算交易会员关系表
drop table IF EXISTS snap.t_S_ClearingTradingPart;

-- 删除产品组表
drop table IF EXISTS snap.t_S_ProductGroup;

-- 删除产品表
drop table IF EXISTS snap.t_S_Product;

-- 删除产品属性表
drop table IF EXISTS snap.t_S_ProductProperty;

-- 删除合约和合约组关系表
drop table IF EXISTS snap.t_S_InstrumentGroup;

-- 删除合约表
drop table IF EXISTS snap.t_S_Instrument;

-- 删除合约属性表
drop table IF EXISTS snap.t_S_InstrumentProperty;

-- 删除证券权益表
drop table IF EXISTS snap.t_S_SecurityProfit;

-- 删除市场表
drop table IF EXISTS snap.t_S_Market;

-- 删除市场产品关联表
drop table IF EXISTS snap.t_S_MarketProduct;

-- 删除市场产品组关联表
drop table IF EXISTS snap.t_S_MarketProductGroup;

-- 删除行情主题表
drop table IF EXISTS snap.t_S_MarketDataTopic;

-- 删除会员订阅主题表
drop table IF EXISTS snap.t_S_PartTopicSubscribe;

-- 删除会员账户关系表
drop table IF EXISTS snap.t_S_PartRoleAccount;

-- 删除会员产品角色表
drop table IF EXISTS snap.t_S_PartProductRole;

-- 删除会员产品交易权限表
drop table IF EXISTS snap.t_S_PartProductRight;

-- 删除客户产品交易权限表
drop table IF EXISTS snap.t_S_ClientProductRight;

-- 删除合约交易阶段属性表
drop table IF EXISTS snap.t_S_TradingSegmentAttr;

-- 删除合约价格绑定表
drop table IF EXISTS snap.t_S_PriceBanding;

-- 删除合约保证金率表
drop table IF EXISTS snap.t_S_MarginRate;

-- 删除合约保证金率的详细内容表
drop table IF EXISTS snap.t_S_MarginRateDetail;

-- 删除合约交易手续费率的详细内容表
drop table IF EXISTS snap.t_S_TransFeeRateDetail;

-- 删除合约交割手续费率的详细内容表
drop table IF EXISTS snap.t_S_DelivFeeRateDetail;

-- 删除市场行情表
drop table IF EXISTS snap.t_S_MarketData;

-- 删除报单表
drop table IF EXISTS snap.t_S_Order;

-- 删除成交表
drop table IF EXISTS snap.t_S_Trade;

-- 删除帐户定义表
drop table IF EXISTS snap.t_S_Account;

-- 删除基本准备金账户表
drop table IF EXISTS snap.t_S_BaseReserveAccount;

-- 删除业务配置参数表表
drop table IF EXISTS snap.t_S_BusinessConfig;

-- 删除客户资金表
drop table IF EXISTS snap.t_S_ClientFund;

-- 删除投资者资金表
drop table IF EXISTS snap.t_S_InvestorFund;

-- 删除会员资金表
drop table IF EXISTS snap.t_S_PartFund;

