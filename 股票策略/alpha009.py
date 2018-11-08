# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     test
   Description :
   Author :       haoyuan.m
   date：          2018/11/8
-------------------------------------------------
   Change Activity:
                   2018/11/8:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'
from atrader import *
import numpy as np
import pandas as pd
import datetime as dt


def init(context):
    set_backtest(initial_cash=1e7)
    reg_kdata('day', 1)
    days = get_trading_days('SSE', '2016-01-01', '2018-01-01')
    months = np.vectorize(lambda x: x.month)(days)
    month_begin = days[pd.Series(months) != pd.Series(months).shift(1)]
    context.month_begin = pd.Series(month_begin).dt.strftime('%Y-%m-%d').tolist()
    context.Tlen = len(context.target_list)
    context.len = 220
    context.len1 = 5
    context.num = 20
    context.initial = 1e7


def on_data(context):
    if dt.datetime.strftime(context.now, '%Y-%m-%d') not in context.month_begin:  # 调仓频率为月
        return
    data = get_reg_kdata(context.reg_kdata[0], [], context.len, fill_up=True, df=True)
    if data['close'].isna().any():
        return
    long_positions = context.account().positions['volume_long']
    total_value = context.account().cash['total_value'].iloc[0]
    alpha009 = np.zeros(context.Tlen) * np.nan
    close = data.close.values.reshape(-1, context.len).astype(float)
    volume = data.volume.values.reshape(-1, context.len).astype(float)
    high = data.high.values.reshape(-1, context.len).astype(float)
    low = data.low.values.reshape(-1, context.len).astype(float)

    delta = np.diff(close, axis=1)
    c1 = delta[:, -5:].min(axis=1) > 0
    c2 = delta[:, -5:].max(axis=1) < 0
    c21 = np.logical_and(~c1, c2)
    c3 = np.logical_or(c1, c2)
    alpha009[c1] = delta[:, -1]
    alpha009[c21] = delta[:, -1]
    alpha009[~c3] = -delta[:, -1]
    num = (np.isnan(alpha009) > 0).sum()
    if num > context.Tlen - context.num:
        return
    targets = np.array(range(context.Tlen)).tolist()
    selected = set(np.argsort(alpha009)[-context.num:])
    money_per = total_value * 0.8 / context.num
    valid = set(targets[np.logical_and(volume[:, -1] != 0, high[:, -1] != low[:, -1])])
    opened = set(targets[long_positions > 0])
    short_targets = valid & opened - selected
    long_targets = valid & selected
    for target in short_targets:
        order_target_volume(0, target, 0, 1, 2)
    for target in long_targets:
        order_value(0, target, money_per, 1, 1, 2)


if __name__ == '__main__':
    begin = '2016-01-01'
    end = '2018-01-01'
    cons_date = dt.datetime.strptime(begin, '%Y-%m-%d') - dt.timedelta(days=1)
    targetlist = get_code_list('hs300', cons_date)['code'].tolist()
    run_backtest(strategy_name='alpha001',
                 file_path='alpha001.py',
                 target_list=targetlist,
                 frequency='day',
                 fre_num=1,
                 begin_date=begin,
                 end_date=end,
                 fq=1)