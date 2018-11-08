# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     alpha001
   Description :
   Author :       haoyuan.m
   date：          2018/11/7
-------------------------------------------------
   Change Activity:
                   2018/11/7:
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
    context.len = 20
    context.len1 = 5
    context.initial = 1e7


def on_data(context):
    if dt.datetime.strftime(context.now, '%Y-%m-%d') not in context.month_begin:  # 调仓频率为月
        return
    data = get_reg_kdata(context.reg_kdata[0], [], context.len + context.len1 + 1, fill_up=True, df=True)
    if data['close'].isna().any():
        return
    datalist = [data[data['target_idx'] == x] for x in pd.unique(data.target_idx)]
    # 生成alpha001因子
    s = np.zeros(context.Tlen) * np.nan
    alpha = np.zeros(context.Tlen) * np.nan
    for target in datalist:
        x1 = np.zeros(context.len1) * np.nan
        target_idx = target.target_idx.iloc[0]
        close = target.close.values
        returns = target.close.pct_change().values
        for i in range(context.len1):
            if returns[-2 - i] < 0:
                x1[i] = returns[-context.len:].std()
            else:
                x1[i] = close[-2 - i]
        x2 = np.sign(x1) * abs(x1) ** 2
        p = np.argmax(x2)
        s[target_idx] = p
    if np.isnan(s).sum() > context.Tlen / 2:
        return
    else:
        s[np.isnan(s)] = np.inf
        mask = np.argsort(s)
        alpha[mask] = np.array(range(len(s)))
        alpha = alpha / mask.max() - 0.5
    # 策略部分
    if np.isnan(alpha).any():
        return
    else:
        targets = np.array(range(context.Tlen))
        long_positions = context.account().positions['volume_long']
        total_value = context.account().cash['total_value'].iloc[0]
        num = (alpha > 0).sum()
        money_per = total_value * 0.8 / num
        long_targets = targets[alpha > 0].tolist()
        sell_targets = targets[alpha < 0].tolist()
        # 调仓日期先平仓，再开仓。
        for target in sell_targets:
            if long_positions[target] > 0:
                order_target_volume(0, target, 0, 1, 2)
        for target in long_targets:
            if long_positions[target] == 0:
                order_value(0, target, money_per, 1, 1, 2)
#### TODo

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

