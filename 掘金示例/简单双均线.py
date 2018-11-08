# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     简单双均线
   Description :
   Author :       haoyuan.m
   date：          2018/10/10
-------------------------------------------------
   Change Activity:
                   2018/10/10:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'
from atrader import *
import numpy as np
import pandas as pd
import datetime as dt
import sys

try:
    import talib
except:
    print('请安装TA-Lib库')
    sys.exit(-1)


# %%
def init(context):
    set_backtest(initial_cash=1000000)
    reg_kdata('day', 1)
    context.win = 21
    context.long_win = 20
    context.short_win = 5


def on_data(context):
    positions = context.account().positions['volume_long']
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=context.win, fill_up=True, df=True)
    if data['close'].isna().any():
        return
    datalist = [data[data['target_idx'] == x] for x in pd.unique(data.target_idx)]
    for target in datalist:
        position = positions.iloc[target.target_idx.iloc[0]]
        ma_short = talib.MA(target.close, timeperiod=context.short_win).iloc[-1]
        ma_long = talib.MA(target.close, timeperiod=context.long_win).iloc[-1]
        if position == 0 and (ma_short > ma_long):
            order_volume(account_idx=0, target_idx=target.target_idx.iloc[0], volume=100, side=1, position_effect=1,
                         order_type=2, price=0)
        elif position > 0 and ((ma_short - ma_long) < 0):
            order_volume(account_idx=0, target_idx=target.target_idx.iloc[0], volume=int(position), side=2,
                         position_effect=2, order_type=2, price=0)


if __name__ == '__main__':
    run_backtest(strategy_name='SMA50', file_path='简单双均线.py', target_list=get_code_list('sz50')['code'],
                 frequency='day', fre_num=1, begin_date='2017-09-01', end_date='2018-09-01', fq=1)
# days = get_trading_days('SSE', '2017-01-01', '2017-12-31')
# months = np.vectorize(lambda x: x.month)(days)
# month_ends = days[pd.Series(months) != pd.Series(months).shift(-1)]
