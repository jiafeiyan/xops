# -*- coding: UTF-8 -*-

class stockVO:
    def __init__(self, stockField):
        # 证券代码
        self.ZQDM = stockField[0].strip() if stockField is not None else None
        # ISIN代码
        self.ISIN = stockField[1].strip() if stockField is not None else None
        # 记录更新时间
        self.GXSJ = stockField[2].strip() if stockField is not None else None
        # 中文证券名称
        self.ZWMC = stockField[3].strip() if stockField is not None else None
        # 英文证券名称
        self.YWMC = stockField[4].strip() if stockField is not None else None
        # 基础证券代码
        self.JCZQDM = stockField[5].strip() if stockField is not None else None
        # 市场种类
        self.SCZL = stockField[6].strip() if stockField is not None else None
        # 证券类别
        self.ZQLB = stockField[7].strip() if stockField is not None else None
        # 证券子类别
        self.ZQZLB = stockField[8].strip() if stockField is not None else None
        # 货币种类
        self.HBZL = stockField[9].strip() if stockField is not None else None
        # 面值
        self.MZ = stockField[10].strip() if stockField is not None else None
        # 可流通证券未上市数量
        self.LTZQWSSSL = stockField[11].strip() if stockField is not None else None
        # 最后交易日期
        self.ZHJRY = stockField[12].strip() if stockField is not None else None
        # 上市日期
        self.SSRQ = stockField[13].strip() if stockField is not None else None
        # 产品集SET编号
        self.CPJSET = stockField[14].strip() if stockField is not None else None
        # 买数量单位
        self.BSLDW = stockField[15].strip() if stockField is not None else None
        # 卖数量单位
        self.SSLDW = stockField[16].strip() if stockField is not None else None
        # 申报数量下限
        self.SBSLXX = stockField[17].strip() if stockField is not None else None
        # 申报数量上限
        self.SBSLSX = stockField[18].strip() if stockField is not None else None
        # 前收盘价格
        self.QSPJ = stockField[19].strip() if stockField is not None else None
        # 价格档位
        self.JGDW = stockField[20].strip() if stockField is not None else None
        # 涨跌幅限制类型
        self.ZDFXZLX = stockField[21].strip() if stockField is not None else None
        # 涨幅上限价格
        self.ZFSXJG = stockField[22].strip() if stockField is not None else None
        # 跌幅下限价格
        self.DFXXJG = stockField[23].strip() if stockField is not None else None
        # 除权比例
        self.CQBL = stockField[24].strip() if stockField is not None else None
        # 除息金额
        self.CXJE = stockField[25].strip() if stockField is not None else None
        # 融资标的标志
        self.RZBBZ = stockField[26].strip() if stockField is not None else None
        # 融资券的标志
        self.RZQBZ = stockField[27].strip() if stockField is not None else None
        # 产品状态标志
        self.CPZTBZ = stockField[28].strip() if stockField is not None else None
        # 备注
        self.BZ = stockField[29].strip() if stockField is not None else None
