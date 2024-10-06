import talib as ta
import pandas as pd
from binance.client import Client
from datetime import datetime, timedelta
import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Binance API 설정 (자신의 API 키와 시크릿 키를 넣어야 합니다)
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')

line_url = os.getenv('LINE_URL')
line_token = os.getenv('LINE_TOKEN')

def line_message(msg):
    print(msg)
    requests.post(line_url, headers={'Authorization': 'Bearer ' + line_token}, data={'message': msg})

client = Client(api_key, api_secret)

# 12시간 봉 데이터를 가져오고 조건을 확인하는 함수
def check_market_conditions(symbol):
    # 12시간 봉 데이터 가져오기 (Binance 제공)
    klines = client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_12HOUR)

    # 데이터프레임으로 변환
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms') + timedelta(hours=9)  # UTC를 한국 시간으로 변환
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)

    # RSI 계산
    df['rsi'] = ta.RSI(df['close'], timeperiod=14)

    # Stochastic RSI 계산
    rsi = df['rsi']
    rsi_l = rsi.rolling(window=14).min()
    rsi_h = rsi.rolling(window=14).max()
    df['stochrsi'] = (rsi - rsi_l) / (rsi_h - rsi_l) * 100

    # Stochastic RSI K 계산 (3봉 이동평균)
    df['stochrsi_k'] = df['stochrsi'].rolling(window=3).mean()

    # 120개의 12시간 봉에 대한 이동평균 거래량 계산
    df['vol_120'] = df['volume'].rolling(window=120).mean()

    # Volume Explosive 조건
    df['vol_explosive'] = df['volume'] > df['vol_120'] * 3

    # b_low, r_low, t_low 조건 확인
    df['b_low'] = (df['rsi'] < 25) & (df['stochrsi_k'] < 5) & df['vol_explosive']
    df['r_low'] = df['rsi'] < 15
    df['t_low'] = (df['rsi'] < 20) & (df['stochrsi_k'] < 1)

    # 결과 반환
    return df[['timestamp', 'close', 'rsi', 'stochrsi_k', 'vol_120', 'vol_explosive', 'b_low', 'r_low', 't_low']]

# Streamlit 앱 설정
st.title('Bitcoin & XRP Futures 12-Hour Chart Analysis')

# 데이터를 확인할 시간대
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
st.write(f"현재 시간: {current_time}")

# 비트코인과 XRP 데이터를 각각 가져오기
btc_df = check_market_conditions('BTCUSDT_PERP')
xrp_df = check_market_conditions('XRPUSDT_PERP')

# 비트코인 데이터 출력
st.header('Bitcoin (BTCUSDT) 12-Hour Chart Analysis')
st.write("최근 비트코인 12시간 봉 데이터:")
st.dataframe(btc_df.tail())

st.write("비트코인 조건에 부합하는 경우:")
if btc_df['b_low'].iloc[-1]:
    st.success("비트코인 b_low 조건 충족: RSI < 25, Stochastic RSI K < 5, Volume Explosive!")
else:
    st.warning("비트코인 b_low 조건 충족 안함.")

if btc_df['r_low'].iloc[-1]:
    st.success("비트코인 r_low 조건 충족: RSI < 15!")
else:
    st.warning("비트코인 r_low 조건 충족 안함.")

if btc_df['t_low'].iloc[-1]:
    st.success("비트코인 t_low 조건 충족: RSI < 20, Stochastic RSI K < 1!")
else:
    st.warning("비트코인 t_low 조건 충족 안함.")

# XRP 데이터 출력
st.header('XRP (XRPUSDT) 12-Hour Chart Analysis')
st.write("최근 XRP 12시간 봉 데이터:")
st.dataframe(xrp_df.tail())

st.write("XRP 조건에 부합하는 경우:")
if xrp_df['b_low'].iloc[-1]:
    st.success("XRP b_low 조건 충족: RSI < 25, Stochastic RSI K < 5, Volume Explosive!")
else:
    st.warning("XRP b_low 조건 충족 안함.")

if xrp_df['r_low'].iloc[-1]:
    st.success("XRP r_low 조건 충족: RSI < 15!")
else:
    st.warning("XRP r_low 조건 충족 안함.")

if xrp_df['t_low'].iloc[-1]:
    st.success("XRP t_low 조건 충족: RSI < 20, Stochastic RSI K < 1!")
else:
    st.warning("XRP t_low 조건 충족 안함.")