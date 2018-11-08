# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     escalator
   Description :
   Author :       haoyuan.m
   date：          2018/10/24
-------------------------------------------------
   Change Activity:
                   2018/10/24:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'
'''
 一剑封喉
在沪深300股指期货与螺纹钢期货里面按照一定比例进行组合投资。
测试时间段：2011年1月1日到2017年6月1日。
统计过去一段时间收盘价的最大值出现的位置与最小值出现的位置，
当满足过去一段时间收盘价的最小值出现的位置早于收盘价的最大值出现的位置，
同时使用均线进行简单过滤，当前价格需要在均线价格之上，则进场做多，空头的条件与之相反。
出场使用3:1的合约价值止盈止损比。
'''
# TODO 空单平仓一单一单平 空单平仓日期对不上
from atrader import *
import numpy as np
import pandas as pd
import datetime as dt


def init(context):
    set_backtest(initial_cash=10000000)
    reg_kdata('day', 1)
    context.Tlen = len(context.target_list)
    context.stoprate = 0.03
    context.N = 30


def on_data(context):
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=context.N + 3, fill_up=True, df=True)
    if data['close'].isna().any():
        return
    long_positions = context.account().positions['volume_long']
    long_hold_cost = context.account().positions['holding_cost_long']
    short_positions = context.account().positions['volume_short']
    short_hold_cost = context.account().positions['holding_cost_short']
    datalist = [data[data['target_idx'] == x] for x in pd.unique(data.target_idx)]
    mktvalue = context.account().cash['total_value'].iloc[0]
    for target in datalist:
        target_idx = target.target_idx.iloc[0]
        close = target.close.values.astype('float')[-context.N:]
        if long_positions[target_idx] > 0:
            if (close[-1] > long_hold_cost[target_idx] * (1 + 3 * context.stoprate)) or \
                    (close[-1] < long_hold_cost[target_idx] * (1 - context.stoprate)):
                order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=1,
                                   order_type=2)
        if short_positions[target_idx] > 0:
            if (close[-1] < short_hold_cost[target_idx] * (1 - 3 * context.stoprate)) or \
                    (close[-1] > short_hold_cost[target_idx] * (1 + context.stoprate)):
                order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=2,
                                   order_type=2)
        if (long_positions[target_idx] == 0) and (short_positions[target_idx] == 0):
            if (close.argmin() > close.argmax()) and (close[-1] > close.mean()):
                order_target_value(account_idx=0, target_idx=target_idx, target_value=mktvalue / context.Tlen, side=1,
                                   order_type=2)
            if (close.argmin() < close.argmax()) and (close[-1] < close.mean()):
                order_target_value(account_idx=0, target_idx=target_idx, target_value=mktvalue / context.Tlen, side=2,
                                   order_type=2)


if __name__ == '__main__':
    target = ['shfe.rb0000', 'CFFEX.IF0000']
    run_backtest('escalator', 'escalator.py', target_list=target, frequency='min', fre_num=30,
                 begin_date='2016-01-01',
                 end_date='2017-06-01', fq=1)
