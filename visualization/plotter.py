import matplotlib.pyplot as plt

class TradeVisualizer:
    def __init__(self):
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

    def plot_trades(self, trades):
        dates = [trade['dt'] for trade in trades]
        prices = [trade['price'] for trade in trades]
        plt.figure(figsize=(12, 6))
        plt.plot(dates, prices, 'o-', label='交易价格')
        plt.title('交易记录')
        plt.legend()
        plt.show()

    def plot_drawdown(self, drawdown_history):
        if not drawdown_history:
            return
        dates = [dd['start_date'] for dd in drawdown_history]
        drawdowns = [dd['drawdown'] for dd in drawdown_history]
        plt.figure(figsize=(12, 6))
        plt.bar(dates, drawdowns, color='red', alpha=0.5)
        plt.title('回撤记录')
        plt.show()
