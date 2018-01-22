# -*- coding: UTF-8 -*-

import argparse


def parse_args(*args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-conf', nargs='+', required=True)
    for arg in args:
        parser.add_argument(arg)
    return parser.parse_args()
