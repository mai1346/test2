# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     RSI
   Description :
   Author :       haoyuan.m
   date：          2018/11/5
-------------------------------------------------
   Change Activity:
                   2018/11/5:
-------------------------------------------------
"""
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
    context.rsi = 20
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
        close = target.close.values.astype(float)
        openp = target.open.values.astype(float)
        rsi = talib.RSI(close, context.rsi)
        ma5 = talib.MA(close, 5)
        ma55 = talib.MA(close, 55)
        ma233 = talib.MA(close, 233)
        ma21 = talib.MA(close, 21)
        if long_positions[target_idx] > 0:
            if close[-1] <= context.stopprice[target_idx]:
                order_target_volume(0, target_idx, 0, 1, 2)
                context.buyprice[target_idx] = 0
                context.times[target_idx] = context.time_now
                context.stopprice[target_idx] = 0
                context.counts[target_idx] = 0
            p16 = close[-1] >= 1.1 * context.buyprice[target_idx] and context.buyprice[target_idx] != 0
            if p16:
                context.stopprice[target_idx] = context.stopprice[target_idx] + (close[-1] - \
                                                                                 context.stopprice[target_idx]) * 0.618
                context.buyprice[target_idx] = close[-1]
                context.counts[target_idx] += 1
                if context.counts[target_idx] >= 2:
                    context.stopprice[target_idx] = close[-1]
                p17 = context.times[target_idx] != context.time_now and context.counts[target_idx] <= 4
                if p17:
                    order_value(0, target_idx, context.initial / context.Tlen * 10, 1, 1, 2)
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
        a = long_positions[target_idx] == 0  # 空仓
        b = target_idx in context.candidates  # 在备选池
        c = context.times[target_idx] != context.time_now
        d = context.counts[target_idx] == 0
        long_open = a and b and c and d
        p20 = 40 < rsi[-1] < 70
        p21 = ma5[-1] > ma21[-1] and ma5[-2] > ma21[-2]
        p221 = openp[-1] < close[-1] and openp[-2] < close[-2] and openp[-3] < close[-3]
        p224 = openp[-1] > close[-2] or abs((close[-2] - openp[-1]) / openp[-1]) < 0.001
        p225 = openp[-2] > close[-3] or abs((close[-3] - openp[-2]) / openp[-2]) < 0.001
        p23 = p221 and p224 and p225 and p20 and p21
        if long_open and p23:
            order_value(0, target_idx, context.initial / context.Tlen * 10, 1, 1, 2)
            context.buyprice[target_idx] = close[-1]
            context.stopprice[target_idx] = close[-1] * 0.9382


if __name__ == '__main__':
    target = get_code_list('hs300')['code']
    run_backtest('RSI', 'RSI.py', target_list=target, frequency='day', fre_num=1,
                 begin_date='2015-01-01',
                 end_date='2018-01-01', fq=1)



