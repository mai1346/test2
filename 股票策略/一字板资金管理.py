# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     一字板资金管理
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
import pandas as pd
import datetime as dt


def init(context):
    set_backtest(initial_cash=1e7)
    reg_kdata('day', 1)
    context.Tlen = len(context.target_list)
    context.entryP = np.zeros(context.Tlen) * np.nan
    context.signalBuy = np.zeros(context.Tlen)
    context.initial = 1e7
    context.opensign = 1
    context.signnum = np.zeros(context.Tlen)
    context.stoprate = 0.05


def on_data(context):
    data = get_reg_kdata(context.reg_kdata[0], [], 2, fill_up=True, df=True)
    if data['close'].isna().any():
        return
    long_positions = context.account().positions['volume_long']
    datalist = [data[data['target_idx'] == x] for x in pd.unique(data.target_idx)]
    for target in datalist:
        target_idx = target.target_idx.iloc[0]
        volume = target.volume.values.astype(float)
        low = target.low.values.astype(float)
        high = target.high.values.astype(float)
        close = target.close.values.astype(float)
        openp = target.open.values.astype(float)
        times = target.time.values
        if volume[-1] == 0 or times[-1] != context.now or low[-1] == 0:
            continue
        if long_positions[target_idx] == 0:
            context.entryP[target_idx] = np.nan
        elif np.isnan(context.entryP[target_idx]):
            context.entryP[target_idx] = openp[-1]
        if context.opensign == 0 and (long_positions == 0).all():
            context.opensign = 1

        if long_positions[target_idx] > 0:
            if openp[-1] - context.entryP[target_idx] < -context.entryP[target_idx] * context.stoprate:
                order_target_volume(0, target_idx, 0, 1, 2)  # TODO orderside 问题
                context.signnum[target_idx] = 0
            elif openp[-1] - context.entryP[target_idx] > context.entryP[target_idx] * context.stoprate:
                context.entryP[target_idx] = openp[-1]
                if context.signnum[target_idx] == 0:
                    context.opensign = 1
                    context.signnum[target_idx] = 1
        a = close[-1] > 1.09 * close[-2]  # 较前一天涨幅超过9%
        b = close[-1] == high[-1] == openp[-1]  # 当天一字板
        c = context.opensign == 1  # 可开仓状态

        long = long_positions[target_idx] == 0 and a and b and c
        if long:
            order_value(0, target_idx, context.initial / 10, 1, 1, 2)
            context.opensign = 0


if __name__ == '__main__':
    begin = '2017-01-01'
    end = '2018-01-01'
    cons_date = dt.datetime.strptime(begin, '%Y-%m-%d') - dt.timedelta(days=1)
    targetlist = get_code_list('hs300', cons_date)['code'].tolist()
    run_backtest(strategy_name='一字板资金管理1',
                 file_path='一字板资金管理.py',
                 target_list=targetlist,
                 frequency='day',
                 fre_num=1,
                 begin_date=begin,
                 end_date=end,
                 fq=1)
