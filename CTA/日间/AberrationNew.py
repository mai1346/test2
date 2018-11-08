# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     AberrationNew
   Description :
   Author :       haoyuan.m
   date：          2018/10/23
-------------------------------------------------
   Change Activity:
                   2018/10/23:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'
#  TODO 未对比，未检验
from atrader import *
import numpy as np
import pandas as pd


def init(context):
    set_backtest(initial_cash=10000000)
    reg_kdata('min', 5)
    context.Tlen = len(context.target_list)  # 标的个数
    context.N = 50  # 窗口长度
    context.initial = 10000000


def on_data(context):
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=context.N + 1, fill_up=True, df=True)  # 获取所有标的数据
    if data['close'].isna().any():
        return
    datalist = [data[data['target_idx'] == x] for x in pd.unique(data.target_idx)]
    long_positions = context.account().positions['volume_long']
    short_positions = context.account().positions['volume_short']
    for target in datalist:
        target_idx = target.target_idx.iloc[0]
        close = target.close.values
        std = close.std()
        mean = close.mean()
        condi_long = close[-1] > 2 * std + mean  # 做多条件 向上突破2倍标准差
        condi_short = close[-1] < mean - 2 * std  # 做空条件 向下突破2倍标准差
        long_close = close[-1] < mean  # 平多条件 回落均值以下
        short_close = close[-1] > mean  # 平空条件 回升均值以上
        if (long_positions.iloc[target_idx] > 0) and long_close:  # 多出场
            order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=1, order_type=2)
        if (short_positions.iloc[target_idx] > 0) and short_close:  # 空出场
            order_target_volume(account_idx=0, target_idx=target_idx, target_volume=0, side=2, order_type=2)
        if (long_positions.iloc[target_idx] == 0) and condi_long:  # 多进场
            order_target_value(account_idx=0, target_idx=target_idx, target_value=context.initial / context.Tlen,
                               side=1, order_type=2)
        if (short_positions.iloc[target_idx] == 0) and condi_short:  # 空进场
            order_target_value(account_idx=0, target_idx=target_idx, target_value=context.initial / context.Tlen,
                               side=2, order_type=2)


if __name__ == '__main__':
    target = ['shfe.rb0000', 'shfe.ru0000']
    run_backtest('aberration', 'AberrationNew.py', target_list=target, frequency='min', fre_num=5,
                 begin_date='2016-01-01',
                 end_date='2018-06-01', fq=1)
