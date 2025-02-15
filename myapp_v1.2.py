import streamlit as st
import pandas as pd
import numpy as np
import os

# Load dataset
data_path = "Merged_FO_Delivery_Data.csv"
df = pd.read_csv(data_path, parse_dates=['Trade Date'])

# Streamlit UI
st.title("📊 Interactive Data Filter App")
st.sidebar.header("🔍 Filters")

# Ensure 'Trade Date' is in datetime format
df['Trade Date'] = pd.to_datetime(df['Trade Date'], errors='coerce')
df = df.dropna(subset=['Trade Date'])  # Remove invalid dates

latest_date = df['Trade Date'].max()
yesterday = latest_date - pd.Timedelta(days=1)
last_week = latest_date - pd.Timedelta(weeks=1)
last_month = latest_date - pd.Timedelta(days=30)

# Date Filter Options
date_filter_option = st.sidebar.radio(
    "📅 Select Date Filter",
    ["Latest Date", "Yesterday", "Last 1 Week", "Last 1 Month", "Custom Date Range"]
)

if date_filter_option == "Latest Date":
    date_range = [latest_date, latest_date]
elif date_filter_option == "Yesterday":
    date_range = [yesterday, latest_date]
elif date_filter_option == "Last 1 Week":
    date_range = [last_week, latest_date]
elif date_filter_option == "Last 1 Month":
    date_range = [last_month, latest_date]
else:
    min_date, max_date = df['Trade Date'].min(), df['Trade Date'].max()
    date_range = st.sidebar.date_input(
        "Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date
    )

# **1️⃣ Default Columns for Display**
default_columns = [
    "Trade Date", "Ticker Symbol", "Cum-OI", "Roll Over %", "OI Change %", "CUMOI CE", "CUMOI PE",
    "Close", "VWAP", "Volume", "AVO", "CHG%", "Change% 22D", "TTQ%5", "DQAVG%5", "ACTION%5",
    "Volume_AVG22", "DELIV_QTY_AVG22", "ACTION_AVG22", "TTQ%22", "DQAVG%22", "ACTION%22"
]

# Ensure only available columns are selected
available_columns = [col for col in default_columns if col in df.columns]

# **2️⃣ Allow Additional Column Selection**
display_columns = st.sidebar.multiselect(
    "Select Additional Columns to Display", 
    df.columns.tolist(), 
    default=available_columns
)

# **3️⃣ Filter by Ticker Symbol**
symbols = df['Ticker Symbol'].dropna().unique().tolist()
select_all = st.sidebar.checkbox("Select All Symbols", value=True)

if select_all:
    selected_tickers = symbols  # Select all if checkbox is checked
else:
    selected_tickers = st.sidebar.multiselect("Select Symbols", symbols, default=symbols[:5])

# **4️⃣ Numeric Column Filters (Preselected Filters)**
numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
default_numeric_filters = ["CHG%", "Change OI", "Change in OI PE AVO"]  # Preselected columns
available_numeric_filters = [col for col in default_numeric_filters if col in numeric_columns]

selected_numeric_columns = st.sidebar.multiselect(
    "Select Numeric Columns to Apply Filters", 
    numeric_columns, 
    default=available_numeric_filters
)

filters = {}  # Store filter ranges
for col in selected_numeric_columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')
    df[col] = df[col].replace([np.inf, -np.inf], np.nan)

    # Default to positive values (>0) for preselected columns
    default_value_filter = "Only Positive (>0)" if col in available_numeric_filters else "All"
    
    value_filter = st.sidebar.radio(
        f"Filter {col} by Value Type",
        ["All", "Only Positive (>0)", "Only Negative (<0)"],
        index=["All", "Only Positive (>0)", "Only Negative (<0)"].index(default_value_filter),
        key=f"value_filter_{col}"
    )

    # Apply value-based filtering
    if value_filter == "Only Positive (>0)":
        df = df[df[col] > 0]
    elif value_filter == "Only Negative (<0)":
        df = df[df[col] < 0]

    # Min-max range selection
    min_val, max_val = df[col].dropna().min(), df[col].dropna().max()
    if np.isfinite(min_val) and np.isfinite(max_val):  # Ensure valid values
        filters[col] = st.sidebar.slider(
            f"Select Range for {col}", 
            float(min_val), float(max_val), (float(min_val), float(max_val)), key=f"slider_{col}"
        )

# **5️⃣ Apply Filters to Data**
filtered_df = df[df['Ticker Symbol'].isin(selected_tickers)]  # Apply symbol filter

if 'Trade Date' in df.columns:
    filtered_df = filtered_df[(filtered_df['Trade Date'] >= pd.to_datetime(date_range[0])) & 
                              (filtered_df['Trade Date'] <= pd.to_datetime(date_range[1]))]

for col, (min_val, max_val) in filters.items():
    filtered_df = filtered_df[(filtered_df[col] >= min_val) & (filtered_df[col] <= max_val)]

# **6️⃣ Make Ticker Symbols Clickable (Redirects to TradingView)**
def make_tradingview_link(ticker):
    return f"[{ticker}](https://www.tradingview.com/chart/?symbol=NSE:{ticker})"

filtered_df['Ticker Symbol'] = filtered_df['Ticker Symbol'].apply(make_tradingview_link)

# **7️⃣ Pagination using a Slider**
num_rows = len(filtered_df)
rows_per_page = 10  # Adjust the number of rows displayed per page

if num_rows > rows_per_page:
    page_number = st.slider("📜 Scroll Through Data", 1, (num_rows // rows_per_page) + 1, 1)
    start_row = (page_number - 1) * rows_per_page
    end_row = start_row + rows_per_page
    filtered_df_paginated = filtered_df.iloc[start_row:end_row]
else:
    filtered_df_paginated = filtered_df  # Show all rows if below threshold

# **8️⃣ Display Filtered Data with Clickable Links**
st.markdown(filtered_df_paginated[display_columns].to_markdown(index=False), unsafe_allow_html=True)

# **9️⃣ Download Button**
csv = filtered_df[display_columns].to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Filtered Data", csv, "filtered_data.csv", "text/csv")

# **🔟 Exit Button**
if st.button("🚪 Exit App"):
    st.sidebar.write("Closing the app...")
    os._exit(0)  # Forcefully exit the app