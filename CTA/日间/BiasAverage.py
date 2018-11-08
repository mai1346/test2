# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     BiasAverage
   Description :
   Author :       haoyuan.m
   date：          2018/10/24
-------------------------------------------------
   Change Activity:
                   2018/10/24:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'

'''
策略名称：BiasAverage
策略逻辑
多头进场条件：快速均线上穿慢速均线后，又掉头向下靠近慢速均线但不向下突破，再上拉时买入
空头进场条件：慢速均线上穿快速均线后，又掉头向下靠近快速均线但不向下突破，再上拉时卖出
多头出场条件：慢速均线上穿快速均线
空头出场条件：快速均线上穿慢速均线
Freq 为输入时间频率
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
    reg_kdata('min', 5)
    context.Tlen = len(context.target_list)
    context.MAfast = 25
    context.MAslow = 134
    context.bias = 40
    context.biasN = 300
    # context.stoprate = 5 / 1000
    context.sign = np.zeros(context.Tlen)


def on_data(context):
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=context.biasN + 1, fill_up=True, df=True)
    if data['close'].isna().any():
        return
    long_positions = context.account().positions['volume_long']
    short_positions = context.account().positions['volume_short']
    datalist = [data[data['target_idx'] == x] for x in pd.unique(data.target_idx)]
    mktvalue = context.account().cash['total_value'].iloc[0]
    for target in datalist:
        target_idx = target.target_idx.iloc[0]
        close = target.close.values.astype('float')
        ma1 = talib.EMA(close, 25)
        ma2 = talib.EMA(close, 134)
        spread = ma1 - ma2
        bias = talib.EMA(spread, 40)
        if ma1[-1] > ma2[-1]:
            context.sign[target_idx] = 1
        elif ma1[-1] > ma2[-1]:
            context.sign[target_idx] = -1
        # 快速均线上穿慢速均线后，又掉头向下靠近慢速均线但不向下突破，再上拉时买入
        condi_long = (spread[-2] > 0) and (bias[-3] > bias[-2]) and (bias[-2] < bias[-1]) and (bias[-1] < 10)
        # 慢速均线上穿快速均线后，又掉头向下靠近快速均线但不向下突破，再上拉时卖出
        condi_short = (spread[-2] < 0) and (bias[-3] < bias[-2]) and (bias[-2] > bias[-1]) and (bias[-1] < 10)
        if (spread[-1] < 0) and (long_positions[target_idx] > 0):
            order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=1,
                               order_type=2)
        if (spread[-1] > 0) and (short_positions[target_idx] > 0):
            order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=2,
                               order_type=2)
        elif (long_positions[target_idx] == 0) and (short_positions[target_idx] == 0):
            if condi_long and (context.sign[target_idx] == 1):
                order_target_value(account_idx=0, target_idx=target_idx, target_value=mktvalue / context.Tlen, side=1,
                                   order_type=2)
                context.sign[target_idx] = 0
            elif condi_short and (context.sign[target_idx] == -1):
                order_target_value(account_idx=0, target_idx=target_idx, target_value=mktvalue / context.Tlen, side=2,
                                   order_type=2)
                context.sign[target_idx] = 0


if __name__ == '__main__':
    target = ['shfe.rb0000']
    run_backtest('BiasAverage', 'BiasAverage.py', target_list=target, frequency='min', fre_num=5,
                 begin_date='2016-01-01',
                 end_date='2018-06-01', fq=1)
