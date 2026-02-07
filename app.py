import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.sheets_connector import fetch_raw_daily, fetch_raw_agent_daily, fetch_agent_list, fetch_account_data
from utils.data_processor import get_daily_summary, get_agent_rankings, get_account_summary
from config.settings import METRIC_COLORS, ENGAGEMENT_TYPES

st.set_page_config(
    page_title="Booster Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #4F8BF9;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #FAFAFA;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #888;
        text-transform: uppercase;
    }
    .metric-delta-up { color: #00CC96; font-size: 0.9rem; }
    .metric-delta-down { color: #EF553B; font-size: 0.9rem; }
    .header-title {
        font-size: 2.2rem;
        font-weight: bold;
        background: linear-gradient(90deg, #4F8BF9, #00CC96);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 15px;
        border-radius: 12px;
        border-left: 4px solid #4F8BF9;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown('<p class="header-title">Booster Performance Dashboard</p>', unsafe_allow_html=True)
st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# --- Load Data ---
with st.spinner("Loading data from Google Sheets..."):
    df_daily = fetch_raw_daily()
    df_agent_daily = fetch_raw_agent_daily()
    agents = fetch_agent_list()
    df_accounts = fetch_account_data()

if df_daily.empty:
    st.error("No engagement data found. Check your Google Sheet connection.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filters")
min_date = df_daily["Date"].min().date()
max_date = df_daily["Date"].max().date()

col_s1, col_s2 = st.sidebar.columns(2)
start_date = col_s1.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
end_date = col_s2.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

agent_filter = st.sidebar.selectbox("Agent", ["All Agents"] + agents)

if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# --- KPI Section ---
filtered_daily, summary = get_daily_summary(df_daily, start_date, end_date)
rankings = get_agent_rankings(df_agent_daily, start_date, end_date)
acct_summary = get_account_summary(df_accounts)

st.markdown("### Key Metrics")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Engagement", f"{summary.get('total_engagement', 0):,}")
c2.metric("Comments", f"{summary.get('comments', 0):,}")
c3.metric("Reactions", f"{summary.get('reactions', 0):,}")
c4.metric("Shares", f"{summary.get('shares', 0):,}")
c5.metric("Daily Average", f"{summary.get('daily_avg', 0):,}")

st.divider()

# --- Account Health Quick Stat ---
if acct_summary:
    ac1, ac2, ac3, ac4 = st.columns(4)
    ac1.metric("Total Accounts", f"{acct_summary['total']:,}")
    ac2.metric("Active Accounts", f"{acct_summary['active']:,}")
    ac3.metric("Active Rate", f"{acct_summary['active_pct']}%")
    ac4.metric("Period Days", f"{summary.get('days', 0)}")
    st.divider()

# --- Charts Row ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("### Daily Engagement Trend")
    if not filtered_daily.empty:
        fig_trend = go.Figure()
        for metric in ENGAGEMENT_TYPES:
            fig_trend.add_trace(go.Scatter(
                x=filtered_daily["Date"],
                y=filtered_daily[metric],
                name=metric,
                mode="lines+markers",
                line=dict(color=METRIC_COLORS[metric], width=2),
                marker=dict(size=6),
            ))
        fig_trend.add_trace(go.Scatter(
            x=filtered_daily["Date"],
            y=filtered_daily["Total"],
            name="Total",
            mode="lines+markers",
            line=dict(color=METRIC_COLORS["Total"], width=3, dash="dash"),
            marker=dict(size=8),
        ))
        fig_trend.update_layout(
            template="plotly_dark",
            height=400,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            hovermode="x unified",
        )
        st.plotly_chart(fig_trend, use_container_width=True)

with col_right:
    st.markdown("### Engagement Mix")
    mix_data = {
        "Type": ENGAGEMENT_TYPES,
        "Value": [summary.get(k.lower(), 0) for k in ENGAGEMENT_TYPES],
    }
    fig_mix = px.donut = px.pie(
        mix_data, values="Value", names="Type",
        hole=0.5,
        color="Type",
        color_discrete_map=METRIC_COLORS,
    )
    fig_mix.update_layout(
        template="plotly_dark",
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )
    fig_mix.update_traces(textposition="inside", textinfo="value+percent+label")
    st.plotly_chart(fig_mix, use_container_width=True)

# --- Top Performers ---
st.markdown("### Agent Rankings")
if not rankings.empty:
    col_rank, col_bar = st.columns([1, 1])

    with col_rank:
        display_df = rankings[["Agent", "Total", "Comments", "Reactions", "Shares", "% Contribution", "Avg/Day"]].copy()
        display_df["% Contribution"] = display_df["% Contribution"].apply(lambda x: f"{x}%")
        display_df["Total"] = display_df["Total"].apply(lambda x: f"{x:,}")
        display_df["Comments"] = display_df["Comments"].apply(lambda x: f"{x:,}")
        display_df["Reactions"] = display_df["Reactions"].apply(lambda x: f"{x:,}")
        display_df["Shares"] = display_df["Shares"].apply(lambda x: f"{x:,}")
        display_df["Avg/Day"] = display_df["Avg/Day"].apply(lambda x: f"{x:,}")
        st.dataframe(display_df, use_container_width=True, height=350)

    with col_bar:
        fig_bar = px.bar(
            rankings.reset_index(),
            x="Agent", y=ENGAGEMENT_TYPES,
            barmode="stack",
            color_discrete_map=METRIC_COLORS,
        )
        fig_bar.update_traces(texttemplate="%{value:,}", textposition="inside")
        fig_bar.update_layout(
            template="plotly_dark",
            height=350,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis_title="",
            yaxis_title="Engagement",
            uniformtext_minsize=8, uniformtext_mode="hide",
        )
        st.plotly_chart(fig_bar, use_container_width=True)
