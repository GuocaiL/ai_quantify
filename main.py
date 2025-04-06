from datetime import datetime
from data.fetcher import StockDataFetcher
from strategies.ma_cross import MA_Cross
from engine.backtester import BacktestEngine
from visualization.plotter import TradeVisualizer
import argparse

def main():

    # 创建参数解析器
    parser = argparse.ArgumentParser(description='量化交易系统')
    parser.add_argument('--mode', type=str, required=True, choices=['backtest', 'trade'],
                       help='运行模式: backtest(回测) 或 trade(实盘)')
    parser.add_argument('--ticker', type=str, required=True,
                       help='股票代码', default='000001')
    parser.add_argument('--initial_capital', type=float, required=False,
                       help='初始资金', default=10000)
    parser.add_argument('--commission', type=float, required=False,
                       help='手续费', default=0.0005)
    parser.add_argument('--start_date', type=str, required=False,
                       help='开始日期', default='20240101')
    parser.add_argument('--end_date', type=str, required=False,
                       help='结束日期', default='20250401')
    
    args = parser.parse_args()

    # 根据模式执行不同操作
    if args.mode == 'backtest':
        fetcher = StockDataFetcher(args.ticker)
        df = fetcher.get_historical_data(
            start_date=args.start_date,
            end_date=args.end_date
        )

        engine = BacktestEngine(cash=float(args.initial_capital), commission=float(args.commission))
        engine.add_data(df)
        engine.add_strategy(MA_Cross)
        engine.add_analyzers()
        
        results = engine.run()
        strat = results[0]
        
        print("最终资产价值: %.2f" % engine.cerebro.broker.getvalue())
        print('累计收益率: %.2f%%' % (strat.analyzers.returns.get_analysis()['rtot']*100))
        print('夏普比率:', strat.analyzers.sharpe.get_analysis()['sharperatio']) 
        
        # 提取最大回撤数据
        max_drawdown = strat.analyzers.drawdown.get_analysis()
        print(f"最大回撤幅度: {max_drawdown.max.drawdown:.2f}%")  # 百分比形式
        print(f"最大回撤持续时间: {max_drawdown.max.len} 天")     # 持续周期
        print(f"最大亏损金额: {max_drawdown.max.moneydown}")     # 绝对金额[[9]]

        # 提取交易统计数据
        trade_analyzer = strat.analyzers.trades.get_analysis()  # 关键：获取TradeAnalyzer数据
        def analyze_trades(analyzer):
            won = analyzer.won.total
            lost = analyzer.lost.total
            total = won + lost
            win_rate = won / total if total > 0 else 0
            
            avg_profit = analyzer.won.pnl.average
            avg_loss = abs(analyzer.lost.pnl.average)
            profit_ratio = avg_profit / avg_loss if avg_loss != 0 else 0
            
            print(f"总交易次数: {total}")
            print(f"胜率: {win_rate:.2%}")
            print(f"平均盈利: {avg_profit:.2f}, 平均亏损: {avg_loss:.2f}")
            print(f"盈亏比: {profit_ratio:.2f}")

        analyze_trades(trade_analyzer)  # 执行分析
        
        visualizer = TradeVisualizer()
        # visualizer.plot_trades(strat.trades)
        # visualizer.plot_drawdown(strat.drawdown_history)
        
        engine.plot_results()
    elif args.mode == 'trade':
        print("实盘交易模式尚未实现")

if __name__ == "__main__":
    main()
