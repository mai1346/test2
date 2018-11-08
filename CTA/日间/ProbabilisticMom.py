# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     ProbabilisticMom
   Description :
   Author :       haoyuan.m
   date：          2018/10/25
-------------------------------------------------
   Change Activity:
                   2018/10/25:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'
# TODO 交易次数明显偏少，条件未触发
'''
 Probabilistic Momentum +Fisherman Plus
在沪深300股指期货与螺纹钢期货里面按照1:50的标准进行投资。
测试时间段：2011年1月1日到2017年1月1日。
在Probabilistic Momentum +Fisherman的基础上增加滚动式止盈止损。
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
    context.stoprate = 0.02
    context.N = 20
    context.initial = 10000000
    context.entryP = np.zeros(context.Tlen) * np.nan


def on_data(context):
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=context.N + 4, fill_up=True, df=True)
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
        openp = target.open.values.astype('float')[-context.N:]
        high = target.high.values.astype('float')[-context.N:]
        low = target.low.values.astype('float')[-context.N:]
        spread = high - low
        if long_positions[target_idx] == 0 and short_positions[target_idx] == 0:
            context.entryP[target_idx] = np.nan
        elif np.isnan(context.entryP[target_idx]):
            context.entryP[target_idx] = openp[-1]
        condi_short1 = spread[-1] < 0.5 * spread.mean() and close[-1] < close[-2]
        condi_long1 = spread[-1] < 0.5 * spread.mean() and close[-1] > close[-2]
        condi_short2 = spread[-1] > 1.5 * spread.mean() and close[-1] > close[-2]
        condi_long2 = spread[-1] > 1.5 * spread.mean() and close[-1] > close[-2]

        # 平仓条件
        if long_positions[target_idx] > 0:
            if (close[-1] > long_hold_cost[target_idx] * (1 + 3 * context.stoprate)) or \
                    (close[-1] < context.entryP[target_idx] * (1 - context.stoprate)):
                order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=1,
                                    order_type=2)
            if close[-1] > context.entryP[target_idx] * (1 + 1 * context.stoprate):
                context.entryP[target_idx] = close[-1]
        if short_positions[target_idx] > 0:
            if (close[-1] < short_hold_cost[target_idx] * (1 - 3 * context.stoprate)) or \
                    (close[-1] < context.entryP[target_idx] * (1 + context.stoprate)):
                order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=2,
                                    order_type=2)
            if close[-1] < context.entryP[target_idx] * (1 - 1 * context.stoprate):
                context.entryP[target_idx] = close[-1]
        # 开仓条件
        if (long_positions[target_idx] == 0) and (short_positions[target_idx] == 0):
            if (condi_long1 or condi_long2) and close[-1] > close.mean():
                order_target_value(account_idx=0, target_idx=target_idx, target_value=context.initial / context.Tlen,
                                   side=1, order_type=2)
            if (condi_short1 or condi_short2) and close[-1] < close.mean():
                order_target_value(account_idx=0, target_idx=target_idx, target_value=context.initial / context.Tlen,
                                   side=2, order_type=2)


if __name__ == '__main__':
    target = ['shfe.rb0000', 'DCE.j0000', 'cffex.if0000']
    run_backtest('ProbabilisticMom', 'ProbabilisticMom.py', target_list=target, frequency='min', fre_num=30,
                 begin_date='2016-01-01',
                 end_date='2018-06-01', fq=1)
