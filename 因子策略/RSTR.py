# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     RSTR
   Description :
   Author :       haoyuan.m
   date：          2018/10/30
-------------------------------------------------
   Change Activity:
                   2018/10/30:
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
    context.win = 21
    context.Tlen = len(context.target_list)
    context.target = np.array(range(context.Tlen))
    days = get_trading_days('SSE', '2017-09-01', '2019-09-01')
    months = np.vectorize(lambda x: x.month)(days)
    month_begin = days[pd.Series(months) != pd.Series(months).shift(1)]
    context.month_begin = pd.Series(month_begin).dt.strftime('%Y-%m-%d').tolist()


def on_data(context):
    positions = context.account().positions['volume_long'].values
    if dt.datetime.strftime(context.now, '%Y-%m-%d') not in context.month_begin:  # 调仓频率为月
        return
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=context.win, fill_up=True, df=True)
    if data['close'].isna().any():
        return
    if positions.any() > 0:
        order_close_all()
    cash = context.account().cash['total_value'].iloc[0]
    closep = data.close.values.reshape(-1, context.win).astype(float)
    rstr = np.diff(np.log(closep)).mean(axis=1)
    threshold = np.percentile(rstr, 80, interpolation='higher')
    long = np.logical_and(positions == 0, rstr > threshold)
    #close = np.logical_and(positions > 0, rstr < threshold)
    target_long = context.target[long]
    order_values = cash / len(target_long)
    # target_close = context.target[close]
    v_order_long = np.vectorize(order_value, otypes=['float'])
    # v_order_close = np.vectorize(order_target_volume, otypes=[int])

    # order_volumes = (order_value / closep[:, -1])[long].astype(int)
    # v_order_close(account_idx=0, target_idx=target_close, target_volume=0, side=1, order_type=2)
    # for target in target_long:

    #     order_value(account_idx=0, target_idx=target, value=order_values, side=1, position_effect=1, order_type=2)
    v_order_long(account_idx=0, target_idx=target_long, value=order_values, side=1, position_effect=1, order_type=2)


if __name__ == '__main__':
    szse = get_code_list('szse_a')['code']
    sse = get_code_list('sse_a')['code']
    target_list = szse.append(sse).tolist()
    run_backtest(strategy_name='RSTR', file_path='RSTR.py', target_list=target_list,
                 frequency='day', fre_num=1, begin_date='2017-09-01', end_date='2018-09-01', fq=1)
