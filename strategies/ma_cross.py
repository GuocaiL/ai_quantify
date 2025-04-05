from datetime import datetime
import akshare as ak

import numpy as np
import pandas as pd
import tushare as ts
import backtrader as bt

# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # Mac系统
# 或者使用以下Windows系统常用字体
# plt.rcParams['font.sans-serif'] = ['SimHei']  # Windows系统
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


class MA_Cross(bt.Strategy):
    params = (
        ('pfast', 5),
        ('pslow', 10),
        ('slope_period', 3),
        ('lookback_period', 63),  # 回溯63天
        ('percentile_days', 63),   # 63*25%≈16天
        ('stop_loss_pct', 0.10),  # 新增：10%止损比例
        ('trail_stop_pct', 0.05)   # 新增：5%移动止盈
    )

    def get_trades(self):
        """获取交易记录"""
        return getattr(self, 'trades', [])

    def log(self, txt, dt=None):
        """Logging function fot this strategy"""
        dt = dt or self.datas[0].datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.volume = self.datas[0].volume
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # 将sma1和sma2保存为实例变量
        self.sma1 = bt.ind.SMA(period=self.p.pfast)
        self.sma2 = bt.ind.SMA(period=self.p.pslow)
        
        self.sma_diff = self.sma1 - self.sma1(-self.p.slope_period)
        self.crossover = bt.ind.CrossOver(self.sma1, self.sma2)

        # 使用简单的列表来跟踪历史价格
        self.history_close = []

        # 添加回撤跟踪变量
        self.peak_value = 0
        self.drawdown = 0
        self.max_drawdown = 0
        self.drawdown_start_date = None
        self.drawdown_end_date = None
        self.drawdown_history = []  # 存储所有回撤记录

        self.trades = []  # 确保在__init__中初始化trades列表

    def next(self):
        # 更新峰值和回撤
        current_value = self.broker.getvalue()
        if current_value > self.peak_value:
            self.peak_value = current_value
            if self.drawdown != 0:  # 回撤结束
                self.drawdown_end_date = self.datas[0].datetime.date(0)
                self.record_drawdown()
            self.drawdown = 0
        else:
            self.drawdown = (self.peak_value - current_value) / self.peak_value * 100
            if self.drawdown > self.max_drawdown:
                self.max_drawdown = self.drawdown
                if self.drawdown_start_date is None:
                    self.drawdown_start_date = self.datas[0].datetime.date(0)

        # 持仓时的止损检查
        if self.position.size > 0:
            # 固定比例止损
            current_price = self.dataclose[0]
            stop_loss_price = self.buyprice * (1 - self.p.stop_loss_pct)
            
            # 移动止盈
            if hasattr(self, 'highest_price'):
                if current_price > self.highest_price:
                    self.highest_price = current_price
            else:
                self.highest_price = current_price
                
            trail_stop_price = self.highest_price * (1 - self.p.trail_stop_pct)

            # 触发止损或移动止盈
            if current_price <= stop_loss_price or current_price <= trail_stop_price:
                self.log(f"触发止跌机制 买入价:{self.buyprice:.2f} 当前价:{current_price:.2f}")
                self.sell(size=self.position.size)
                return  # 止损后直接返回，不再执行后续逻辑


        # 添加当前收盘价到历史数据
        self.history_close.append(self.dataclose[0])
        
        # 保持历史数据长度不超过lookback_period
        if len(self.history_close) > self.p.lookback_period:
            self.history_close.pop(0)

        # 检查数据是否足够
        if len(self.history_close) < self.p.lookback_period:
            return

        # 计算有多少天价格低于当前开盘价
        lower_days = sum(1 for price in self.history_close if price < self.datas[0].open[0])

        # self.log("lower_days, %.2f" % lower_days)
        # self.log(lower_days/self.p.lookback_period)
        
        # 判断是否符合购买条件
        is_low_percentile = lower_days <= self.p.percentile_days

        if self.position.size == 0:
            if (self.crossover > 0 
                # and  self.sma_diff[0] > 0.05 
                # and
                # is_low_percentile
                ):
                
                self.log("BUY CREATE, %.2f" % self.dataclose[0])
                self.log("低于过去%d天中%d天的价格" % (self.p.lookback_period, lower_days))
                self.size = np.floor(0.95 * self.broker.cash / self.dataclose[0])
                self.buy(size=self.size)
        # 已持有
        elif self.position.size > 0:
            if self.crossover < 0:  # 死叉
                self.log("SELL CREATE, %.2f" % self.dataclose[0])
                self.sell(size=self.position.size)

        # 在买卖执行时记录标记
        if self.position.size > 0 and not hasattr(self, 'buy_marker'):
            self.buy_marker = {
                'dt': self.datas[0].datetime.date(0),
                'price': self.dataclose[0],
                'size': self.position.size
            }
        elif self.position.size == 0 and hasattr(self, 'buy_marker'):
            self.sell_marker = {
                'dt': self.datas[0].datetime.date(0),
                'price': self.dataclose[0],
                'size': self.position.size
            }
            del self.buy_marker

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    "BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                    % (order.executed.price, order.executed.value, order.executed.comm)
                )

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                self.bar_executed_close = self.dataclose[0]
            else:
                self.log(
                    "SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                    % (order.executed.price, order.executed.value, order.executed.comm)
                )
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
            
        pnl_pct = trade.pnl / trade.price * 100
        self.trades.append({  # 确保使用self.trades而不是创建新变量
            'ref': trade.ref,
            'dt': self.datas[0].datetime.date(0),
            'price': trade.price,
            'size': trade.size,
            'pnl': trade.pnl,
            'pnl_pct': pnl_pct
        })

    def record_drawdown(self):
        """记录完成的回撤"""
        if self.drawdown_start_date and self.drawdown_end_date:
            duration = (self.drawdown_end_date - self.drawdown_start_date).days
            self.drawdown_history.append({
                'drawdown': self.drawdown,
                'start_date': self.drawdown_start_date,
                'end_date': self.drawdown_end_date,
                'duration': duration
            })
        self.drawdown_start_date = None
        self.drawdown = 0

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        
        # 计算收益率百分比
        pnl_pct = trade.pnl / trade.price * 100
        self.log(f"交易结果: {trade.status_names[trade.status]}, 盈亏: {trade.pnl:.2f}, 收益率: {pnl_pct:.2f}%")
        
        # 记录交易信息用于绘图
        if not hasattr(self, 'trades'):
            self.trades = []
        self.trades.append({
            'ref': trade.ref,
            'dt': self.datas[0].datetime.date(0),
            'price': trade.price,
            'size': trade.size,
            'pnl': trade.pnl,
            'pnl_pct': pnl_pct,
            'status': trade.status_names[trade.status]
        })

def get_data(code, start="20240801", end="20240930"):
    # df = ts.get_k_data(code, autype="qfq", start=start, end=end)
    df = ak.stock_zh_a_hist(
        symbol=code, 
        period="daily", 
        start_date=start, 
        end_date=end, 
        adjust="")
    #df = ts.pro_bar(ts_code=code, adj='qfq', start_date=start, end_date=end)
    # 列名映射
    df = df.rename(columns={
        '开盘': 'open',
        '最高': 'high',
        '最低': 'low',
        '收盘': 'close',
        '成交量': 'volume',
        '日期': 'date'
    })
    df.index = pd.to_datetime(df.date)
    df["openinterest"] = 0
    df = df[["open", "high", "low", "close", "volume", "openinterest"]]
    return df



if __name__ == "__main__":

    start = datetime(2024, 1, 1)
    end = datetime(2025, 4, 4)
    # 000333
    # 002031
    # 600203
    dataframe = get_data("002031", start=start.strftime('%Y%m%d'), end=end.strftime('%Y%m%d'))
    data = bt.feeds.PandasData(dataname=dataframe, fromdate=start, todate=end)

    cerebro = bt.Cerebro()

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.0)
    cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    
    cerebro.addstrategy(MA_Cross)

    cerebro.adddata(data)

    cerebro.broker.setcash(50000)

    cerebro.broker.setcommission(commission=0.0005)

    print("Starting Portfolio Value: %.2f" % cerebro.broker.getvalue())

    class TradePlotter(bt.observers.DrawDown):
        def _plotlabel(self):
            labels = super()._plotlabel()
            # 修改这里：使用self._owner而不是self.strategy
            if hasattr(self._owner, 'trades'):
                for trade in self._owner.trades:
                    labels.append(f"交易#{trade['ref']}: {trade['pnl_pct']:.2f}%")
            return labels
    
    cerebro.addobserver(TradePlotter)
    
    # 运行回测
    results = cerebro.run()

    print("Final Portfolio Value: %.2f" % cerebro.broker.getvalue())

    strat = results[0]

    # 打印分析结果
    print('最终资产价值: %.2f' % cerebro.broker.getvalue())
    print('累计收益率: %.2f%%' % (strat.analyzers.returns.get_analysis()['rtot']*100))
    print('年化收益率: %.2f%%' % (strat.analyzers.returns.get_analysis()['rnorm100']))
    print('夏普比率: %.2f' % strat.analyzers.sharpe.get_analysis()['sharperatio'])
    # print('最大回撤: %.2f%%' % strat.analyzers.drawdown.get_analysis()['max']['drawdown'])
    # print('最长回撤周期: %d' % strat.analyzers.drawdown.get_analysis()['max']['len'])
    
    # 交易统计
    trade_analysis = strat.analyzers.trades.get_analysis()
    print('总交易次数: %d' % trade_analysis.total.closed)
    print('胜率: %.2f%%' % (trade_analysis.won.total/trade_analysis.total.closed*100))
    print('平均收益率: %.2f%%' % trade_analysis.pnl.net.average)
    print('SQN指数: %.2f' % strat.analyzers.sqn.get_analysis()['sqn'])

    # 打印自定义回撤信息
    print('\n=== 自定义回撤分析 ===')
    print(f'最大回撤: {strat.max_drawdown:.2f}%')
    
    if strat.drawdown_history:
        print('\n详细回撤记录:')
        for i, dd in enumerate(sorted(strat.drawdown_history, key=lambda x: x['drawdown'], reverse=True)):
            print(f'回撤{i+1}: {dd["drawdown"]:.2f}%')
            print(f'开始日期: {dd["start_date"]}')
            print(f'结束日期: {dd["end_date"]}')
            print(f'持续时间: {dd["duration"]}天\n')
    else:
        print('没有记录到明显的回撤周期')

    # 修改绘图部分
    cerebro.plot(style='candle', 
                barup='green', 
                bardown='red',
                plotdist=0.1, 
                volume=False, 
                subtxtsize=8,
                figtitle='均线交叉策略回测结果')  # 添加中文标题
    
    # 或者使用以下方式单独设置图形属性
    fig = cerebro.plot(style='candle', barup='green', bardown='red')[0][0]
    fig.suptitle('均线交叉策略回测结果', fontproperties='SimHei')  # 显式设置字体