# -*- coding: UTF-8 -*-

import math

CALLPUT_CALL = 0
CALLPUT_PUT = 1

UNDERLYING_COMMODITY = 0
UNDERLYING_FUTURE = 1

OPTIONTYPE_EUROPEAN = 0
OPTIONTYPE_AMERICAN = 1


def norm_density(d):
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * d * d)


def norm_dist(d):
    return (1.0 + math.erf(d / math.sqrt(2.0))) / 2.0


class Option:
    def __init__(self, underlying, option_type, call_put, up, sp, sig, x, y, z):
        self.underlying = underlying
        self.option_type = option_type
        self.call_put = call_put
        self.underlying_price = up #标的资产现价
        self.strike_price = sp #执行价
        self.sigma = sig #波动率
        self.t = x #距离到期时间
        self.r = y #无风险利率
        self.b = z #cost of carry, 若无分红等, 持有成本一般等于无风险利率r, 期货持有成本为0

    def copy_from(self, o):
        self.underlying = o.underlying
        self.option_type = o.option_type
        self.call_put = o.call_put
        self.underlying_price = o.underlying_price
        self.strike_price = o.strike_price
        self.sigma = o.sigma
        self.t = o.t
        self.r = o.r
        self.b = o.b


class BaseBLACKSCHOLES:
    def __init__(self, accuracy=1.0e-6):
        self.ACCURACY = accuracy

    def calc_price(self, op):
        return 0

    def calc_sigma(self, op, d):
        l_sigma = 0.01
        h_sigma = 0.5

        while True:
            op.sigma = l_sigma
            l_bs_p = self.calc_price(op)
            op.sigma = h_sigma
            h_bs_p = self.calc_price(op)

            if h_bs_p - l_bs_p == 0:
                o_sigma = (l_sigma + h_sigma) / 2
                return round(o_sigma, 4)

            o_sigma = l_sigma + ((d - l_bs_p) * (h_sigma - l_sigma)) / (h_bs_p - l_bs_p)

            op.sigma = o_sigma
            bs_p = self.calc_price(op)

            if abs(bs_p - d) < self.ACCURACY:
                return round(o_sigma, 4)

            if o_sigma < l_sigma:
                h_sigma = l_sigma
                l_sigma = o_sigma
            elif o_sigma < h_sigma:
                l_sigma = o_sigma
            else:
                l_sigma = h_sigma
                h_sigma = o_sigma


class DCE_BLACKSCHOLES(BaseBLACKSCHOLES):
    def __init__(self, accuracy=1.0e-6):
        BaseBLACKSCHOLES.__init__(self, accuracy)

    def calc_price(self, op):
        _S = op.underlying_price
        _yt = op.t / 365.00
        _tt = op.t / 365.00
        _sqtt = math.sqrt(_tt)

        if op.underlying == UNDERLYING_COMMODITY:
            _S = op.underlying_price * math.exp(-op.b * op.t)

        d1 = (math.log(_S / op.strike_price) + 0.5 * math.pow(op.sigma, 2) * _tt) / (op.sigma * _sqtt)
        d2 = (math.log(_S / op.strike_price) - 0.5 * math.pow(op.sigma, 2) * _tt) / (op.sigma * _sqtt)

        if op.call_put == CALLPUT_CALL:
            return _S * math.exp(-op.r * _yt) * norm_dist(d1) - op.strike_price * math.exp(-op.r * _tt) * norm_dist(d2)
        else:
            return -_S * math.exp((op.b - op.r) * _tt) * norm_dist(-d1) + op.strike_price * math.exp(-op.r * _yt) * norm_dist(-d2)


class SHFE_BLACKSCHOLES(BaseBLACKSCHOLES):
    def __init__(self, accuracy=1.0e-6):
        BaseBLACKSCHOLES.__init__(self, accuracy)

    def calc_price(self, op):
        _S = op.underlying_price
        _yt = op.t / 360.00
        _tt = op.t / 250.00
        _sqtt = math.sqrt(_tt)

        d1 = (math.log(_S / op.strike_price) + 0.5 * math.pow(op.sigma, 2) * _tt) / (op.sigma * _sqtt)
        d2 = (math.log(_S / op.strike_price) - 0.5 * math.pow(op.sigma, 2) * _tt) / (op.sigma * _sqtt)

        if op.call_put == CALLPUT_CALL:
            return _S * math.exp(-op.r * _yt) * norm_dist(d1) - op.strike_price * math.exp(-op.r * _tt) * norm_dist(d2)
        else:
            return -_S * math.exp((op.b - op.r) * _tt) * norm_dist(-d1) + op.strike_price * math.exp(-op.r * _yt) * norm_dist(-d2)
