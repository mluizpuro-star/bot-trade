import ccxt
import pandas as pd
import time
import datetime

exchange = ccxt.binance({'enableRateLimit': True})

symbol = 'BTC/USDT'
timeframe = '5m'

def indicadores(df):
    close = df['close']

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    ma = close.rolling(20).mean()

    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26

    return rsi, ma, macd

sinal = None
tempo_entrada = None
modo_ativo = False

while True:
    try:
        agora = datetime.datetime.now()
        minuto = agora.minute
        segundo = agora.second

        if minuto % 5 != 3 and not modo_ativo:
            time.sleep(10)
            continue

        candles = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        df = pd.DataFrame(candles, columns=['time','open','high','low','close','volume'])

        rsi, ma, macd = indicadores(df)
        last = df.iloc[-1]

        if minuto % 5 == 3 and sinal is None:
            modo_ativo = True

            score_buy = 0
            score_sell = 0

            if rsi.iloc[-1] < 35:
                score_buy += 1
            if last['close'] > ma.iloc[-1]:
                score_buy += 1
            if macd.iloc[-1] > 0:
                score_buy += 1

            if rsi.iloc[-1] > 65:
                score_sell += 1
            if last['close'] < ma.iloc[-1]:
                score_sell += 1
            if macd.iloc[-1] < 0:
                score_sell += 1

            print("\n====================")
            print(f"⏰ {agora.strftime('%H:%M:%S')}")
            print(f"💰 Preço: {last['close']}")
            print(f"📊 RSI: {rsi.iloc[-1]:.2f}")

            if score_buy >= 2:
                sinal = "COMPRA"
                tempo_entrada = (minuto + 2) % 60
                print("🟢 PREPARAR COMPRA")

            elif score_sell >= 2:
                sinal = "VENDA"
                tempo_entrada = (minuto + 2) % 60
                print("🔴 PREPARAR VENDA")

            else:
                print("⚪ SEM SINAL")
                modo_ativo = False

        if modo_ativo and sinal is not None:
            segundos_restantes = (tempo_entrada * 60) - (minuto * 60 + segundo)

            if segundos_restantes > 0:
                print(f"⏳ {segundos_restantes}s para {sinal}")

            if segundos_restantes <= 0:
                print(f"🚀 ENTRAR AGORA ({sinal})")
                sinal = None
                tempo_entrada = None
                modo_ativo = False

        time.sleep(1)

    except Exception as e:
        print("Erro:", e)
        time.sleep(5)
