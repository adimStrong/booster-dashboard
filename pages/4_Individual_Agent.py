import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.sheets_connector import fetch_raw_agent_daily, fetch_agent_list, fetch_raw_daily, fetch_account_data
from utils.data_processor import get_agent_rankings, get_account_by_agent
from config.settings import METRIC_COLORS, ENGAGEMENT_TYPES, ACCOUNT_STATUS_COLORS

st.set_page_config(page_title="Individual Agent", page_icon="👤", layout="wide")

st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 15px;
        border-radius: 12px;
        border-left: 4px solid #4F8BF9;
    }
    .agent-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #4F8BF9;
    }
</style>
""", unsafe_allow_html=True)

st.title("Individual Agent Report")

with st.spinner("Loading..."):
    df_agent_daily = fetch_raw_agent_daily()
    df_daily = fetch_raw_daily()
    agents = fetch_agent_list()
    df_accounts = fetch_account_data()

if df_agent_daily.empty:
    st.error("No data available.")
    st.stop()

# --- Agent Selector ---
active_agents = sorted(df_agent_daily[df_agent_daily["Total"] > 0]["Agent"].unique().tolist())
selected_agent = st.sidebar.selectbox("Select Agent", active_agents)

# --- Date Range ---
min_date = df_agent_daily["Date"].min().date()
max_date = df_agent_daily["Date"].max().date()
col_s1, col_s2 = st.sidebar.columns(2)
start_date = col_s1.date_input("Start", min_date)
end_date = col_s2.date_input("End", max_date)

# Filter agent data
agent_data = df_agent_daily[
    (df_agent_daily["Agent"] == selected_agent) &
    (df_agent_daily["Date"] >= pd.Timestamp(start_date)) &
    (df_agent_daily["Date"] <= pd.Timestamp(end_date))
].sort_values("Date")

all_agents_period = df_agent_daily[
    (df_agent_daily["Date"] >= pd.Timestamp(start_date)) &
    (df_agent_daily["Date"] <= pd.Timestamp(end_date))
]

st.markdown(f'<p class="agent-header">{selected_agent}</p>', unsafe_allow_html=True)

# --- Profile KPIs ---
total_engagement = int(agent_data["Total"].sum())
total_comments = int(agent_data["Comments"].sum())
total_reactions = int(agent_data["Reactions"].sum())
total_shares = int(agent_data["Shares"].sum())
days_active = int((agent_data["Total"] > 0).sum())
total_days = int(len(agent_data))
avg_per_day = int(total_engagement / days_active) if days_active > 0 else 0

# Rank
rankings = get_agent_rankings(df_agent_daily, start_date, end_date)
rank = "N/A"
contribution = "0%"
if not rankings.empty and selected_agent in rankings["Agent"].values:
    agent_rank_row = rankings[rankings["Agent"] == selected_agent]
    rank = agent_rank_row.index[0]
    contribution = f"{agent_rank_row['% Contribution'].values[0]}%"

# Consistency score (coefficient of variation - lower is more consistent)
active_days_data = agent_data[agent_data["Total"] > 0]["Total"]
if len(active_days_data) > 1:
    cv = (active_days_data.std() / active_days_data.mean() * 100)
    consistency = max(0, round(100 - cv, 1))
else:
    consistency = 100.0

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Engagement", f"{total_engagement:,}")
c2.metric("Rank", f"#{rank}")
c3.metric("Contribution", contribution)
c4.metric("Avg/Day", f"{avg_per_day:,}")
c5.metric("Days Active", f"{days_active}/{total_days}")
c6.metric("Consistency", f"{consistency}%")

st.divider()

# --- Performance Charts ---
col_line, col_pie = st.columns([2, 1])

with col_line:
    st.markdown("### Daily Performance")
    fig = go.Figure()
    for metric in ENGAGEMENT_TYPES:
        fig.add_trace(go.Scatter(
            x=agent_data["Date"], y=agent_data[metric],
            name=metric, mode="lines+markers",
            line=dict(color=METRIC_COLORS[metric], width=2),
        ))
    fig.add_trace(go.Scatter(
        x=agent_data["Date"], y=agent_data["Total"],
        name="Total", mode="lines+markers",
        line=dict(color=METRIC_COLORS["Total"], width=3, dash="dash"),
    ))
    fig.update_layout(
        template="plotly_dark", height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

with col_pie:
    st.markdown("### Engagement Breakdown")
    fig_pie = px.pie(
        values=[total_comments, total_reactions, total_shares],
        names=ENGAGEMENT_TYPES,
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

# --- Agent vs Team Average ---
st.divider()
st.markdown("### Agent vs Team Average")
team_avg = all_agents_period.groupby("Date")[ENGAGEMENT_TYPES + ["Total"]].mean().reset_index()
team_avg = team_avg.sort_values("Date")

fig_compare = go.Figure()
fig_compare.add_trace(go.Bar(
    x=agent_data["Date"].dt.strftime("%b %d"),
    y=agent_data["Total"],
    name=selected_agent,
    marker_color="#4F8BF9",
))
fig_compare.add_trace(go.Scatter(
    x=team_avg["Date"].dt.strftime("%b %d"),
    y=team_avg["Total"],
    name="Team Average",
    mode="lines+markers",
    line=dict(color="#EF553B", width=2, dash="dash"),
))
fig_compare.update_traces(texttemplate="%{value:,}", textposition="outside", selector=dict(type="bar"))
fig_compare.update_layout(
    template="plotly_dark", height=350,
    margin=dict(l=20, r=20, t=30, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    xaxis_title="", yaxis_title="Total Engagement",
)
st.plotly_chart(fig_compare, use_container_width=True)

# --- Account Status Section ---
st.divider()
st.markdown("### Account Status")
agent_accounts = df_accounts[df_accounts["Agent"] == selected_agent] if not df_accounts.empty else pd.DataFrame()

if not agent_accounts.empty:
    total_acct = len(agent_accounts)
    active_acct = len(agent_accounts[agent_accounts["Account Status"] == "Active"])
    active_pct = round(active_acct / total_acct * 100, 1) if total_acct > 0 else 0

    ac1, ac2, ac3 = st.columns(3)
    ac1.metric("Total Accounts", f"{total_acct}")
    ac2.metric("Active Accounts", f"{active_acct}")
    ac3.metric("Active Rate", f"{active_pct}%")

    col_acct_pie, col_acct_timeline = st.columns([1, 1])

    with col_acct_pie:
        status_counts = agent_accounts["Account Status"].value_counts()
        fig_acct = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            hole=0.5,
            color=status_counts.index,
            color_discrete_map=ACCOUNT_STATUS_COLORS,
        )
        fig_acct.update_layout(
            template="plotly_dark", height=300,
            margin=dict(l=20, r=20, t=30, b=20),
        )
        fig_acct.update_traces(textposition="inside", textinfo="value+percent+label")
        st.plotly_chart(fig_acct, use_container_width=True)

    with col_acct_timeline:
        dated = agent_accounts.dropna(subset=["Created Date"])
        if not dated.empty:
            dated["Month"] = dated["Created Date"].dt.to_period("M").astype(str)
            timeline = dated.groupby("Month").size().reset_index(name="Accounts Created")
            fig_tl = px.bar(
                timeline, x="Month", y="Accounts Created",
                color_discrete_sequence=["#4F8BF9"],
            )
            fig_tl.update_traces(texttemplate="%{value}", textposition="outside")
            fig_tl.update_layout(
                template="plotly_dark", height=300,
                margin=dict(l=20, r=20, t=30, b=20),
                xaxis_title="", yaxis_title="Accounts",
            )
            st.plotly_chart(fig_tl, use_container_width=True)
else:
    st.info("No account data available for this agent.")
