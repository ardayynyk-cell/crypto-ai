import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Crypto AI Lab", page_icon="🧠", layout="wide")

API = "https://api.binance.com/api/v3/klines"

# ---------- data ----------
@st.cache_data(ttl=20)
def get_klines(symbol, interval, limit):
    r = requests.get(API, params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=15)
    r.raise_for_status()
    d = r.json()
    cols = ["time","open","high","low","close","volume","close_time","quote_volume",
            "trades","taker_base","taker_quote","ignore"]
    df = pd.DataFrame(d, columns=cols)
    for c in ["open","high","low","close","volume","taker_base","taker_quote"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    return df

def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()

def rsi(s, n=14):
    d = s.diff()
    up = d.clip(lower=0)
    down = -d.clip(upper=0)
    au = up.ewm(alpha=1/n, adjust=False).mean()
    ad = down.ewm(alpha=1/n, adjust=False).mean()
    rs = au / ad.replace(0, np.nan)
    return 100 - (100/(1+rs))

def atr(df, n=14):
    prev = df["close"].shift(1)
    tr = pd.concat([
        df["high"]-df["low"],
        (df["high"]-prev).abs(),
        (df["low"]-prev).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()

def analyze(df):
    x = df.copy()
    x["ema20"] = ema(x.close,20)
    x["ema50"] = ema(x.close,50)
    x["rsi"] = rsi(x.close)
    x["atr"] = atr(x)
    last = x.iloc[-1]
    support = x.tail(50)["low"].min()
    resistance = x.tail(50)["high"].max()
    if last.close > last.ema20 > last.ema50:
        trend = "Bullish"
    elif last.close < last.ema20 < last.ema50:
        trend = "Bearish"
    else:
        trend = "Mixed"
    avgvol = x.tail(20).volume.mean()
    vol_state = "High" if last.volume > avgvol*1.4 else ("Low" if last.volume < avgvol*.7 else "Normal")
    r = float(last.rsi)
    rstate = "Overbought" if r >= 70 else ("Oversold" if r <= 30 else "Neutral")
    return x, {
        "price": float(last.close), "ema20": float(last.ema20), "ema50": float(last.ema50),
        "rsi": r, "atr": float(last.atr), "atr_pct": float(last.atr/last.close*100),
        "support": float(support), "resistance": float(resistance),
        "trend": trend, "volume": vol_state, "rstate": rstate
    }

# ---------- state ----------
if "balance" not in st.session_state: st.session_state.balance = 10000.0
if "position" not in st.session_state: st.session_state.position = None
if "history" not in st.session_state: st.session_state.history = []

st.title("🧠 Crypto AI Lab")
st.caption("Market analysis + educational paper trading. No real orders are placed.")

with st.sidebar:
    st.header("Market")
    symbol = st.selectbox("Symbol", ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","ADAUSDT","DOGEUSDT"])
    interval = st.selectbox("Timeframe", ["5m","15m","1h","4h","1d"], index=1)
    limit = st.selectbox("Candles", [150,300,500], index=1)
    refresh = st.button("🔄 Refresh data", use_container_width=True)
    st.divider()
    st.header("Paper wallet")
    starting = st.number_input("Reset balance", min_value=100.0, value=10000.0, step=100.0)
    size_pct = st.slider("Position size %", 1, 100, 10)
    if st.button("Reset simulator", use_container_width=True):
        st.session_state.balance = float(starting)
        st.session_state.position = None
        st.session_state.history = []
        st.rerun()

try:
    df = get_klines(symbol, interval, int(limit))
    df, a = analyze(df)
except Exception as e:
    st.error("Market data could not be loaded. Check your internet connection or try again.")
    st.stop()

# ---------- chart ----------
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df.time, open=df.open, high=df.high, low=df.low, close=df.close,
    name="Price"
))
fig.add_trace(go.Scatter(x=df.time, y=df.ema20, name="EMA 20", line=dict(width=1.5)))
fig.add_trace(go.Scatter(x=df.time, y=df.ema50, name="EMA 50", line=dict(width=1.5)))
fig.add_hline(y=a["support"], line_dash="dot", annotation_text="Support")
fig.add_hline(y=a["resistance"], line_dash="dot", annotation_text="Resistance")
fig.update_layout(height=560, xaxis_rangeslider_visible=False, margin=dict(l=10,r=10,t=20,b=10))
st.plotly_chart(fig, use_container_width=True)

# ---------- metrics ----------
m1,m2,m3,m4,m5 = st.columns(5)
m1.metric("Price", f"{a['price']:,.4f}")
m2.metric("Trend", a["trend"])
m3.metric("RSI", f"{a['rsi']:.1f}")
m4.metric("ATR", f"{a['atr_pct']:.2f}%")
m5.metric("Volume", a["volume"])

left,right = st.columns([1.2,1])

with left:
    st.subheader("🧠 Market analysis")
    if a["trend"] == "Bullish":
        st.success("The current EMA structure is bullish.")
    elif a["trend"] == "Bearish":
        st.warning("The current EMA structure is bearish.")
    else:
        st.info("The current EMA structure is mixed.")
    st.write(f"**RSI:** {a['rsi']:.1f} — {a['rstate']}")
    st.write(f"**Support:** `{a['support']:,.4f}`")
    st.write(f"**Resistance:** `{a['resistance']:,.4f}`")
    st.write(f"**EMA20:** `{a['ema20']:,.4f}`")
    st.write(f"**EMA50:** `{a['ema50']:,.4f}`")
    st.write(f"**ATR:** `{a['atr']:,.4f}` ({a['atr_pct']:.2f}% of price)")
    st.info("These are indicator observations, not guaranteed predictions. The app does not infer a guaranteed entry, target, leverage or profit.")

with right:
    st.subheader("💰 Paper trading")
    st.write(f"**Virtual balance:** ${st.session_state.balance:,.2f}")
    p = st.session_state.position
    if p:
        current = a["price"]
        pnl = (current-p["entry"])*p["qty"] if p["side"]=="LONG" else (p["entry"]-current)*p["qty"]
        st.write(f"Open: **{p['side']}** · Entry `{p['entry']:,.4f}` · Qty `{p['qty']:.6f}`")
        st.metric("Unrealized P/L", f"${pnl:,.2f}")
        if st.button("Close position", use_container_width=True):
            st.session_state.balance += pnl
            st.session_state.history.insert(0,{
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Side": p["side"], "Entry": p["entry"], "Exit": current,
                "P/L": pnl, "Reason":"Manual close"
            })
            st.session_state.position = None
            st.rerun()
    else:
        st.caption("No open paper position.")
        notional = st.session_state.balance * size_pct/100
        qty = notional/a["price"]
        c1,c2 = st.columns(2)
        if c1.button("Simulate LONG", use_container_width=True):
            st.session_state.position={"side":"LONG","entry":a["price"],"qty":qty}
            st.rerun()
        if c2.button("Simulate SHORT", use_container_width=True):
            st.session_state.position={"side":"SHORT","entry":a["price"],"qty":qty}
            st.rerun()

st.subheader("📋 Paper trade history")
if st.session_state.history:
    h = pd.DataFrame(st.session_state.history)
    st.dataframe(h, use_container_width=True, hide_index=True)
    closed = h["P/L"].sum()
    st.write(f"Closed P/L: **${closed:,.2f}**")
else:
    st.info("No paper trades yet.")

st.divider()
st.caption("Educational simulator. No connection to a trading account and no real orders are sent.")
