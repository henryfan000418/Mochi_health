import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt

# -------------------------- setup: Connect to Google Sheet


def connect_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)
    spreadsheet_id = "1LPLf3rzBCCkY8wudtFTaX7UziGoS7ABp3qheg4mbsmI"
    sheet = client.open_by_key(spreadsheet_id).sheet1
    return sheet

sheet = connect_sheet()

# -------------------------- UI: Mood Logging

st.set_page_config(page_title="Mood Logger", layout="centered")
st.title("📝 Mood Logger & Visualizer")

st.header("Log Your Mood")
mood = st.selectbox("How are you feeling today?", ["😊 Happy", "😠 Angry", "😕 Confused", "🎉 Excited"])
note = st.text_input("Optional note (e.g., 'busy morning', 'frustrating meeting')")

if st.button("Submit"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        sheet.append_row([timestamp, mood, note])
        st.success("✅ Mood logged successfully!")
    except Exception as e:
        st.error(f"❌ Error logging mood: {e}")

# -------------------------- Load data from Google Sheets

try:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Ensure all columns exist
    expected_cols = ['timestamp', 'mood', 'note']
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    # Convert timestamp safely
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    df = pd.DataFrame(columns=['timestamp', 'mood', 'note'])

# -------------------------- Mood Visualization with Matplotlib
st.header("📅 Mood Explorer")

try:
    # Load data from Google Sheets
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Ensure required columns exist
    for col in ['timestamp', 'mood', 'note']:
        if col not in df.columns:
            df[col] = ""

    # Convert timestamp to datetime and add 'date'
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.dropna(subset=['timestamp'])  # Remove rows with invalid timestamps
    df['date'] = df['timestamp'].dt.date

    if df.empty:
        st.info("No mood data available yet.")
    else:
        # 🎯 Date filter
        unique_dates = sorted(df['date'].dropna().unique())
        selected_date = st.date_input(
            "Select a date to view moods:",
            value=datetime.today().date(),
            min_value=min(unique_dates),
            max_value=max(unique_dates)
        )

        # 🎯 Mood filter
        unique_moods = sorted(df['mood'].dropna().unique())
        selected_moods = st.multiselect(
            "Select mood(s) to filter:",
            options=unique_moods,
            default=unique_moods
        )

        # Filtered daily data
        df_filtered = df[
            (df['date'] == selected_date) &
            (df['mood'].isin(selected_moods))
        ]

        # 🎨 Daily Mood Chart
        st.subheader(f"Mood Distribution on {selected_date}")
        if df_filtered.empty:
            st.warning("No mood data for selected date and mood(s).")
        else:
            mood_counts = df_filtered['mood'].value_counts()
            fig1, ax1 = plt.subplots()
            mood_counts.plot(kind='bar', ax=ax1, color='lightblue', edgecolor='black')
            ax1.set_title("Mood Count (Filtered)")
            ax1.set_xlabel("Mood")
            ax1.set_ylabel("Count")
            ax1.set_xticklabels(mood_counts.index, rotation=0)
            st.pyplot(fig1)

        # 📈 Mood Trend Chart
        st.subheader("Mood Trend Over Time (Filtered)")
        df_trend = df[df['mood'].isin(selected_moods)]
        grouped = df_trend.groupby(['date', 'mood']).size().unstack(fill_value=0)

        if grouped.empty:
            st.info("No mood data for trend chart.")
        else:
            fig2, ax2 = plt.subplots(figsize=(10, 5))
            grouped.plot(kind='bar', stacked=True, ax=ax2)
            ax2.set_title("Mood Count by Day")
            ax2.set_xlabel("Date")
            ax2.set_ylabel("Count")
            st.pyplot(fig2)

except Exception as e:
    st.error(f"❌ Failed to process mood data: {e}")

# -------------------------- Manual Refresh
st.markdown("---")
if st.button("🔄 Refresh Data"):
    st.experimental_rerun()