#!/usr/bin/python
#coding:utf-8

"""
@author: Miaohua.L
@contact: miaohua.l@bitpower.com.cn
@file: multifactors.py
@time: 2018/9/5 14:13
"""

from atrader import *
import numpy as np
import pandas as pd

import statsmodels.api as sm

try:
    import statsmodels.tsa.stattools as ts
except:
    print('请安装statsmodels库')
    sys.exit(-1)

'''
本策略根据EG两步法(1.序列同阶单整2.OLS残差平稳)判断序列具有协整关系后(若无协整关系则全平仓位不进行操作)
通过计算两个价格序列回归残差的均值和标准差并用均值加减0.9倍标准差得到上下轨
在价差突破上轨的时候做空价差;在价差突破下轨的时候做多价差
若有仓位,在残差回归至上下轨内的时候平仓
回测数据为:rb1801和rb1805的1min数据
回测时间为:2017-09-25 08:00:00到2017-10-01 15:00:00
'''


# 协整检验的函数
def cointegration_test(series01, series02):
    target1 = ts.adfuller(np.array(series01), 1)[1]
    target2 = ts.adfuller(np.array(series02), 1)[1]
    # 同时平稳或不平稳则差分再次检验
    if (target1 > 0.1 and target2 > 0.1) or (target1 < 0.1 and target2 < 0.1):
        urt_diff_1 = ts.adfuller(np.diff(np.array(series01)), 1)[1]
        urt_diff_2 = ts.adfuller(np.diff(np.array(series02)), 1)[1]
        # 同时差分平稳进行OLS回归的残差平稳检验
        if urt_diff_1 < 0.1 and urt_diff_2 < 0.1:
            result = sm.OLS(np.array(series01.astype(float)), sm.add_constant(np.array(series02.astype(float))), missing='drop').fit()
            beta, c, resid = result.params[1], result.params[0], result.resid
            if ts.adfuller(np.array(resid), 1)[1] > 0.1:
                result = 0.0
            else:
                result = 1.0
            return beta, c, resid, result

        else:
            result = 0.0
            return 0.0, 0.0, 0.0, result

    else:
        result = 0.0
        return 0.0, 0.0, 0.0, result


def init(context):
    set_backtest(initial_cash=100000)
    # 订阅品种
    reg_kdata('min', 1)


def on_data(context):
    # 获取过去800个60s的收盘价数据
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=801, fill_up=True, df=True)
    if data['close'].isna().any():
        return
    close_01 = data[data['target_idx'] == 0]['close']
    close_02 = data[data['target_idx'] == 1]['close']

    # 展示两个价格序列的协整检验的结果
    beta, c, resid, result = cointegration_test(close_01, close_02)
    # 如果返回协整检验不通过的结果则全平仓位等待
    if not result:
        print(context.now, '协整检验不通过,全平所有仓位')
        order_close_all()
        return

    # 计算残差的标准差上下轨
    mean = np.mean(resid)
    up = mean + 1.5 * np.std(resid)
    down = mean - 1.5 * np.std(resid)
    # 计算新残差
    resid_new = close_01.iloc[-1] - beta * close_02.iloc[-1] - c
    # 获取rb1801的多空仓位
    positions = context.account().positions
    position_01_long = positions['volume_long'].iloc[0]
    position_01_short = positions['volume_short'].iloc[0]
    if not position_01_long and not position_01_short:
        # 上穿上轨时做空新残差
        if resid_new > up:
            order_target_volume(account_idx=0, target_idx=0, target_volume=1, side=2,
                               order_type=2, price=0)
            print(context.now, context.target_list[0] + '以市价单开空仓1手')
            order_target_volume(account_idx=0, target_idx=1, target_volume=1, side=1,
                               order_type=2, price=0)
            print(context.now, context.target_list[1] + '以市价单开多仓1手')
        # 下穿下轨时做多新残差
        if resid_new < down:
            order_target_volume(account_idx=0, target_idx=0, target_volume=1, side=1,
                               order_type=2, price=0)
            print(context.now, context.target_list[0], '以市价单开多仓1手')
            order_target_volume(account_idx=0, target_idx=1, target_volume=1, side=2,
                               order_type=2, price=0)
            print(context.now, context.target_list[1], '以市价单开空仓1手')
    # 新残差回归时平仓
    elif position_01_short:
        if resid_new <= up:
            order_close_all()
            print(context.now, '价格回归,平掉所有仓位')
        # 突破下轨反向开仓
        if resid_new < down:
            order_target_volume(account_idx=0, target_idx=0, target_volume=1, side=1,
                               order_type=2, price=0)
            print(context.now, context.target_list[0], '以市价单开多仓1手')
            order_target_volume(account_idx=0, target_idx=1, target_volume=1, side=2,
                               order_type=2, price=0)
            print(context.now, context.target_list[1], '以市价单开空仓1手')
    elif position_01_long:
        if resid_new >= down:
            order_close_all()
            print(context.now, '价格回归,平所有仓位')
        # 突破上轨反向开仓
        if resid_new > up:
            order_target_volume(account_idx=0, target_idx=0, target_volume=1, side=2,
                               order_type=2, price=0)
            print(context.now, context.target_list[0] + '以市价单开空仓1手')
            order_target_volume(account_idx=0, target_idx=1, target_volume=1, side=1,
                               order_type=2, price=0)
            print(context.now, context.target_list[1] + '以市价单开多仓1手')


if __name__ == '__main__':
    target = ['shfe.rb1801', 'shfe.rb1805']
    run_backtest('跨期套利', '跨期套利.py', target_list=target, frequency='min', fre_num=1, begin_date='2017-09-25',
                 end_date='2017-10-01', fq=1)