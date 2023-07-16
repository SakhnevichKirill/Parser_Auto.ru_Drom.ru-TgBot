import schedule
import time

from auto import AutoParser
from drom import DromParser

import os, sys

sys.path.insert(1, os.path.join(sys.path[0], "../"))
from bot import get_global_max_price


def AutoParse():
    ap = AutoParser(price=get_global_max_price(), debug=True)
    ap.parse_page(save_to_db=True)
    print(ap.advertisement)
    return True


def DromParse():
    dp = DromParser(price=get_global_max_price(), debug=True)
    dp.parse_page()
    print(dp.advertisement)
    return True


def ParseSources():
    AutoParse()
    DromParse()


schedule.every(1).minutes.do(ParseSources)

while True:
    schedule.run_pending()
    time.sleep(1)
    print("sleep...")
