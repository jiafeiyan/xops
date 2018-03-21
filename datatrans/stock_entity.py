# -*- coding: UTF-8 -*-

class stockVO:
    def __init__(self, stockField):
        # 证券代码
        self.ZQDM = stockField[0].strip()
        # ISIN代码
        self.ISIN = stockField[1].strip()
        # 记录更新时间
        self.GXSJ = stockField[2].strip()
        # 中文证券名称
        self.ZWMC = stockField[3].strip()
        # 英文证券名称
        self.YWMC = stockField[4].strip()
        # 基础证券代码
        self.JCZQDM = stockField[5].strip()
        # 市场种类
        self.SCZL = stockField[6].strip()
        # 证券类别
        self.ZQLB = stockField[7].strip()
        # 证券子类别
        self.ZQZLB = stockField[8].strip()
        # 货币种类
        self.HBZL = stockField[9].strip()
        # 面值
        self.MZ = stockField[10].strip()
        # 可流通证券未上市数量
        self.LTZQWSSSL = stockField[11].strip()
        # 最后交易日期
        self.ZHJRY = stockField[12].strip()
        # 上市日期
        self.SSRQ = stockField[13].strip()
        # 产品集SET编号
        self.CPJSET = stockField[14].strip()
        # 买数量单位
        self.BSLDW = stockField[15].strip()
        # 卖数量单位
        self.SSLDW = stockField[16].strip()
        # 申报数量下限
        self.SBSLXX = stockField[17].strip()
        # 申报数量上限
        self.SBSLSX = stockField[18].strip()
        # 前收盘价格
        self.QSPJ = stockField[19].strip()
        # 价格档位
        self.JGDW = stockField[20].strip()
        # 涨跌幅限制类型
        self.ZDFXZLX = stockField[21].strip()
        # 涨幅上限价格
        self.ZFSXJG = stockField[22].strip()
        # 跌幅下限价格
        self.DFXXJG = stockField[23].strip()
        # 除权比例
        self.CQBL = stockField[24].strip()
        # 除息金额
        self.CXJE = stockField[25].strip()
        # 融资标的标志
        self.RZBBZ = stockField[26].strip()
        # 融资券的标志
        self.RZQBZ = stockField[27].strip()
        # 产品状态标志
        self.CPZTBZ = stockField[28].strip()
        # 备注
        self.BZ = stockField[29].strip()
