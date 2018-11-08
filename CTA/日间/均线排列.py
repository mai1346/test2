# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     均线排列
   Description :
   Author :       haoyuan.m
   date：          2018/10/22
-------------------------------------------------
   Change Activity:
                   2018/10/22:
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


def init(context):
    set_backtest(initial_cash=10000000)
    reg_kdata('day', 1)
    context.N = 61
    context.stop = np.zeros(len(context.target_list))



def on_data(context):
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=context.N + 3, fill_up=True, df=True)
    if data['close'].isna().any():
        return
    datalist = [data[data['target_idx'] == x] for x in pd.unique(data.target_idx)]
    long_positions = context.account().positions['volume_long']
    short_positions = context.account().positions['volume_short']

    for target in datalist:
        target_idx = target.target_idx.iloc[0]
        high = target.high
        low = target.low
        close = target.close
        MA10 = talib.MA(close, 10)
        MA20 = talib.MA(close, 20)
        MA40 = talib.MA(close, 40)
        MA60 = talib.MA(close, 60)
        MAhigh = talib.MA(high, 30)
        MAlow = talib.MA(low, 30)

        condi_long = (close.iloc[-1] > MAhigh.iloc[-1]) and (MA20.iloc[-1] > MA40.iloc[-1]) \
                     and (MA10.iloc[-1] > MA20.iloc[-1]) and (MA60.iloc[-1] > MA60.iloc[-2])
        condi_short = (close.iloc[-1] < MAlow.iloc[-1]) and (MA20.iloc[-1] < MA40.iloc[-1]) \
                      and (MA10.iloc[-1] < MA20.iloc[-1]) and (MA60.iloc[-1] < MA60.iloc[-2])
        if long_positions.iloc[target_idx] == 0 and short_positions.iloc[target_idx] == 0:
            if condi_long:
                order_target_percent(account_idx=0, target_idx=target_idx, target_percent=0.8 / 3, side=1, order_type=2)
                context.stop[target_idx] = min(low.iloc[-20:])
            elif condi_short:
                order_target_percent(account_idx=0, target_idx=target_idx, target_percent=0.8 / 3, side=2, order_type=2)
                context.stop[target_idx] = max(high[-20:])
        if long_positions.iloc[target_idx] > 0:
            if (close.iloc[-1] < min(close.iloc[-11:-1])) or (close.iloc[-1] < context.stop[target_idx]):
                order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=1, order_type=2)
                context.stop[target_idx] = 0
        if short_positions.iloc[target_idx] > 0:
            if (close.iloc[-1] > max(close.iloc[-11:-1])) or (close.iloc[-1] > context.stop[target_idx]):
                order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=2, order_type=2)
                context.stop[target_idx] = 0


if __name__ == '__main__':
    target = ['shfe.rb0000', 'dce.j0000', 'dce.i0000']
    run_backtest('均线排列volume', '均线排列.py', target_list=target, frequency='day', fre_num=1, begin_date='2016-01-01',
                 end_date='2017-11-21', fq=1)
