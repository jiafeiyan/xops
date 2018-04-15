-- 清空交易系统柜台系统对应关系表
truncate table sync.t_TradeSystemBrokerSystem;

-- 清空柜台系统会员对应关系表
truncate table sync.t_BrokerSystemParticipant;

-- 清空交易所表
truncate table sync.t_Exchange;

-- 清空结算组表
truncate table sync.t_SettlementGroup;

-- 清空业务参数表表
truncate table sync.t_BusinessConfig;

-- 清空资金账户表
truncate table sync.t_Account;

-- 清空基本准备金账户表
truncate table sync.t_BaseReserveAccount;

-- 清空交易资金账户信息表
truncate table sync.t_TradingAccount;

-- 清空结算交易会员关系表
truncate table sync.t_ClearingTradingPart;

-- 清空会员表
truncate table sync.t_Participant;

-- 清空客户信息表
truncate table sync.t_Client;

-- 清空会员客户关系表
truncate table sync.t_PartClient;

-- 清空会员产品角色表
truncate table sync.t_PartProductRole;

-- 清空会员产品交易权限表
truncate table sync.t_PartProductRight;

-- 清空会员账户关系表
truncate table sync.t_PartRoleAccount;

-- 清空客户产品交易权限表
truncate table sync.t_ClientProductRight;

-- 清空会员合约持仓表
truncate table sync.t_PartPosition;

-- 清空客户合约持仓表
truncate table sync.t_ClientPosition;

-- 清空交易用户表
truncate table sync.t_User;

-- 清空用户功能权限表
truncate table sync.t_UserFunctionRight;

-- 清空交易员IP地址表
truncate table sync.t_UserIP;

-- 清空交易合约表
truncate table sync.t_Instrument;

-- 清空合约和合约组关系表
truncate table sync.t_InstrumentGroup;

-- 清空合约属性表
truncate table sync.t_CurrInstrumentProperty;

-- 清空当前合约保证金率表
truncate table sync.t_CurrMarginRate;

-- 清空当前合约保证金率的详细内容表
truncate table sync.t_CurrMarginRateDetail;

-- 清空当前合约价格绑定表
truncate table sync.t_CurrPriceBanding;

-- 清空当前合约交易阶段属性表
truncate table sync.t_CurrTradingSegmentAttr;

-- 清空市场表
truncate table sync.t_Market;

-- 清空市场行情表
truncate table sync.t_MarketData;

-- 清空市场产品关联表
truncate table sync.t_MarketProduct;

-- 清空市场产品组关联表
truncate table sync.t_MarketProductGroup;

-- 清空行情主题表
truncate table sync.t_MarketDataTopic;

-- 清空会员订阅市场表
truncate table sync.t_PartTopicSubscribe;

-- 清空行情发布状态表
truncate table sync.t_MdPubStatus;

-- 清空期货合约持仓明细表
truncate table sync.t_FuturePositionDtl;

