# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     RangeRatio
   Description :
   Author :       haoyuan.m
   date：          2018/10/25
-------------------------------------------------
   Change Activity:
                   2018/10/25:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'
# TODO 止盈止损条件问题？
'''
 Range Ratio Trading
统计过去一段时间的最低价的最大值与最小值的差占最高价的最大值与最低价的最小值的差在一定范围内
同时满足close > average (close,N)均线过滤的有条件下，做多
统计过去一段时间的最高价的最大值与最小值的差占最高价的最大值与最低价的最小值的差在一定范围内
同时满足close < average (close,N)均线过滤的有条件下，做空
出场使用3:1的合约价值止盈止损比
'''
from atrader import *
import numpy as np
import pandas as pd
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
    context.N = 30
    context.n = 0.8
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
    mktvalue = context.account().cash['total_value'].iloc[0]
    for target in datalist:
        target_idx = target.target_idx.iloc[0]
        close = target.close.values.astype('float')[-context.N:]
        high = target.high.values.astype('float')[-context.N:]
        low = target.low.values.astype('float')[-context.N:]
        buy = (low.max() - low.min()) <= context.n * (high.max() - low.min())
        sell = (high.max() - high.min()) <= context.n * (high.max() - low.min())
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
            if not sell and buy and close[-1] > close.mean():
                order_target_value(account_idx=0, target_idx=target_idx, target_value=context.initial / context.Tlen,
                                   side=1, order_type=2)
            if sell and not buy and close[-1] < close.mean():
                order_target_value(account_idx=0, target_idx=target_idx, target_value=context.initial / context.Tlen,
                                   side=2, order_type=2)


if __name__ == '__main__':
    target = ['shfe.rb0000', 'CFFEX.IF0000']
    run_backtest('RangeRatio', 'RangeRatio.py', target_list=target, frequency='min', fre_num=30,
                 begin_date='2016-01-01',
                 end_date='2018-06-01', fq=1)