-- 清空交易系统表
truncate table siminfo.t_TradeSystem;

-- 清空柜台系统表
truncate table siminfo.t_BrokerSystem;

-- 清空交易系统柜台系统对应关系表
truncate table siminfo.t_TradeSystemBrokerSystem;

-- 清空柜台系统结算组对应关系表
truncate table siminfo.t_BrokerSystemSettlementGroup;

-- 清空交易所表
truncate table siminfo.t_Exchange;

-- 清空交易系统交易日表
-- truncate table siminfo.t_TradeSystemTradingDay;

-- 清空结算组表
truncate table siminfo.t_SettlementGroup;

-- 清空交易系统结算组关系表
truncate table siminfo.t_TradeSystemSettlementGroup;

-- 清空赛事活动表
truncate table siminfo.t_Activity;

-- 清空赛事活动结算组关系表
truncate table siminfo.t_ActivitySettlementGroup;

-- 清空赛事活动投资者关系表
truncate table siminfo.t_ActivityInvestor;

-- 清空赛事活动可排名投资者表
truncate table siminfo.t_ActivityRankableInvestor;

-- 清空日历表
-- truncate table siminfo.t_TradingCalendar;

-- 清空交易资金账户信息表
truncate table siminfo.t_TradingAccount;

-- 清空会员表
truncate table siminfo.t_Participant;

-- 清空客户表
truncate table siminfo.t_Client;

-- 清空会员客户关系表
truncate table siminfo.t_PartClient;

-- 清空投资者信息表
truncate table siminfo.t_Investor;

-- 清空投资者客户关系表
truncate table siminfo.t_InvestorClient;

-- 清空投资者赛事评估信息表
truncate table siminfo.t_ActivityInvestorEvaluation;

-- 清空交易用户表
truncate table siminfo.t_User;

-- 清空用户功能权限表
truncate table siminfo.t_UserFunctionRight;

-- 清空交易员IP地址表
truncate table siminfo.t_UserIP;

-- 清空结算交易会员关系表
truncate table siminfo.t_ClearingTradingPart;

-- 清空产品组表
truncate table siminfo.t_ProductGroup;

-- 清空产品表
truncate table siminfo.t_Product;

-- 清空产品属性表
truncate table siminfo.t_ProductProperty;

-- 清空合约和合约组关系表
truncate table siminfo.t_InstrumentGroup;

-- 清空合约表
truncate table siminfo.t_Instrument;

-- 清空合约属性表
truncate table siminfo.t_InstrumentProperty;

-- 清空证券权益表
truncate table siminfo.t_SecurityProfit;

-- 清空行情发布状态表
truncate table siminfo.t_MdPubStatus;

-- 清空市场表
truncate table siminfo.t_Market;

-- 清空市场产品关联表
truncate table siminfo.t_MarketProduct;

-- 清空市场产品组关联表
truncate table siminfo.t_MarketProductGroup;

-- 清空行情主题表
truncate table siminfo.t_MarketDataTopic;

-- 清空会员订阅主题表
truncate table siminfo.t_PartTopicSubscribe;

-- 清空会员账户关系表
truncate table siminfo.t_PartRoleAccount;

-- 清空会员产品角色表
truncate table siminfo.t_PartProductRole;

-- 清空会员产品交易权限表
truncate table siminfo.t_PartProductRight;

-- 清空客户产品交易权限表
truncate table siminfo.t_ClientProductRight;

-- 清空合约交易阶段属性表
truncate table siminfo.t_TradingSegmentAttr;

-- 清空合约价格绑定表
truncate table siminfo.t_PriceBanding;

-- 清空合约保证金率表
truncate table siminfo.t_MarginRate;

-- 清空合约保证金率的详细内容表
truncate table siminfo.t_MarginRateDetail;

-- 清空合约交易手续费率的详细内容表
truncate table siminfo.t_TransFeeRateDetail;

-- 清空合约交割手续费率的详细内容表
truncate table siminfo.t_DelivFeeRateDetail;

-- 清空市场行情表
truncate table siminfo.t_MarketData;

-- 清空帐户定义表
truncate table siminfo.t_Account;

-- 清空基本准备金账户表
truncate table siminfo.t_BaseReserveAccount;

-- 清空业务配置参数表表
truncate table siminfo.t_BusinessConfig;

-- 清空客户资金表
truncate table siminfo.t_ClientFund;

-- 清空投资者资金表
truncate table siminfo.t_InvestorFund;

-- 清空会员资金表
truncate table siminfo.t_PartFund;

-- 清空客户合约持仓表
truncate table siminfo.t_ClientPosition;

-- 清空客户分红股票持仓表
truncate table siminfo.t_ClientPositionForSecurityProfit;

-- 清空会员合约持仓表
truncate table siminfo.t_PartPosition;

-- 清空期货合约持仓明细表
truncate table siminfo.t_FuturePositionDtl;

