import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.sheets_connector import fetch_raw_daily, fetch_raw_agent_daily
from utils.data_processor import get_day_comparison, filter_by_date
from config.settings import METRIC_COLORS, ENGAGEMENT_TYPES

st.set_page_config(page_title="Daily Report", page_icon="📅", layout="wide")

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

st.title("Daily Report")

with st.spinner("Loading..."):
    df_daily = fetch_raw_daily()
    df_agent_daily = fetch_raw_agent_daily()

if df_daily.empty:
    st.error("No data available.")
    st.stop()

available_dates = sorted(df_daily["Date"].dt.date.unique(), reverse=True)
selected_date = st.sidebar.date_input(
    "Select Date",
    value=available_dates[0],
    min_value=available_dates[-1],
    max_value=available_dates[0],
)

# --- Day Comparison ---
today_metrics, prev_metrics, deltas = get_day_comparison(df_daily, selected_date)

st.markdown(f"### {pd.Timestamp(selected_date).strftime('%A, %B %d, %Y')}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Engagement", f"{today_metrics.get('Total', 0):,}", delta=f"{deltas.get('Total', 0):+,} vs prev day")
c2.metric("Comments", f"{today_metrics.get('Comments', 0):,}", delta=f"{deltas.get('Comments', 0):+,}")
c3.metric("Reactions", f"{today_metrics.get('Reactions', 0):,}", delta=f"{deltas.get('Reactions', 0):+,}")
c4.metric("Shares", f"{today_metrics.get('Shares', 0):,}", delta=f"{deltas.get('Shares', 0):+,}")

st.divider()

# --- Agent Breakdown for Selected Day ---
st.markdown("### Agent Breakdown")
day_agents = df_agent_daily[df_agent_daily["Date"] == pd.Timestamp(selected_date)].copy()

if not day_agents.empty:
    day_agents = day_agents[day_agents["Total"] > 0].sort_values("Total", ascending=False)

    col_table, col_chart = st.columns([1, 1])

    with col_table:
        avg_total = df_daily["Total"].mean()
        display = day_agents[["Agent", "Comments", "Reactions", "Shares", "Total"]].copy()
        display["% of Day"] = (display["Total"] / display["Total"].sum() * 100).round(1).astype(str) + "%"

        def status_icon(total):
            return "Above Avg" if total >= avg_total / day_agents.shape[0] else "Below Avg"

        display["Status"] = display["Total"].apply(status_icon)
        st.dataframe(display.reset_index(drop=True), use_container_width=True, height=350)

    with col_chart:
        fig = px.bar(
            day_agents,
            x="Agent", y=ENGAGEMENT_TYPES,
            barmode="stack",
            color_discrete_map=METRIC_COLORS,
        )
        fig.update_traces(texttemplate="%{value:,}", textposition="inside")
        fig.update_layout(
            template="plotly_dark",
            height=350,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis_title="", yaxis_title="Engagement",
            uniformtext_minsize=8, uniformtext_mode="hide",
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- Top Performer Highlight ---
    top = day_agents.iloc[0]
    st.success(f"Top Performer: **{top['Agent']}** with **{int(top['Total']):,}** total engagement "
               f"({int(top['Comments']):,} comments, {int(top['Reactions']):,} reactions, {int(top['Shares']):,} shares)")
else:
    st.warning("No agent data available for this date.")

# --- Daily Trend Context (last 7 days) ---
st.divider()
st.markdown("### Recent Daily Trend")
fig_trend = go.Figure()
for metric in ENGAGEMENT_TYPES:
    fig_trend.add_trace(go.Bar(
        x=df_daily["Date"], y=df_daily[metric],
        name=metric,
        marker_color=METRIC_COLORS[metric],
    ))
fig_trend.update_traces(texttemplate="%{value:,}", textposition="inside")
fig_trend.update_layout(
    barmode="stack",
    template="plotly_dark",
    height=300,
    margin=dict(l=20, r=20, t=30, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    xaxis_title="", yaxis_title="Engagement",
    uniformtext_minsize=8, uniformtext_mode="hide",
)
# Highlight selected date
fig_trend.add_vline(
    x=pd.Timestamp(selected_date).timestamp() * 1000,
    line_dash="dash", line_color="yellow", line_width=2,
    annotation_text="Selected", annotation_position="top",
)
st.plotly_chart(fig_trend, use_container_width=True)
