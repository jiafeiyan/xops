# -*- coding: UTF-8 -*-

import trans_stockinfo
import trans_futureinfo

def init(mysql):
    parameters = {
    }
    # trans_stockinfo.transform(param=parameters, mysql=mysql)

    parameters = {
    }
    trans_futureinfo.transform(param=parameters, mysql=mysql)
