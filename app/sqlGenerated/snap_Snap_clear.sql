-- 清空交易系统表
truncate table snap.t_S_TradeSystem;

-- 清空柜台系统表
truncate table snap.t_S_BrokerSystem;

-- 清空交易系统柜台系统对应关系表
truncate table snap.t_S_TradeSystemBrokerSystem;

-- 清空柜台系统结算组对应关系表
truncate table snap.t_S_BrokerSystemSettlementGroup;

-- 清空交易所表
truncate table snap.t_S_Exchange;

-- 清空结算组表
truncate table snap.t_S_SettlementGroup;

-- 清空交易系统结算组关系表
truncate table snap.t_S_TradeSystemSettlementGroup;

-- 清空赛事活动表
truncate table snap.t_S_Activity;

-- 清空赛事活动结算组关系表
truncate table snap.t_S_ActivitySettlementGroup;

-- 清空赛事活动投资者关系表
truncate table snap.t_S_ActivityInvestor;

-- 清空交易资金账户信息表
truncate table snap.t_S_TradingAccount;

-- 清空会员表
truncate table snap.t_S_Participant;

-- 清空客户表
truncate table snap.t_S_Client;

-- 清空客户合约持仓表
truncate table snap.t_S_ClientPosition;

-- 清空会员客户关系表
truncate table snap.t_S_PartClient;

-- 清空投资者信息表
truncate table snap.t_S_Investor;

-- 清空投资者客户关系表
truncate table snap.t_S_InvestorClient;

-- 清空投资者赛事评估信息表
truncate table snap.t_S_ActivityInvestorEvaluation;

-- 清空交易用户表
truncate table snap.t_S_User;

-- 清空用户功能权限表
truncate table snap.t_S_UserFunctionRight;

-- 清空交易员IP地址表
truncate table snap.t_S_UserIP;

-- 清空结算交易会员关系表
truncate table snap.t_S_ClearingTradingPart;

-- 清空产品组表
truncate table snap.t_S_ProductGroup;

-- 清空产品表
truncate table snap.t_S_Product;

-- 清空产品属性表
truncate table snap.t_S_ProductProperty;

-- 清空合约和合约组关系表
truncate table snap.t_S_InstrumentGroup;

-- 清空合约表
truncate table snap.t_S_Instrument;

-- 清空合约属性表
truncate table snap.t_S_InstrumentProperty;

-- 清空证券权益表
truncate table snap.t_S_SecurityProfit;

-- 清空市场表
truncate table snap.t_S_Market;

-- 清空市场产品关联表
truncate table snap.t_S_MarketProduct;

-- 清空市场产品组关联表
truncate table snap.t_S_MarketProductGroup;

-- 清空行情主题表
truncate table snap.t_S_MarketDataTopic;

-- 清空会员订阅主题表
truncate table snap.t_S_PartTopicSubscribe;

-- 清空会员账户关系表
truncate table snap.t_S_PartRoleAccount;

-- 清空会员产品角色表
truncate table snap.t_S_PartProductRole;

-- 清空会员产品交易权限表
truncate table snap.t_S_PartProductRight;

-- 清空客户产品交易权限表
truncate table snap.t_S_ClientProductRight;

-- 清空合约交易阶段属性表
truncate table snap.t_S_TradingSegmentAttr;

-- 清空合约价格绑定表
truncate table snap.t_S_PriceBanding;

-- 清空合约保证金率表
truncate table snap.t_S_MarginRate;

-- 清空合约保证金率的详细内容表
truncate table snap.t_S_MarginRateDetail;

-- 清空合约交易手续费率的详细内容表
truncate table snap.t_S_TransFeeRateDetail;

-- 清空合约交割手续费率的详细内容表
truncate table snap.t_S_DelivFeeRateDetail;

-- 清空市场行情表
truncate table snap.t_S_MarketData;

-- 清空报单表
truncate table snap.t_S_Order;

-- 清空成交表
truncate table snap.t_S_Trade;

-- 清空帐户定义表
truncate table snap.t_S_Account;

-- 清空基本准备金账户表
truncate table snap.t_S_BaseReserveAccount;

-- 清空业务配置参数表表
truncate table snap.t_S_BusinessConfig;

-- 清空客户资金表
truncate table snap.t_S_ClientFund;

-- 清空投资者资金表
truncate table snap.t_S_InvestorFund;

-- 清空会员资金表
truncate table snap.t_S_PartFund;

-- 清空期货合约持仓明细表
truncate table snap.t_S_FuturePositionDtl;

-- 清空未知探索活动表
truncate table snap.t_S_DiscoveryActivity;

-- 清空未知探索活动结算组关系表
truncate table snap.t_S_DiscoveryActSettleGroup;

-- 清空未知探索活动投资者关系表
truncate table snap.t_S_DiscoveryActivityInvestor;

-- 清空投资者未知探索评估信息表
truncate table snap.t_S_DiscoveryActInvestorEval;

