# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     BollTrading
   Description :
   Author :       haoyuan.m
   date：          2018/11/2
-------------------------------------------------
   Change Activity:
                   2018/11/2:
-------------------------------------------------
"""
# TODO 投入金额问题
__author__ = 'haoyuan.m'
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
    set_backtest(initial_cash=1e8)
    reg_kdata('day', 1)
    context.Tlen = len(context.target_list)
    context.buyprice = np.zeros(context.Tlen)
    context.stopprice = np.zeros(context.Tlen)
    context.times = np.zeros(context.Tlen).tolist()
    context.counts = np.zeros(context.Tlen)
    context.candidates = []
    context.candidates_times = np.zeros(context.Tlen).tolist()
    context.selltimes = np.zeros(context.Tlen).tolist()
    context.ma = 233
    context.atr = 20
    context.boll = 20
    context.initial = 1e8
    context.time_now = 0


def on_data(context):
    context.time_now += 1
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=context.ma + 4, fill_up=True, df=True)
    if data['close'].isna().any():
        return
    long_positions = context.account().positions['volume_long']
    datalist = [data[data['target_idx'] == x] for x in pd.unique(data.target_idx)]
    for target in datalist:
        target_idx = target.target_idx.iloc[0]
        high = target.high.values.astype(float)
        low = target.low.values.astype(float)
        close = target.close.values.astype(float)
        atr = talib.ATR(high, low, close, context.atr)
        upperband, _, lowerband = talib.BBANDS(close, timeperiod=context.boll, nbdevup=2, nbdevdn=2, matype=0)
        ma55 = talib.MA(close, 55)
        ma233 = talib.MA(close, 233)
        if long_positions[target_idx] > 0:
            p12 = (close[-1] <= context.buyprice[target_idx] - 2 * atr[-1]) or \
                  (close[-1] <= context.stopprice[target_idx])
            if p12:
                order_target_volume(0, target_idx, 0, 1, 2)
                context.buyprice[target_idx] = 0
                context.times[target_idx] = context.time_now
                context.stopprice[target_idx] = 0
                context.counts[target_idx] = 0
                context.selltimes[target_idx] = context.time_now
            p16 = close[-1] >= 1.1 * context.buyprice[target_idx] and context.buyprice[target_idx] != 0 and \
                  context.times[target_idx] != context.time_now
            if p16:
                context.stopprice[target_idx] = close[-1] * 0.9618
                context.buyprice[target_idx] = close[-1]
                context.counts[target_idx] += 1
                if context.counts[target_idx] >= 2:
                    context.stopprice[target_idx] = close[-1]
                p17 = context.times[target_idx] != context.time_now and context.counts[target_idx] <= 4
                if p17:
                    order_value(0, target_idx, context.initial / context.Tlen *10, 1, 1, 2)
                context.times[target_idx] = context.time_now
        p34 = ma55[-3] > ma233[-3] and ma55[-2] > ma233[-2] and ma55[-1] > ma233[-1]
        if p34:
            context.candidates_times[target_idx] = context.time_now
            p35 = (context.time_now - context.candidates_times[target_idx]) >= 150
            p36 = (context.time_now - context.candidates_times[target_idx]) < 150
            if p36:
                context.candidates.append(target_idx)
            if p35:
                context.candidates_times[target_idx] = 0
        a = long_positions[target_idx] == 0
        b = target_idx in context.candidates
        c = context.times[target_idx] != context.time_now
        d = context.counts[target_idx] == 0
        e = context.time_now - context.selltimes[target_idx] > 23
        long_open = a and b and c and d and e
        if long_open and (close[-1] > upperband[-1]) and (upperband[-1] - lowerband[-1]) > 1.2 * (
                upperband - lowerband)[-21:].mean():
            order_value(0, target_idx, context.initial / context.Tlen * 10, 1, 1, 2)
            context.buyprice[target_idx] = close[-1]
            context.stopprice[target_idx] = close[-1] * 0.9382


if __name__ == '__main__':
    target = get_code_list('hs300')['code']
    run_backtest('BollTrading2p', 'BollTrading2.py', target_list=target, frequency='day', fre_num=1,
                 begin_date='2015-01-01',
                 end_date='2018-01-01', fq=1)
