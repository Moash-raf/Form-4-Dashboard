import os
import json
import pandas as pd
import streamlit as st
from datetime import datetime, date

DATA_DIR = "data"

# --- Load all daily filing JSON files ---
all_filings = []
for filename in os.listdir(DATA_DIR):
    if filename.startswith("daily_filings_") and filename.endswith(".json"):
        file_path = os.path.join(DATA_DIR, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure it's a list of filings
                if isinstance(data, list):
                    # Extract date from filename
                    date_str = filename.replace("daily_filings_", "").replace(".json", "")
                    for filing in data:
                        filing["file_date"] = date_str
                    all_filings.extend(data)
        except Exception as e:
            st.warning(f"Failed to read {filename}: {e}")

if not all_filings:
    st.error("No filings found in data folder.")
    st.stop()

# --- Convert to DataFrame ---
df = pd.DataFrame(all_filings)

# --- Parse timestamp properly ---
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df["Date"] = df["timestamp"].dt.date  # for easy filtering

# === CONFIG ===
TODAY = date.today().strftime("%Y_%m_%d")
DAILY_FILINGS_PATH = os.path.join(DATA_DIR, f"daily_filings_{TODAY}.json")

st.set_page_config(page_title="Form 4 Dashboard", layout="wide")

st.title("SEC Form 4 Dashboard")
st.caption("Monitor insider transactions parsed from the SEC daily filings feed.\nUpdated hourly from 6 AM to 11 PM")


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

# === DATE RANGE FILTER ===
min_date = df["Timestamp"].min().date()
max_date = df["Timestamp"].max().date()

selected_dates = st.sidebar.date_input(
    "Filter by Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

filtered_df = df.copy()
if len(selected_dates) == 2:
    start_date, end_date = selected_dates
    filtered_df = filtered_df[
        (filtered_df["Timestamp"].dt.date >= start_date) &
        (filtered_df["Timestamp"].dt.date <= end_date)
    ]



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
