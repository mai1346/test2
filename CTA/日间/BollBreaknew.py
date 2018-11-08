# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     BollBreaknew
   Description :
   Author :       haoyuan.m
   date：          2018/10/25
-------------------------------------------------
   Change Activity:
                   2018/10/25:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'
# TODO 未完成 原始文件止盈信号有问题, 平仓信号可能有问题。
'''
 布林带突破趋势策略
多头入场：当前价格突破布林带上轨
空头入场：当前价格跌破布林带下轨
止损：开仓价格之下N倍ATR
止盈：开仓价格之上N倍ATR
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
    context.entryP = np.zeros(context.Tlen) * np.nan
    context.Boll = 10
    context.N = 30
    context.Boll = 10
    context.ATR = 10
    context.ATRratio = 0.6
    context.initial = 10000000


def on_data(context):
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=context.N + 1, fill_up=True, df=True)
    if data['close'].isna().any():
        return
    long_positions = context.account().positions['volume_long']
    short_positions = context.account().positions['volume_short']
    datalist = [data[data['target_idx'] == x] for x in pd.unique(data.target_idx)]
    for target in datalist:
        target_idx = target.target_idx.iloc[0]
        close = target.close.values.astype('float')
        high = target.high.values.astype('float')
        low = target.low.values.astype('float')
        openp = target.open.values.astype('float')
        upperband, _, lowerband = talib.BBANDS(close, timeperiod=context.Boll, nbdevup=2, nbdevdn=2, matype=0)
        atr = talib.ATR(high, low, close, timeperiod=context.ATR)
        if long_positions[target_idx] == 0 and short_positions[target_idx] == 0:
            context.entryP[target_idx] = np.nan
        elif np.isnan(context.entryP[target_idx]):
            context.entryP[target_idx] = openp[-1]
        # 多单止损
        long_close = long_positions[target_idx] > 0 and \
                     (close[-1] - context.entryP[target_idx]) < -context.ATRratio * atr[-1]
        # 空单止损
        short_close = short_positions[target_idx] > 0 and \
                      (close[-1] - context.entryP[target_idx]) > context.ATRratio * atr[-1]
        # 多单止盈
        long_profit = long_positions[target_idx] > 0 and \
                      ((close[-1] - context.entryP[target_idx]) > context.ATRratio * atr[-1])
        # 空单止盈
        short_profit = short_positions[target_idx] > 0 and \
                       ((close[-1] - context.entryP[target_idx]) < -context.ATRratio * atr[-1])
        # 开仓
        long_open = long_positions[target_idx] == 0 and short_positions[target_idx] == 0 and close[-1] > upperband[-1]
        short_open = long_positions[target_idx] == 0 and short_positions[target_idx] == 0 and close[-1] < lowerband[-1]
        if long_open:
            order_target_value(account_idx=0, target_idx=target_idx, target_value=context.initial / context.Tlen,
                               side=1, order_type=2)
            print('开多')
        elif short_open:
            order_target_value(account_idx=0, target_idx=target_idx, target_value=context.initial / context.Tlen,
                               side=2, order_type=2)
            print('开空')
        # 平仓
        if long_close:
            order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=1, order_type=2)
            print('多单止损')
        if long_profit:
            order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=1, order_type=2)
            context.entryP[target_idx] = close[-1]
            print('多单止盈')
        if short_close:
            order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=2, order_type=2)
            print('空单止损')
        if short_profit:
            order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=2, order_type=2)
            context.entryP[target_idx] = close[-1]
            print('空单止盈')


if __name__ == '__main__':
    target = ['cffex.if0000', 'shfe.rb0000']
    run_backtest('BollBreaknew', 'BollBreaknew.py', target_list=target, frequency='min', fre_num=60,
                 begin_date='2016-01-01',
                 end_date='2018-06-01', fq=1)
