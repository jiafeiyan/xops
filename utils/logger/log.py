# -*- coding: UTF-8 -*-
import logging
import sys


class log:
    def __init__(self):
        pass

    # ERROR
    # WARNING
    # INFO
    # DEBUG
    @staticmethod
    def get_logger(category, verbose=logging.INFO):
        logger = logging.getLogger(category)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')
        logger.addHandler(console_handler)
        logger.setLevel(verbose)
        return logger
