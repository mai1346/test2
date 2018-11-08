# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     成分股多空占比
   Description :
   Author :       haoyuan.m
   date：          2018/11/6
-------------------------------------------------
   Change Activity:
                   2018/11/6:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'
from atrader import *
import numpy as np
import datetime as dt
import sys

try:
    import talib
except:
    print('请安装TA-Lib库')
    sys.exit(-1)


def init(context):
    set_backtest(initial_cash=1e7)
    reg_kdata('day', 1)
    context.len = 3  # 回顾周期，选择的历史对比周期数
    context.len2 = 1  # 周期内满足条件的天数 (len2 <= len)
    context.initial = 1e7


def ma(close, win):
    result = []
    for start in range(close.shape[1] - win + 1):
        end = start + win
        ma = close[:, start:end].mean(axis=1)
        result.append(ma)
    return np.array(result)


def on_data(context):
    cons = get_reg_kdata(context.reg_kdata[0], [x for x in range(300)], 25 + context.len, fill_up=True, df=True)
    if cons['close'].isna().any():
        return
    long_positions = context.account().positions['volume_long'][300]
    close = cons.close.values.reshape(-1, context.len + 25)
    time = cons.time.values.reshape(-1, context.len + 25)
    ma5 = ma(close, 5)
    ma5_diff = np.diff(ma5, axis=0)
    ma10 = ma(close, 10)
    ma10_diff = np.diff(ma10, axis=0)
    ma20 = ma(close, 20)
    ma20_diff = np.diff(ma20, axis=0)
    aux = np.zeros(300)
    a = close[:, -1] > ma5[-1]
    b = (ma5_diff >= 0).sum(axis=0) >= context.len2
    c = (ma10_diff >= 0).sum(axis=0) >= context.len2
    d = (ma20_diff >= 0).sum(axis=0) >= context.len2
    e = (ma5[-context.len:] >= ma10[-context.len:]).sum(axis=0) >= context.len2
    f = (ma10[-context.len:] >= ma20[-context.len:]).sum(axis=0) >= context.len2
    long = np.logical_and.reduce((a, b, c, d, e, f))
    a_s = close[:, -1] <= ma5[-1]
    b_s = (ma5_diff <= 0).sum(axis=0) >= context.len2
    c_s = (ma10_diff <= 0).sum(axis=0) >= context.len2
    d_s = (ma20_diff <= 0).sum(axis=0) >= context.len2
    e_s = (ma5[-context.len:] <= ma10[-context.len:]).sum(axis=0) >= context.len2
    f_s = (ma10[-context.len:] <= ma20[-context.len:]).sum(axis=0) >= context.len2
    short = np.logical_and.reduce((a_s, b_s, c_s, d_s, e_s, f_s))
    aux[long] = 1
    aux[short] = -1
    long_ratio = (aux == 1).sum() / (time[:, -1] == context.now).sum()  # 可交易股票个数
    short_ratio = (aux == -1).sum() / (time[:, -1] == context.now).sum()  # 可交易股票个数
    if long_positions == 0 and long_ratio > 0.15 > short_ratio:
        order_value(0, 300, context.initial, 1, 1, 2)
    elif long_positions > 0 and long_ratio < 0.15 < short_ratio:
        order_target_volume(0, 300, 0, 2, 2)


if __name__ == '__main__':
    begin = '2015-01-01'
    end = '2018-06-01'
    cons_date = dt.datetime.strptime(begin, '%Y-%m-%d') - dt.timedelta(days=1)
    targetlist = get_code_list('hs300', cons_date)['code'].tolist()
    targetlist.append('CFFEX.IF0000')
    run_backtest(strategy_name='成分股多空占比',
                 file_path='成分股多空占比.py',
                 target_list=targetlist,
                 frequency='day',
                 fre_num=1,
                 begin_date=begin,
                 end_date=end,
                 fq=1)
