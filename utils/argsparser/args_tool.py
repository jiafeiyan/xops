# -*- coding: UTF-8 -*-

import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-conf', nargs='+', required=True)
    return parser.parse_args()
