# Crypto AI Lab — Streamlit Web App

## What it does
- Live public market candles
- Candlestick chart
- EMA20 / EMA50
- RSI
- ATR
- Recent support/resistance
- Volume condition
- Paper wallet
- Simulated long/short positions
- Trade history and P/L

## Run locally
1. Install Python 3.11+.
2. Open a terminal in this folder.
3. `pip install -r requirements.txt`
4. `streamlit run app.py`

## Deploy
Upload `app.py` and `requirements.txt` to a GitHub repository, then create a Streamlit Community Cloud app from that repository.
No exchange API key is required for the public candle data used by this first version.

This application is an educational simulator and does not place real orders.
