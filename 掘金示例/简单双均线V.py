# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     简单双均线V
   Description :
   Author :       haoyuan.m
   date：          2018/10/26
-------------------------------------------------
   Change Activity:
                   2018/10/26:
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
    # reg_userindi(indi_func=gen_signal)
    context.win = 21
    context.long_win = 20
    context.short_win = 5
    context.Tlen = len(context.target_list)


def on_data(context):
    positions = context.account().positions['volume_long'].values
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=context.win, fill_up=True, df=True)
    if data['close'].isna().any():
        return
    close = data.close.values.reshape(-1, context.win).astype(float)
    mashort = close[:, -context.short_win:].mean(axis=1)
    malong = close[:, -context.long_win:].mean(axis=1)
    target = np.array(range(context.Tlen))
    long = np.logical_and(positions == 0, mashort > malong)
    short = np.logical_and(positions > 0, mashort < malong)
    target_long = target[long].tolist()
    target_short = target[short].tolist()
    positions_short = positions[short]
    v_order = np.vectorize(order_volume)
    v_order(account_idx=0, target_idx=target_long, volume=100, side=1, position_effect=1,
            order_type=2, price=0)
    v_order(account_idx=0, target_idx=target_short, volume=positions_short, side=2,
            position_effect=2, order_type=2, price=0)


if __name__ == '__main__':
    szse = get_code_list('szse_a')['code']
    sse = get_code_list('sse_a')['code']
    target_list = szse.append(sse).tolist()
    run_backtest(strategy_name='SMAVALLA', file_path='简单双均线V.py', target_list=target_list,
                 frequency='day', fre_num=1, begin_date='2017-09-01', end_date='2018-09-01', fq=1)
# days = get_trading_days('SSE', '2017-01-01', '2017-12-31')
# months = np.vectorize(lambda x: x.month)(days)
# month_ends = days[pd.Series(months) != pd.Series(months).shift(-1)]

