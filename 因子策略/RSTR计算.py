# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     RSTR计算
   Description :
   Author :       haoyuan.m
   date：          2018/10/31
-------------------------------------------------
   Change Activity:
                   2018/10/31:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'
from atrader import *
import numpy as np
from sqlalchemy import create_engine

conTL = create_engine('mssql+pymssql://QRUser04:Passw0rdBP@10.86.166.13/TLDB')
Market = pd.read_sql("SELECT a.TRADE_DATE, a.TICKER_SYMBOL, a.CLOSE_PRICE_1 as 'close' \
                   FROM TLDB.dbo.mkt_equd_adj \
                   WHERE a.TRADE_DATE > '2007-01-01' \
                   and a.TRADE_DATE <= '2018-10-30' \
                   ORDER by TICKER_SYMBOL, TRADE_DATE", conTL)
