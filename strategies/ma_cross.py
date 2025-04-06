
# -*- coding: utf-8 -*-

# 导入必要的库
from datetime import datetime  # 日期时间处理库
import akshare as ak  # 财经数据接口库

import numpy as np  # 数值计算库
import pandas as pd  # 数据分析库
import tushare as ts  # 股票数据接口库
import backtrader as bt  # 量化回测框架


import matplotlib.pyplot as plt  # 绘图库

# 设置matplotlib显示中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # Mac系统
# 或者使用以下Windows系统常用字体
# plt.rcParams['font.sans-serif'] = ['SimHei']  # Windows系统
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


# 定义MA_Cross策略类，继承自backtrader的Strategy类
class MA_Cross(bt.Strategy):
    # 定义策略参数
    params = (
        ('pfast', 5),  # 快速均线周期
        ('pslow', 10),  # 慢速均线周期
        ('slope_period', 3),  # 斜率计算周期
        ('lookback_period', 63),  # 回溯63天
        ('percentile_days', 63),   # 63*25%≈16天
        ('stop_loss_pct', 0.10),  # 新增：10%止损比例
        ('trail_stop_pct', 0.05)   # 新增：5%移动止盈
    )

    def get_trades(self):
        """获取交易记录"""
        return getattr(self, 'trades', [])

    def log(self, txt, dt=None):
        """日志记录函数"""
        dt = dt or self.datas[0].datetime.date(0)  # 获取当前日期
        print("%s, %s" % (dt.isoformat(), txt))  # 打印日期和日志内容

    def __init__(self):
        """策略初始化函数"""
        # 保存收盘价和成交量引用
        self.dataclose = self.datas[0].close
        self.volume = self.datas[0].volume
        
        # 订单相关变量初始化
        # self.order = None  # 当前订单
        self.buyprice = None  # 买入价格
        # self.buycomm = None  # 买入佣金
        
        # 计算均线指标
        # 将sma1和sma2保存为实例变量
        self.sma1 = bt.ind.SMA(period=self.p.pfast)  # 快速均线
        self.sma2 = bt.ind.SMA(period=self.p.pslow)  # 慢速均线
        
        # 计算均线斜率和交叉信号
        self.sma1_diff = self.sma1 - self.sma1(-self.p.slope_period)  # sma1均线斜率
        self.sma2_diff = self.sma2 - self.sma2(-self.p.slope_period)  # sma2均线斜率
        self.crossover = bt.ind.CrossOver(self.sma1, self.sma2)  # 均线交叉信号
        
        # 使用简单的列表来跟踪历史价格
        self.history_close = []
        

    def next(self):
        """每个bar调用的主逻辑函数"""

        # 添加当前收盘价到历史数据
        self.history_close.append(self.dataclose[0])
        
        # 保持历史数据长度不超过lookback_period
        if len(self.history_close) > self.p.lookback_period:
            self.history_close.pop(0)  # 移除最早的数据

        # 检查数据是否足够
        if len(self.history_close) < self.p.lookback_period:
            return  # 数据不足时直接返回

        # 计算有多少天价格低于当前开盘价
        lower_days = sum(1 for price in self.history_close if price < self.datas[0].open[0])

        # 判断是否符合购买条件
        is_low_percentile = lower_days <= self.p.percentile_days

        # 没有持仓时的买入逻辑
        if self.position.size == 0:
            if (
                self.crossover > 0  # 金叉条件
                # and self.sma1_diff[0] > 0.05
                # and  self.sma2_diff[0] > 0
                # and is_low_percentile
                # and 5日均线开始上升的时候就买
                # self.sma1[0] > self.sma1[-1] and self.sma2[0] > self.sma2[-1] # 买早
                # self.sma1[0] > self.sma1[-1] and self.sma1[0] > self.sma1[-2] and self.sma2[0] > self.sma2[-1]# 买正好
                ):
                
                self.log("BUY CREATE, %.2f" % self.dataclose[0])
                self.log("低于过去%d天中%d天的价格" % (self.p.lookback_period, lower_days))
                # 计算买入数量（使用95%的现金）
                self.size = np.floor(0.95 * self.broker.cash / self.dataclose[0])
                self.buy(size=self.size)  # 执行买入
        # 已持有时的卖出逻辑
        elif self.position.size > 0:
            if self.crossover < 0:  # 死叉条件
            # if self.sma1[0] < self.sma1[-1]:  # 5日均线下降的时候卖出
                self.log("SELL CREATE, %.2f" % self.dataclose[0])
                self.sell(size=self.position.size)  # 卖出全部持仓


    def notify_order(self, order):
        """订单状态变化回调函数"""
        # 忽略已提交和已接受的中间状态
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        # 订单完成处理
        if order.status in [order.Completed]:
            if order.isbuy():  # 买入订单
                self.log(
                    "BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                    % (order.executed.price, order.executed.value, order.executed.comm)
                )
                # 记录买入价格和佣金
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                # self.bar_executed_close = self.dataclose[0]
            else:  # 卖出订单
                self.log(
                    "SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f, 总资产 %.2f, 盈利 %.4f%%"
                    % (
                        order.executed.price, 
                        order.executed.value, 
                        order.executed.comm, 
                        self.broker.getvalue(), 
                        (self.broker.getvalue() - self.broker.startingcash)/self.broker.startingcash * 100
                         )
                )
            # 记录订单执行时的K线位置    
            # self.bar_executed = len(self)

        # 订单取消/保证金不足/被拒绝处理
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        # 重置订单引用
        self.order = None
