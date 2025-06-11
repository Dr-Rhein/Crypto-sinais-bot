import os
import time
import threading
import ccxt
import pandas as pd
import requests
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
BYBIT_SECRET = os.getenv('BYBIT_SECRET')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

SYMBOLS = ['BTC/USDT', 'ETH/USDT']
TIMEFRAMES = ['5m', '15m']
INTERVALO_CHECAGEM = 60

exchange = ccxt.bybit({
    'apiKey': BYBIT_API_KEY,
    'secret': BYBIT_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

def fetch_data(symbol, timeframe, limit=100):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return df

def calculate_indicators(df):
    df['ema9'] = EMAIndicator(close=df['close'], window=9).ema_indicator()
    df['ema21'] = EMAIndicator(close=df['close'], window=21).ema_indicator()
    df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
    atr = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14)
    df['atr'] = atr.average_true_range()
    df['volume_ma'] = df['volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma']
    return df

def generate_signal(df):
    current = df.iloc[-1]
    buy_cond = current['ema9'] > current['ema21'] and current['rsi'] > 35 and current['volume_ratio'] > 1.2
    sell_cond = current['ema9'] < current['ema21'] and current['rsi'] < 65 and current['volume_ratio'] > 1.2
    if buy_cond:
        return "🟢 COMPRA", current['close'], current['atr'] * 1.5, current['atr'] * 3
    elif sell_cond:
        return "🔴 VENDA", current['close'], current['atr'] * 1.5, current['atr'] * 3
    return None, None, None, None

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Erro Telegram: {response.text}")
    except Exception as e:
        print(f"Erro ao enviar alerta: {e}")

def sinal_loop():
    print("✅ Bot iniciado")
    while True:
        try:
            for symbol in SYMBOLS:
                for timeframe in TIMEFRAMES:
                    df = fetch_data(symbol, timeframe)
                    df = calculate_indicators(df)
                    signal, entry, sl, tp = generate_signal(df)
                    if signal:
                        sl_price = entry - sl if "COMPRA" in signal else entry + sl
                        tp_price = entry + tp if "COMPRA" in signal else entry - tp
                        msg = (f"📊 *SINAL CONFIRMADO* ({timeframe})
"
                               f"*Par:* {symbol}
*Tipo:* {signal}
"
                               f"*Entrada:* {entry:.2f}
"
                               f"*Stop Loss:* {sl_price:.2f}
"
                               f"*Take Profit:* {tp_price:.2f}")
                        send_telegram_alert(msg)
        except Exception as e:
            print(f"Erro: {e}")
        time.sleep(INTERVALO_CHECAGEM)

def iniciar_bot_em_thread():
    thread = threading.Thread(target=sinal_loop)
    thread.daemon = True
    thread.start()
