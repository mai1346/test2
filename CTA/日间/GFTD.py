# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     GFTD
   Description :
   Author :       haoyuan.m
   date：          2018/10/29
-------------------------------------------------
   Change Activity:
                   2018/10/29:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'

from atrader import *
import numpy as np
import pandas as pd
import datetime as dt

try:
    import talib
except:
    print('请安装TA-Lib库')
    sys.exit(-1)


def init(context):
    reg_kdata('day', 1)
    context.Tlen = len(context.target_list)
    context.initial = 1e7
    context.Ndown = 5
    context.Nup = 5
    context.T1 = 2
    context.T2 = 2
    context.Natr = 10
    context.m = 5
    context.entryprice = np.ones(context.Tlen) * np.nan
    context.histExtre = np.ones(context.Tlen) * np.nan
    context.preclose = np.ones(context.Tlen) * np.nan
    context.entrytime = np.zeros(context.Tlen)
    context.pastcount = np.zeros(context.Tlen)


def getGFTD(close, volume, m, Ndown, Nup):
    diff1 = close[-Ndown:] - close[-Ndown - m:-m]
    diff2 = close[-Nup:] - close[-Nup - m:-m]
    value = int(((diff1 < 0).sum() == Ndown - (diff2 > 0).sum() == Nup) * (volume.mean() > 2000))
    value = np.array([value, int(close[-1] > close[-4:].mean() and volume[-1] >= 1.1 * volume[-4:].mean() - \
                            (close[-1] <= close[-4:].mean() and volume[-1] >= 1.1 * volume[-4:].mean()))])
    return value


def on_data(context):
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=30, fill_up=True, df=True)
    if data['close'].isna().any():
        return
    datalist = [data[data['target_idx'] == x] for x in pd.unique(data.target_idx)]
    long_positions = context.account().positions['volume_long']
    short_positions = context.account().positions['volume_short']
    for target in datalist:
        target_idx = target.target_idx.iloc[0]
        high = target.high.values.astype(float)
        low = target.low.values.astype(float)
        close = target.close.values.astype(float)
        volume = target.volume.values.astype(float)
        openp = target.open.values.astype(float)

        atr = talib.ATR(high, low, close, context.Natr)
        TD = getGFTD(close, volume, context.m, context.Ndown, context.Nup)
        if long_positions[target_idx] == 0 and short_positions[target_idx] == 0:
            context.entryprice[target_idx] = np.nan
            context.histExtre[target_idx] = np.nan
        elif np.isnan(context.entryprice[target_idx]):
            context.entryprice[target_idx] = openp[-1]

        if long_positions[target_idx] > 0:
            context.histExtre[target_idx] = max(context.histExtre[target_idx], high[-1])
        if short_positions[target_idx] > 0:
            context.histExtre[target_idx] = min(context.histExtre[target_idx], low[-1])
        # 平仓条件
        long_close = long_positions[target_idx] > 0 and (context.entryprice[target_idx] - close[-1]) > \
                     min(2.5 * atr[-1], close[-1] * 0.06)
        short_close = short_positions[target_idx] > 0 and -(context.entryprice[target_idx] - close[-1]) > \
                      min(2.5 * atr[-1], close[-1] * 0.06)
        long_profit = long_positions[target_idx] > 0 and (close[-1] - context.entryprice[target_idx]) > \
                      min(3 * atr[-1], close[-1] * 0.06)
        short_profit = short_positions[target_idx] > 0 and -(context.entryprice[target_idx] - close[-1]) > \
                       min(2.5 * atr[-1], close[-1] * 0.06)
        if long_profit or short_profit:
            context.entryprice[target_idx] = close[-1]
        if TD[0] != 0:
            context.pastcount[target_idx] = TD[0]
        if short_close or long_close or context.entrytime[target_idx] > 30:
            context.pastcount[target_idx] = 0
        if abs(context.pastcount[target_idx]) == 1 and np.isnan(context.preclose[target_idx]):
            context.preclose[target_idx] = close[-1]
        if context.pastcount[target_idx] == 0:
            context.preclose[target_idx] = np.nan

        add_sig = context.pastcount[target_idx] * TD[1] > 0 and context.pastcount[target_idx] * (close[-1] - context.preclose[target_idx]) >= 0
        if add_sig:
            context.preclose[target_idx] = close[-1]
            context.pastcount[target_idx] += np.sign(context.pastcount[target_idx])
        if (long_close or short_close) and context.pastcount[target_idx] > context.T1:
            context.pastcount[target_idx] = context.T1 - 1
        if (long_close or short_close) and context.pastcount[target_idx] < -context.T2:
            context.pastcount[target_idx] = -context.T2 + 1
        if context.entrytime[target_idx] > 30:
            context.entrytime[target_idx] = 0
        if context.entrytime[target_idx] == 0 and abs(context.pastcount[target_idx]) > 0:
            context.entrytime[target_idx] = 1
        if context.entrytime[target_idx] != 0:
            context.entrytime[target_idx] += 1

        # 开仓条件：
        long_open = context.pastcount[target_idx] > context.T1 and long_positions[target_idx] == 0 and \
                    short_positions[target_idx] == 0 and close[-1] >= close.mean()
        short_open = context.pastcount[target_idx] < -context.T2 and long_positions[target_idx] == 0 and \
                     short_positions[target_idx] == 0 and close[-1] <= close.mean()
        if long_open:
            order_value(0, target_idx, context.initial, 1, 1, 2)
        if short_open:
            order_value(0, target_idx, context.initial, 2, 1, 2)
        if long_positions[target_idx] > 0 and long_close:
            order_target_volume(0, target_idx, 0, 1, 2)
        if short_positions[target_idx] > 0 and short_close:
            order_target_volume(0, target_idx, 0, 2, 2)


if __name__ == '__main__':
    target = ['czce.sr000', 'shfe.rb0000', 'dce.j0000']
    run_backtest('GFTD', 'GFTD.py', target_list=target, frequency='day', fre_num=1,
                 begin_date='2016-01-01',
                 end_date='2018-06-01', fq=1)
