# -*- coding: UTF-8 -*-

import os
import platform


class path:
    def __init__(self):
        pass

    @staticmethod
    def convert(param_path):
        system = platform.system()
        # 判断是否为Windows
        if system == 'Windows':
            param_path = param_path.replace("${", "%")
            param_path = param_path.replace("}", "%")
        output = os.popen("echo " + param_path)
        return output.readline()
