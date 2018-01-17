# -*- coding: UTF-8 -*-

import trans_stockinfo
import trans_futureinfo

def init(mysql):
    parameters = {
        'SettlementGroupID': 'SG01',
    }
    # trans_stockinfo.transform(param=parameters, mysql=mysql)

    parameters = {
        'SettlementGroupID': 'SG02',
    }
    trans_futureinfo.transform(param=parameters, mysql=mysql)
