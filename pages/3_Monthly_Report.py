import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.sheets_connector import fetch_raw_daily, fetch_raw_agent_daily, fetch_raw_monthly
from utils.data_processor import get_agent_rankings
from config.settings import METRIC_COLORS, ENGAGEMENT_TYPES

st.set_page_config(page_title="Monthly Report", page_icon="📆", layout="wide")

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

st.title("Monthly Report")

with st.spinner("Loading..."):
    df_daily = fetch_raw_daily()
    df_agent_daily = fetch_raw_agent_daily()
    df_monthly = fetch_raw_monthly()

if df_daily.empty:
    st.error("No data available.")
    st.stop()

# --- Month Selector ---
df_daily["Month"] = df_daily["Date"].dt.to_period("M").astype(str)
months = sorted(df_daily["Month"].unique(), reverse=True)
selected_month = st.sidebar.selectbox("Select Month", months)

# Filter data for selected month
month_data = df_daily[df_daily["Month"] == selected_month].sort_values("Date")
month_start = month_data["Date"].min()
month_end = month_data["Date"].max()

# --- KPIs ---
st.markdown(f"### {pd.Timestamp(selected_month).strftime('%B %Y')}")

totals = month_data[ENGAGEMENT_TYPES + ["Total"]].sum()
days_in_month = len(month_data)
daily_avg = totals / days_in_month if days_in_month > 0 else totals * 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Engagement", f"{int(totals['Total']):,}")
c2.metric("Comments", f"{int(totals['Comments']):,}")
c3.metric("Reactions", f"{int(totals['Reactions']):,}")
c4.metric("Shares", f"{int(totals['Shares']):,}")
c5.metric("Daily Average", f"{int(daily_avg['Total']):,}")

st.divider()

# --- Daily Trend within Month ---
st.markdown("### Daily Trend")
col_trend, col_mix = st.columns([2, 1])

with col_trend:
    fig = go.Figure()
    for metric in ENGAGEMENT_TYPES:
        fig.add_trace(go.Scatter(
            x=month_data["Date"],
            y=month_data[metric],
            name=metric,
            mode="lines+markers",
            line=dict(color=METRIC_COLORS[metric], width=2),
        ))
    fig.add_trace(go.Scatter(
        x=month_data["Date"],
        y=month_data["Total"],
        name="Total",
        mode="lines+markers",
        line=dict(color=METRIC_COLORS["Total"], width=3, dash="dash"),
    ))
    fig.update_layout(
        template="plotly_dark",
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

with col_mix:
    st.markdown("### Engagement Composition")
    mix_vals = [int(totals[m]) for m in ENGAGEMENT_TYPES]
    fig_pie = px.pie(
        values=mix_vals, names=ENGAGEMENT_TYPES,
        hole=0.5,
        color=ENGAGEMENT_TYPES,
        color_discrete_map=METRIC_COLORS,
    )
    fig_pie.update_layout(
        template="plotly_dark", height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )
    fig_pie.update_traces(textposition="inside", textinfo="value+percent+label")
    st.plotly_chart(fig_pie, use_container_width=True)

# --- Calendar Heatmap ---
st.divider()
st.markdown("### Daily Heatmap")
heatmap_data = month_data[["Date", "Total"]].copy()
heatmap_data["Day"] = heatmap_data["Date"].dt.day
heatmap_data["Weekday"] = heatmap_data["Date"].dt.day_name()

fig_heat = px.bar(
    heatmap_data,
    x=heatmap_data["Date"].dt.strftime("%b %d (%a)"),
    y="Total",
    color="Total",
    color_continuous_scale="Blues",
)
fig_heat.update_traces(texttemplate="%{value:,}", textposition="outside")
fig_heat.update_layout(
    template="plotly_dark", height=300,
    margin=dict(l=20, r=20, t=30, b=20),
    xaxis_title="", yaxis_title="Total Engagement",
    coloraxis_showscale=False,
)
st.plotly_chart(fig_heat, use_container_width=True)

# --- Monthly Agent Leaderboard ---
st.divider()
st.markdown("### Agent Leaderboard")
rankings = get_agent_rankings(df_agent_daily, month_start, month_end)

if not rankings.empty:
    col_rank, col_bar = st.columns([1, 1])
    with col_rank:
        disp = rankings[["Agent", "Total", "Comments", "Reactions", "Shares", "% Contribution", "Avg/Day"]].copy()
        disp["% Contribution"] = disp["% Contribution"].apply(lambda x: f"{x}%")
        for c in ["Total", "Comments", "Reactions", "Shares"]:
            disp[c] = disp[c].apply(lambda x: f"{x:,}")
        st.dataframe(disp, use_container_width=True, height=400)

    with col_bar:
        fig_bar = px.bar(
            rankings.reset_index(),
            x="Agent", y=ENGAGEMENT_TYPES,
            barmode="stack",
            color_discrete_map=METRIC_COLORS,
        )
        fig_bar.update_traces(texttemplate="%{value:,}", textposition="inside")
        fig_bar.update_layout(
            template="plotly_dark", height=400,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis_title="", yaxis_title="Engagement",
            uniformtext_minsize=8, uniformtext_mode="hide",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# --- Month-over-Month (if multiple months) ---
if len(months) > 1 and not df_monthly.empty:
    st.divider()
    st.markdown("### Month-over-Month Trend")
    fig_mom = go.Figure()
    for metric in ENGAGEMENT_TYPES:
        if metric in df_monthly.columns:
            fig_mom.add_trace(go.Bar(
                x=df_monthly["Month"], y=df_monthly[metric],
                name=metric, marker_color=METRIC_COLORS[metric],
            ))
    fig_mom.update_traces(texttemplate="%{value:,}", textposition="inside")
    fig_mom.update_layout(
        barmode="stack", template="plotly_dark", height=300,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        uniformtext_minsize=8, uniformtext_mode="hide",
    )
    st.plotly_chart(fig_mom, use_container_width=True)
