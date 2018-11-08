# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     Donchain
   Description :
   Author :       haoyuan.m
   date：          2018/10/25
-------------------------------------------------
   Change Activity:
                   2018/10/25:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'
# TODO 未开空仓 未平仓
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
    reg_kdata('min', 60)
    reg_kdata('day', 1)
    context.Tlen = len(context.target_list)
    context.LenM = 20
    context.LenD = 20
    context.entryP = np.zeros(context.Tlen) * np.nan
    context.ATRratio = 1
    context.initial = 10000000


def on_data(context):
    dataM = get_reg_kdata(reg_idx=context.reg_kdata[0], length=context.LenM + 1, fill_up=True, df=True)
    dataD = get_reg_kdata(reg_idx=context.reg_kdata[1], length=context.LenD + 1, fill_up=True, df=True)
    if dataM['close'].isna().any() or dataD['close'].isna().any():
        return
    long_positions = context.account().positions['volume_long']
    short_positions = context.account().positions['volume_short']
    dataMlist = [dataM[dataM['target_idx'] == x] for x in pd.unique(dataM.target_idx)]
    dataDlist = [dataD[dataD['target_idx'] == x] for x in pd.unique(dataD.target_idx)]
    for i in range(len(dataMlist)):
        targetM = dataMlist[i]
        targetD = dataDlist[i]
        closeM = targetM.close.values.astype('float')
        openM = targetM.open.values.astype('float')
        highM = targetM.high.values.astype('float')
        lowM = targetM.low.values.astype('float')
        closeD = targetD.close.values.astype('float')
        highD = targetD.high.values.astype('float')
        lowD = targetD.low.values.astype('float')

        if long_positions[i] == 0 and short_positions[i] == 0:
            context.entryP[i] = np.nan
        elif np.isnan(context.entryP[i]):
            context.entryP[i] = openM[-1]
        atr = talib.ATR(highD, lowD, closeD, timeperiod=context.LenD)
        if long_positions[i] > 0:
            if closeM[-1] < context.entryP[i] - context.ATRratio * atr[-2]:
                order_target_volume(account_idx=0, target_idx=i, target_volume=0, side=1, order_type=2)
            elif closeM[-1] > context.entryP[i] + 2 * context.ATRratio * atr[-2]:
                context.entryP[i] = openM[-1]
        if short_positions[i] > 0:
            if closeM[-1] > context.entryP[i] + context.ATRratio * atr[-2]:
                order_target_volume(account_idx=0, target_idx=i, target_volume=0, side=2, order_type=2)
            elif closeM[-1] < context.entryP[i] - 2 * context.ATRratio * atr[-2]:
                context.entryP[i] = openM[-1]
        if (long_positions[i] == 0) and (short_positions[i] == 0):
            if closeM[-1] > highM[-context.LenD:-1].max():  # 做多 最新价大于过去一段时间最高价
                order_target_value(account_idx=0, target_idx=i, target_value=context.initial / context.Tlen, side=1,
                                   order_type=2)
            if closeM[-1] < lowM[-context.LenD:-1].min():  # 做空 最新价小于过去一段时间最低价
                order_target_value(account_idx=0, target_idx=i, target_value=context.initial / context.Tlen, side=2,
                                   order_type=2)


if __name__ == '__main__':
    target = ['dce.jm0000', 'shfe.rb0000']
    run_backtest('Donchain', 'Donchain.py', target_list=target, frequency='min', fre_num=60, begin_date='2016-01-01',
                 end_date='2018-06-01', fq=1)
