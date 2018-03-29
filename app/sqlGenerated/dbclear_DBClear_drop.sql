-- 删除结算会话表
drop table IF EXISTS dbclear.t_Settlement;

-- 删除会员合约持仓表
drop table IF EXISTS dbclear.t_PartPosition;

-- 删除客户合约持仓表
drop table IF EXISTS dbclear.t_ClientPosition;

-- 删除客户分红股票持仓表
drop table IF EXISTS dbclear.t_ClientPositionForSecurityProfit;

-- 删除市场行情表
drop table IF EXISTS dbclear.t_MarketData;

-- 删除成交表
drop table IF EXISTS dbclear.t_Trade;

-- 删除报单表
drop table IF EXISTS dbclear.t_Order;

-- 删除客户合约交割持仓表
drop table IF EXISTS dbclear.t_ClientDelivPosition;

-- 删除客户交割手续费表
drop table IF EXISTS dbclear.t_ClientDelivFee;

-- 删除交割合约表
drop table IF EXISTS dbclear.t_DelivInstrument;

-- 删除客户合约持仓保证金表
drop table IF EXISTS dbclear.t_ClientPositionMargin;

-- 删除客户合约成交盈亏表
drop table IF EXISTS dbclear.t_ClientTradeProfit;

-- 删除客户合约持仓盈亏表
drop table IF EXISTS dbclear.t_ClientPositionProfit;

-- 删除客户合约交易手续费率表
drop table IF EXISTS dbclear.t_ClientTransFeeRatio;

-- 删除客户合约交易手续费表
drop table IF EXISTS dbclear.t_ClientTransFee;

-- 删除客户资金表
drop table IF EXISTS dbclear.t_ClientFund;

-- 删除客户持仓权利金表
drop table IF EXISTS dbclear.t_ClientPositionPremium;

