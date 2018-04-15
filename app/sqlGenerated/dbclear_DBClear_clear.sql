-- 清空结算会话表
truncate table dbclear.t_Settlement;

-- 清空会员合约持仓表
truncate table dbclear.t_PartPosition;

-- 清空客户合约持仓表
truncate table dbclear.t_ClientPosition;

-- 清空客户分红股票持仓表
truncate table dbclear.t_ClientPositionForSecurityProfit;

-- 清空市场行情表
truncate table dbclear.t_MarketData;

-- 清空成交表
truncate table dbclear.t_Trade;

-- 清空报单表
truncate table dbclear.t_Order;

-- 清空客户合约交割持仓表
truncate table dbclear.t_ClientDelivPosition;

-- 清空客户交割手续费表
truncate table dbclear.t_ClientDelivFee;

-- 清空交割合约表
truncate table dbclear.t_DelivInstrument;

-- 清空客户合约持仓保证金表
truncate table dbclear.t_ClientPositionMargin;

-- 清空客户合约成交盈亏表
truncate table dbclear.t_ClientTradeProfit;

-- 清空客户合约持仓盈亏表
truncate table dbclear.t_ClientPositionProfit;

-- 清空客户合约交易手续费率表
truncate table dbclear.t_ClientTransFeeRatio;

-- 清空客户合约交易手续费表
truncate table dbclear.t_ClientTransFee;

-- 清空客户资金表
truncate table dbclear.t_ClientFund;

-- 清空客户持仓权利金表
truncate table dbclear.t_ClientPositionPremium;

-- 清空期货合约持仓明细表
truncate table dbclear.t_FuturePositionDtl;

