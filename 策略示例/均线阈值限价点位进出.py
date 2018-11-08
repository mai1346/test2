# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     均线阈值限价点位进出
   Description :
   Author :       haoyuan.m
   date：          2018/10/24
-------------------------------------------------
   Change Activity:
                   2018/10/24:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'
#  TODO 净值下降到0
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
    reg_kdata('min', 60)
    context.Tlen = len(context.target_list)  # 标的个数
    context.TT = np.zeros(context.Tlen)
    context.N = 20  # 窗口长度
    context.P = 10
    context.Q = 0.03
    context.init = 10000000


def on_data(context):
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=context.N + 30, fill_up=True, df=True)  # 获取所有标的数据
    if data['close'].isna().any():
        return
    mktvalue = context.account().cash['total_value'].iloc[0]
    datalist = [data[data['target_idx'] == x] for x in pd.unique(data.target_idx)]
    long_positions = context.account().positions['volume_long']
    short_positions = context.account().positions['volume_short']
    for target in datalist:
        target_idx = target.target_idx.iloc[0]
        close = target.close
        MA10 = talib.MA(target.close, 10).values
        MA5 = talib.MA(target.close, 5).values
        Spread = MA5 - MA10
        buyprice = np.floor(MA10[-1]) + 20
        sellprice = np.floor(MA10[-1]) - 20
        condi_long = (close.iloc[-1] > (MA10[-1] + context.P)) and (close.iloc[-2] < (MA10[-1] + context.P)) and \
                     (not (close.iloc[-1] > MA10[-1] * (1 + context.Q)))  # 开多条件
        condi_short = (close.iloc[-1] < (MA10[-1] - context.P)) and (close.iloc[-2] > (MA10[-1] - context.P)) and \
                      (not (close.iloc[-1] < MA10[-1] * (1 - context.Q)))  # 开空条件
        if (long_positions.iloc[target_idx] == 0) and condi_long:
            order_target_value(account_idx=0, target_idx=target_idx, target_value=10000000 / context.Tlen, side=1,
                               order_type=1, price=buyprice)
        if (short_positions.iloc[target_idx] == 0) and condi_short:
            order_target_value(account_idx=0, target_idx=target_idx, target_value=10000000 / context.Tlen, side=2,
                               order_type=1, price=sellprice)
        elif long_positions.iloc[target_idx] > 0:
            if (close.iloc[-1] > MA5[-1]) and (context.TT[target_idx] == 0):
                context.TT[target_idx] = 1  # 多单止盈标签
            if (close.iloc[-1] < (MA10[-1] - context.P)) and (close.iloc[-2] > MA10[-1] - context.P):
                order_target_value(account_idx=0, target_idx=target_idx, target_value=0, side=1, order_type=2)
                order_target_value(account_idx=0, target_idx=target_idx, target_value=10000000 / context.Tlen, side=2,
                                   order_type=1, price=sellprice)
            if ((context.TT[target_idx] == 1) and (close.iloc[-1] < MA5[-1]) and (Spread[-1] > 15)) or \
                    (close.iloc[-1] > MA10[-1] * (1 + context.Q)) or (close.iloc[-1] < (MA10[-1] - context.P)):
                order_target_value(account_idx=0, target_idx=target_idx, target_value=0, side=1, order_type=2)
                context.TT[target_idx] = 0
        elif short_positions.iloc[target_idx] > 0:
            if (close.iloc[-1] < MA5[-1]) and (context.TT[target_idx] == 0):
                context.TT[target_idx] = -1  # 多单止盈标签
            if (close.iloc[-1] > (MA10[-1] + context.P)) and (close.iloc[-2] < MA10[-1] + context.P):
                order_target_value(account_idx=0, target_idx=target_idx, target_value=0, side=2, order_type=2)
                order_target_value(account_idx=0, target_idx=target_idx, target_value=10000000 / context.Tlen, side=1,
                                   order_type=1, price=buyprice)
            if ((context.TT[target_idx] == -1) and (close.iloc[-1] > MA5[-1]) and (Spread[-1] < -15)) or \
                    (close.iloc[-1] < MA10[-1] * (1 - context.Q)) or (close.iloc[-1] > (MA10[-1] + context.P)):
                order_target_value(account_idx=0, target_idx=target_idx, target_value=0, side=2, order_type=2)
                context.TT[target_idx] = 0
        if mktvalue < 0:
            print('haha')

    currentbar=get_current_bar()
    print(currentbar)
    cash=context.account(0).cash
    print(cash)
    if cash['valid_cash'][0] <= 0:
        orders=get_order_info()
        print(orders)
    a=0


if __name__ == '__main__':
    target = ['shfe.rb0000']
    run_backtest('均线阈值限价点位进出', '均线阈值限价点位进出.py', target_list=target, frequency='min', fre_num=60,
                 begin_date='2016-01-01',
                 end_date='2018-06-30', fq=1)


