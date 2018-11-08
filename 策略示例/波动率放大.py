# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     波动率放大
   Description :
   Author :       haoyuan.m
   date：          2018/10/25
-------------------------------------------------
   Change Activity:
                   2018/10/25:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'
'''
 波动率放大+均线突破+日历过滤+滚动止损止盈
进场只在每周的周一到周四进行，周五不进场开仓，但可以平仓。
寻找波动率放大突破点，同时满足close > average (close,N)均线过滤的有条件下，做多
寻找波动率放大突破点，同时满足close < average (close,N)均线过滤的有条件下，做空
出场使用3:1的合约价值止盈止损比
在沪深300股指期货与螺纹钢期货里面按照1:50的标准进行投资。
'''
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
    context.Tlen = len(context.target_list)
    context.stoprate = 0.03
    context.N = 20
    context.initial = 10000000


def on_data(context):
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=context.N + 3, fill_up=True, df=True)
    if data['close'].isna().any():
        return
    long_positions = context.account().positions['volume_long']
    long_hold_cost = context.account().positions['holding_cost_long']
    short_positions = context.account().positions['volume_short']
    short_hold_cost = context.account().positions['holding_cost_short']
    datalist = [data[data['target_idx'] == x] for x in pd.unique(data.target_idx)]
    for target in datalist:
        target_idx = target.target_idx.iloc[0]
        close = target.close.values.astype('float')[-context.N:]
        high = target.high.values.astype('float')[-context.N:]
        low = target.low.values.astype('float')[-context.N:]
        openp = target.open.values.astype('float')[-context.N:]
        e = high - openp
        f = openp - low
        g = e[-6:-1].mean()
        j = f[-6:-1].mean()
        # 平仓条件
        if long_positions[target_idx] > 0:
            if (close[-1] > long_hold_cost[target_idx] * (1 + 3 * context.stoprate)) or \
                    (close[-1] < long_hold_cost[target_idx] * (1 - context.stoprate)):
                order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=1,
                                    order_type=2)
        if short_positions[target_idx] > 0:
            if (close[-1] < short_hold_cost[target_idx] * (1 - 3 * context.stoprate)) or \
                    (close[-1] > short_hold_cost[target_idx] * (1 + context.stoprate)):
                order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=2,
                                    order_type=2)
        # 开仓条件
        if (long_positions[target_idx] == 0) and (short_positions[target_idx] == 0):
            if openp[-1] + g <= close[-1] and context.now.weekday() != 4 and close[-1] > close.mean():
                order_target_value(account_idx=0, target_idx=target_idx, target_value=context.initial / context.Tlen,
                                   side=1, order_type=2)
            if openp[-1] - j >= close[-1] and context.now.weekday() != 4 and close[-1] < close.mean():
                order_target_value(account_idx=0, target_idx=target_idx, target_value=context.initial / context.Tlen,
                                   side=2, order_type=2)


if __name__ == '__main__':
    target = ['shfe.rb0000', 'DCE.j0000']
    run_backtest('波动率放大', '波动率放大.py', target_list=target, frequency='min', fre_num=30,
                 begin_date='2016-01-01',
                 end_date='2018-06-01', fq=1)
