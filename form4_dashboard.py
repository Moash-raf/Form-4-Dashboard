import streamlit as st
import pandas as pd
import json
import os
from datetime import date

# === CONFIG ===
BASE_PATH = "data"
TODAY = date.today().strftime("%Y_%m_%d")
DAILY_FILINGS_PATH = os.path.join(BASE_PATH, f"daily_filings_{TODAY}.json")

st.set_page_config(page_title="Form 4 Dashboard", layout="wide")

st.title("SEC Form 4 Dashboard")
st.caption("Monitor insider transactions parsed from the SEC daily filings feed.\nUpdated hourly from 6 AM to 11 PM")

# === LOAD DATA ===
if not os.path.exists(DAILY_FILINGS_PATH):
    st.warning("No daily filings found for today.")
    st.stop()

with open(DAILY_FILINGS_PATH, "r", encoding="utf-8") as f:
    filings = json.load(f)

if not filings:
    st.warning("No filings available.")
    st.stop()

df = pd.DataFrame(filings)

# === CREATE BUY/SELL COLUMN ===
df["Buy/Sell"] = df["is_purchased"].apply(lambda x: "Buy" if x else "Sell")

# === REORDER COLUMNS ===
columns_order = [
    "issuer", "symbol", "owner", "shares", "price", "Buy/Sell",
    "timestamp", "title", "transaction_code", "source_url"
]
df = df[columns_order]

rename_map = {
    "issuer": "Issuer",
    "symbol": "Symbol",
    "owner": "Owner",
    "shares": "Shares",
    "price": "Price",
    "Buy/Sell": "Buy/Sell",
    "timestamp": "Timestamp",
    "title": "Title",
    "transaction_code": "Transaction Code",
    "source_url": "URL"
}

# After renaming columns
df = df.rename(columns=rename_map)

# --- Round/format for display ---
df["Shares"] = df["Shares"].apply(lambda x: f"{x:,.2f}")
df["Price"] = df["Price"].apply(lambda x: f"{x:,.2f}")



# === SIDEBAR FILTERS ===
st.sidebar.header("Filters")
symbol_filter = st.sidebar.multiselect("Ticker Symbol", sorted(df["Symbol"].dropna().unique()))
owner_filter = st.sidebar.text_input("Owner name contains...")
buy_sell_filter = st.sidebar.selectbox("Transaction type", ["All", "Buy", "Sell"])

filtered_df = df.copy()

if symbol_filter:
    filtered_df = filtered_df[filtered_df["Symbol"].isin(symbol_filter)]
if owner_filter:
    filtered_df = filtered_df[filtered_df["Owner"].str.contains(owner_filter, case=False, na=False)]
if buy_sell_filter != "All":
    filtered_df = filtered_df[filtered_df["Buy/Sell"] == buy_sell_filter]

# === STYLING FUNCTION: highlight only Buy/Sell column ===
def highlight_buy_sell(col):
    if col.name == "Buy/Sell":
        return ['background-color: #0A8500; color: white' if v=="Buy" 
                else 'background-color: #CF0C0C; color: white' for v in col]
    else:
        return ['']*len(col)

# === DISPLAY DATAFRAME ===
st.dataframe(
    filtered_df.style.apply(highlight_buy_sell, axis=0),
    width='stretch',
    height=600
)

st.caption(f"Showing {len(filtered_df)} filings out of {len(df)} total.")
