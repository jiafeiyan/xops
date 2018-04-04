-- 删除交易系统柜台系统对应关系表
drop table IF EXISTS sync.t_TradeSystemBrokerSystem;

-- 删除柜台系统会员对应关系表
drop table IF EXISTS sync.t_BrokerSystemParticipant;

-- 删除交易所表
drop table IF EXISTS sync.t_Exchange;

-- 删除结算组表
drop table IF EXISTS sync.t_SettlementGroup;

-- 删除业务参数表表
drop table IF EXISTS sync.t_BusinessConfig;

-- 删除资金账户表
drop table IF EXISTS sync.t_Account;

-- 删除基本准备金账户表
drop table IF EXISTS sync.t_BaseReserveAccount;

-- 删除交易资金账户信息表
drop table IF EXISTS sync.t_TradingAccount;

-- 删除结算交易会员关系表
drop table IF EXISTS sync.t_ClearingTradingPart;

-- 删除会员表
drop table IF EXISTS sync.t_Participant;

-- 删除客户信息表
drop table IF EXISTS sync.t_Client;

-- 删除会员客户关系表
drop table IF EXISTS sync.t_PartClient;

-- 删除会员产品角色表
drop table IF EXISTS sync.t_PartProductRole;

-- 删除会员产品交易权限表
drop table IF EXISTS sync.t_PartProductRight;

-- 删除会员账户关系表
drop table IF EXISTS sync.t_PartRoleAccount;

-- 删除客户产品交易权限表
drop table IF EXISTS sync.t_ClientProductRight;

-- 删除会员合约持仓表
drop table IF EXISTS sync.t_PartPosition;

-- 删除客户合约持仓表
drop table IF EXISTS sync.t_ClientPosition;

-- 删除交易用户表
drop table IF EXISTS sync.t_User;

-- 删除用户功能权限表
drop table IF EXISTS sync.t_UserFunctionRight;

-- 删除交易员IP地址表
drop table IF EXISTS sync.t_UserIP;

-- 删除交易合约表
drop table IF EXISTS sync.t_Instrument;

-- 删除合约和合约组关系表
drop table IF EXISTS sync.t_InstrumentGroup;

-- 删除合约属性表
drop table IF EXISTS sync.t_CurrInstrumentProperty;

-- 删除当前合约保证金率表
drop table IF EXISTS sync.t_CurrMarginRate;

-- 删除当前合约保证金率的详细内容表
drop table IF EXISTS sync.t_CurrMarginRateDetail;

-- 删除当前合约价格绑定表
drop table IF EXISTS sync.t_CurrPriceBanding;

-- 删除当前合约交易阶段属性表
drop table IF EXISTS sync.t_CurrTradingSegmentAttr;

-- 删除市场表
drop table IF EXISTS sync.t_Market;

-- 删除市场行情表
drop table IF EXISTS sync.t_MarketData;

-- 删除市场产品关联表
drop table IF EXISTS sync.t_MarketProduct;

-- 删除市场产品组关联表
drop table IF EXISTS sync.t_MarketProductGroup;

-- 删除行情主题表
drop table IF EXISTS sync.t_MarketDataTopic;

-- 删除会员订阅市场表
drop table IF EXISTS sync.t_PartTopicSubscribe;

-- 删除行情发布状态表
drop table IF EXISTS sync.t_MdPubStatus;

-- 删除期货合约持仓明细表
drop table IF EXISTS sync.t_FuturePositionDtl;

