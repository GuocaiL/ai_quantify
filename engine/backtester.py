import backtrader as bt
from datetime import datetime

class BacktestEngine:
    def __init__(self, cash=50000, commission=0.0005):
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(cash)
        self.cerebro.broker.setcommission(commission=commission)

    def add_data(self, df, fromdate, todate):
        """添加回测数据
        
        Args:
            df (pd.DataFrame): 包含股票数据的DataFrame
            fromdate (datetime): 回测开始日期
            todate (datetime): 回测结束日期
            
        Returns:
            self: 返回实例本身以支持链式调用
        """
        data = bt.feeds.PandasData(dataname=df, fromdate=fromdate, todate=todate)
        self.cerebro.adddata(data)
        return self

    def add_strategy(self, strategy, **params):
        self.cerebro.addstrategy(strategy, **params)
        return self

    def add_analyzers(self):
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.0)
        self.cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        self.cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
        return self

    def run(self):
        return self.cerebro.run()

    def plot_results(self):
        self.cerebro.plot(style='candle', barup='green', bardown='red')
