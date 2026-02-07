import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.sheets_connector import fetch_raw_daily, fetch_raw_agent_daily
from utils.data_processor import get_weekly_data, get_weekly_agent_data, get_agent_rankings
from config.settings import METRIC_COLORS, ENGAGEMENT_TYPES

st.set_page_config(page_title="Weekly Report", page_icon="📊", layout="wide")

st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 15px;
        border-radius: 12px;
        border-left: 4px solid #4F8BF9;
    }
</style>
""", unsafe_allow_html=True)

st.title("Weekly Report")

with st.spinner("Loading..."):
    df_daily = fetch_raw_daily()
    df_agent_daily = fetch_raw_agent_daily()

if df_daily.empty:
    st.error("No data available.")
    st.stop()

weekly = get_weekly_data(df_daily)
weekly_agents = get_weekly_agent_data(df_agent_daily)

if weekly.empty:
    st.warning("Not enough data for weekly reports.")
    st.stop()

# --- Week Selector ---
week_options = weekly["Week_Label"].tolist()
selected_week_label = st.sidebar.selectbox("Select Week", week_options, index=len(week_options) - 1)
selected_row = weekly[weekly["Week_Label"] == selected_week_label].iloc[0]
sel_year = int(selected_row["Year"])
sel_week = int(selected_row["Week"])

is_complete = bool(selected_row["Is_Complete"])
days_count = int(selected_row["Days"])
week_range = selected_row["Week_Range"]

st.markdown(f"### {selected_week_label}")
st.caption(f"{week_range}")
if not is_complete:
    st.warning(f"This week is incomplete ({days_count}/7 days). Averages are based on {days_count} day{'s' if days_count != 1 else ''}.")

# --- KPIs ---
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Engagement", f"{int(selected_row['Total']):,}")
c2.metric("Comments", f"{int(selected_row['Comments']):,}")
c3.metric("Reactions", f"{int(selected_row['Reactions']):,}")
c4.metric("Shares", f"{int(selected_row['Shares']):,}")
c5.metric("Days in Week", f"{days_count}/7" if not is_complete else "7")

# --- Daily Averages ---
st.divider()
st.markdown(f"### Daily Averages (based on {days_count} day{'s' if days_count != 1 else ''})")
a1, a2, a3, a4 = st.columns(4)
a1.metric("Avg Total/Day", f"{int(selected_row['Avg_Total']):,}")
a2.metric("Avg Comments/Day", f"{int(selected_row['Avg_Comments']):,}")
a3.metric("Avg Reactions/Day", f"{int(selected_row['Avg_Reactions']):,}")
a4.metric("Avg Shares/Day", f"{int(selected_row['Avg_Shares']):,}")

# --- WoW Comparison ---
idx = weekly[weekly["Week_Label"] == selected_week_label].index[0]
if idx > 0:
    prev_row = weekly.iloc[idx - 1]
    st.divider()
    st.markdown("### Week-over-Week Change")
    wc1, wc2, wc3, wc4 = st.columns(4)
    for col_obj, metric in zip([wc1, wc2, wc3, wc4], ENGAGEMENT_TYPES + ["Total"]):
        curr = int(selected_row[metric])
        prev = int(prev_row[metric])
        delta = curr - prev
        pct = round(delta / prev * 100, 1) if prev > 0 else 0
        col_obj.metric(metric, f"{curr:,}", delta=f"{delta:+,} ({pct:+.1f}%)")

st.divider()

# --- Daily Breakdown within Week ---
st.markdown("### Daily Breakdown")
week_days = df_daily[
    (df_daily["Date"].dt.isocalendar().week.astype(int) == sel_week) &
    (df_daily["Date"].dt.isocalendar().year.astype(int) == sel_year)
].sort_values("Date")

if not week_days.empty:
    col_chart, col_table = st.columns([2, 1])
    with col_chart:
        fig = go.Figure()
        for metric in ENGAGEMENT_TYPES:
            fig.add_trace(go.Bar(
                x=week_days["Date"].dt.strftime("%a %b %d"),
                y=week_days[metric],
                name=metric,
                marker_color=METRIC_COLORS[metric],
            ))
        fig.update_traces(texttemplate="%{value:,}", textposition="inside")
        fig.update_layout(
            barmode="stack",
            template="plotly_dark",
            height=350,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            uniformtext_minsize=8, uniformtext_mode="hide",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        display = week_days[["Date", "Comments", "Reactions", "Shares", "Total"]].copy()
        display["Date"] = display["Date"].dt.strftime("%a %b %d")
        best_day = display.loc[display["Total"].idxmax()]
        st.dataframe(display.reset_index(drop=True), use_container_width=True, height=300)
        st.success(f"Best day: **{best_day['Date']}** ({int(best_day['Total']):,} total)")

# --- Agent Rankings for the Week ---
st.divider()
st.markdown("### Agent Rankings (This Week)")
if not week_days.empty:
    start = week_days["Date"].min()
    end = week_days["Date"].max()
    rankings = get_agent_rankings(df_agent_daily, start, end)
    if not rankings.empty:
        col_rank, col_bar = st.columns([1, 1])
        with col_rank:
            disp = rankings[["Agent", "Total", "Comments", "Reactions", "Shares", "% Contribution"]].copy()
            disp["% Contribution"] = disp["% Contribution"].apply(lambda x: f"{x}%")
            for c in ["Total", "Comments", "Reactions", "Shares"]:
                disp[c] = disp[c].apply(lambda x: f"{x:,}")
            st.dataframe(disp, use_container_width=True, height=350)

        with col_bar:
            fig_bar = px.bar(
                rankings.reset_index(), x="Agent", y=ENGAGEMENT_TYPES,
                barmode="stack", color_discrete_map=METRIC_COLORS,
            )
            fig_bar.update_traces(texttemplate="%{value:,}", textposition="inside")
            fig_bar.update_layout(
                template="plotly_dark", height=350,
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                xaxis_title="", yaxis_title="Engagement",
                uniformtext_minsize=8, uniformtext_mode="hide",
            )
            st.plotly_chart(fig_bar, use_container_width=True)
