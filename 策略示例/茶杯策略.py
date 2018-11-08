# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     茶杯策略
   Description :
   Author :       haoyuan.m
   date：          2018/10/25
-------------------------------------------------
   Change Activity:
                   2018/10/25:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'
# TODO 空头曲线下降严重。止损？
'''
 茶杯策略
首先定义杯子与倒杯子形态，然后寻找切入点进行交易。
寻找上涨趋势中的杯子形态，寻找此处作为入场点
同时满足close > average (close,N)均线过滤的有条件下，做多
寻找下跌趋势中的杯子形态，寻找此处作为入场点
同时满足close < average (close,N)均线过滤的有条件下，做空
出场使用并滚动式止盈止损。
在沪深300股指期货与螺纹钢期货里面按照1:50的标准进行投资。测试时间段：2011年1月1日到2017年1月1日。
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
    context.entryP = np.zeros(context.Tlen)
    context.N = 20
    context.stoprate = 0.02
    context.initial = 10000000


def on_data(context):
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=context.N + 3, fill_up=True, df=True)  # 获取所有标的数据
    if data['close'].isna().any():
        return
    mktvalue = context.account().cash['total_value'].iloc[0]
    datalist = [data[data['target_idx'] == x] for x in pd.unique(data.target_idx)]
    long_positions = context.account().positions['volume_long']
    short_positions = context.account().positions['volume_short']
    for target in datalist:
        target_idx = target.target_idx.iloc[0]
        close = target.close.values.astype('float')
        openp = target.open.values.astype('float')
        high = target.high.values.astype('float')
        low = target.low.values.astype('float')
        ma20 = talib.MA(close, context.N)
        if long_positions[target_idx] == 0 and short_positions[target_idx] == 0:
            context.entryP[target_idx] = np.nan
        elif np.isnan(context.entryP[target_idx]):
            context.entryP[target_idx] = openp[-1]
        # 平仓
        if long_positions[target_idx] > 0:
            if close[-1] > context.entryP[target_idx] * (1 + 3 * context.stoprate) or \
                    close[-1] < context.entryP[target_idx] * (1 - context.stoprate):
                order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=1, order_type=2)
            if close[-1] > context.entryP[target_idx] * (1 + 1 * context.stoprate):
                context.entryP[target_idx] = close[-1]
        if short_positions[target_idx] > 0:
            if close[-1] < context.entryP[target_idx] * (1 - 3 * context.stoprate) or \
                    close[-1] > context.entryP[target_idx] * (1 + context.stoprate):
                order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=2, order_type=2)
            if close[-1] < context.entryP[target_idx] * (1 - 1 * context.stoprate):
                context.entryP[target_idx] = close[-1]
        # 开仓
        if low[-1] > low[-2] and low[-2] < low[-5:-2].min() and close[-1] > ma20[-1]:
            order_target_value(account_idx=0, target_idx=target_idx, target_value=context.initial / context.Tlen,
                               side=1, order_type=2)
        if high[-1] < high[-2] and high[-2] > high[-5:-2].max() and close[-1] < ma20[-1]:
            order_target_value(account_idx=0, target_idx=target_idx, target_value=context.initial / context.Tlen,
                               side=2, order_type=2)


if __name__ == '__main__':
    target = ['dce.j0000', 'shfe.rb0000']
    run_backtest('茶杯策略', '茶杯策略.py', target_list=target, frequency='min', fre_num=30, begin_date='2016-01-01',
                 end_date='2018-06-01', fq=1)


