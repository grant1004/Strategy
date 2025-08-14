import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 讀取數據
with open('日線/6257.json', 'r') as f:
    data = json.load(f)

df = pd.DataFrame(data['data'])
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)
df.sort_index(inplace=True)


# 計算RSI
def compute_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


df['RSI'] = compute_rsi(df['close'], 20)

# 計算布林帶
df['SMA20'] = df['close'].rolling(window=7).mean()
df['STD20'] = df['close'].rolling(window=7).std()
df['UpperBand'] = df['SMA20'] + (df['STD20'] * 2)
df['LowerBand'] = df['SMA20'] - (df['STD20'] * 2)


# 計算斐波那契回撤水平
def fibonacci_levels(df):
    high = df['close'].rolling(window=14).max()
    low = df['close'].rolling(window=14).min()
    diff = high - low
    levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
    for level in levels:
        df[f'Fib_{level}'] = high - (diff * level)
    return df


df = fibonacci_levels(df)


# 生成交易信號（包含止損機制）
def generate_signals(df, stop_loss_pct=0.2):
    df['Signal'] = 0  # 0 表示無信號，1 表示買入信號，-1 表示賣出信號
    df['Position'] = 0  # 0 表示未持倉，1 表示持倉中
    df['Stop_Loss'] = 0  # 用於標記止損賣出

    in_position = False
    entry_price = 0
    for i in range(1, len(df)):
        # 買入條件：RSI < 40 且價格接近或突破下軌，且當前未持倉
        if df['RSI'].iloc[i] < 35 and df['close'].iloc[i] <= df['LowerBand'].iloc[i] * 1.05 and not in_position:
            df['Signal'].iloc[i] = 1
            in_position = True
            entry_price = df['close'].iloc[i]
            # 賣出條件：價格突破0.618斐波那契回撤水平，或觸發止損，或價格觸及布林帶上軌且RSI > 70
        elif (df['close'].iloc[i] > df['Fib_0.5'].iloc[i] and df['close'].iloc[i - 1] <= df['Fib_0.618'].iloc[
            i - 1] and in_position) or \
             (in_position and df['close'].iloc[i] <= entry_price * (1 - stop_loss_pct)) or \
             (in_position and df['close'].iloc[i] >= df['UpperBand'].iloc[i] and df['RSI'].iloc[i] > 70):
            df['Signal'].iloc[i] = -1
            if df['close'].iloc[i] <= entry_price * (1 - stop_loss_pct):
                df['Stop_Loss'].iloc[i] = 1  # 標記為止損賣出
            in_position = False
            entry_price = 0

        df['Position'].iloc[i] = 1 if in_position else 0

    return df


df = generate_signals(df, stop_loss_pct=0.2)  # 設置5%的止損


# 計算策略回報
def calculate_returns(df):
    df['Returns'] = df['close'].pct_change()
    df['Strategy_Returns'] = 0.0

    entry_price = 0
    for i in range(1, len(df)):
        if df['Signal'].iloc[i] == 1:  # 買入
            entry_price = df['close'].iloc[i]
        elif df['Signal'].iloc[i] == -1 and entry_price > 0:  # 賣出
            returns = (df['close'].iloc[i] - entry_price) / entry_price
            df['Strategy_Returns'].iloc[i] = returns
            entry_price = 0

    df['Cumulative_Strategy_Returns'] = (1 + df['Strategy_Returns']).cumprod()
    df['Cumulative_Market_Returns'] = (1 + df['Returns']).cumprod()

    return df


df = calculate_returns(df)


# 修改繪圖函數以顯示所有斐波那契水平
def plot_trading_signals(df):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(20, 15), sharex=True)

    # 價格和信號圖
    ax1.plot(df.index, df['close'], label='Close Price', color='blue')

    # 繪製所有斐波那契水平
    fib_levels = [0, 0.236, 0.382, 0.5]
    fib_colors = ['red', 'orange', 'yellow', 'green']
    for level, color in zip(fib_levels, fib_colors):
        ax1.plot(df.index, df[f'Fib_{level}'], label=f'Fib {level}', color=color, linestyle='--', alpha=0.7)

    ax1.fill_between(df.index, df['LowerBand'], df['UpperBand'], alpha=0.1, color='gray')
    ax1.plot(df.index, df['UpperBand'], label='Upper Band', color='gray', linestyle=':')
    ax1.plot(df.index, df['LowerBand'], label='Lower Band', color='gray', linestyle=':')

    # 買入和賣出信號
    buy_signals = df[df['Signal'] == 1]
    sell_signals = df[(df['Signal'] == -1) & (df['Stop_Loss'] == 0)]
    stop_loss_signals = df[(df['Signal'] == -1) & (df['Stop_Loss'] == 1)]

    ax1.scatter(buy_signals.index, buy_signals['close'], color='green', marker='^', s=100, label='Buy Signal')
    ax1.scatter(sell_signals.index, sell_signals['close'], color='red', marker='v', s=100, label='Sell Signal')
    ax1.scatter(stop_loss_signals.index, stop_loss_signals['close'], color='purple', marker='v', s=100,
                label='Stop Loss')

    # 持倉狀態
    ax1.fill_between(df.index, 0, df['close'], where=df['Position'] == 1, color='yellow', alpha=0.3,
                     label='Holding Position')

    # 標註持倉開始和結束時間
    for i in range(1, len(df)):
        if df['Signal'].iloc[i] == 1:  # 買入信號
            date_str = df.index[i].strftime('%m/%d')
            ax1.axvline(x=df.index[i], color='green', linestyle='--', alpha=0.7)
            ax1.text(df.index[i], df['close'].min(), f'Buy\n{date_str}', color='green',
                     rotation=90, verticalalignment='bottom', horizontalalignment='right')
        elif df['Signal'].iloc[i] == -1:  # 賣出信號
            date_str = df.index[i].strftime('%m/%d')
            color = 'purple' if df['Stop_Loss'].iloc[i] == 1 else 'red'
            label = 'Stop\nLoss' if df['Stop_Loss'].iloc[i] == 1 else 'Sell'
            ax1.axvline(x=df.index[i], color=color, linestyle='--', alpha=0.7)
            ax1.text(df.index[i], df['close'].min(), f'{label}\n{date_str}', color=color,
                     rotation=90, verticalalignment='bottom', horizontalalignment='right')

    ax1.set_title('Trading Signals with Price, Fibonacci Levels, and Bollinger Bands')
    ax1.legend(loc='upper left', bbox_to_anchor=(1, 1))
    ax1.grid(True, alpha=0.3)

    # 設置 x 軸日期格式
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # RSI 圖
    ax2.plot(df.index, df['RSI'], label='RSI', color='orange')
    ax2.axhline(y=30, color='green', linestyle='--')
    ax2.axhline(y=70, color='red', linestyle='--')
    ax2.fill_between(df.index, 30, 70, alpha=0.1, color='gray')
    ax2.set_title('RSI Indicator')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 回報比較圖
    ax3.plot(df.index, df['Cumulative_Strategy_Returns'], label='Strategy Returns', color='green')
    ax3.plot(df.index, df['Cumulative_Market_Returns'], label='Market Returns', color='blue')
    ax3.set_title('Cumulative Returns Comparison')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("trading_signals_chart.png", dpi=300, bbox_inches='tight')
    plt.show()


# 執行繪圖
plot_trading_signals(df)

# 打印策略績效
print(f"策略累積回報: {df['Cumulative_Strategy_Returns'].iloc[-1]}")
print(f"買入持有累積回報: {df['Cumulative_Market_Returns'].iloc[-1]}")