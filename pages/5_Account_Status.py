import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.sheets_connector import fetch_account_data
from utils.data_processor import get_account_summary, get_account_by_agent, get_account_creation_timeline
from config.settings import ACCOUNT_STATUS_COLORS

st.set_page_config(page_title="Account Status", page_icon="📋", layout="wide")

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

st.title("Account Status Overview")

with st.spinner("Loading account data..."):
    df_accounts = fetch_account_data()

if df_accounts.empty:
    st.error("No account data found.")
    st.stop()

# --- Filters ---
all_statuses = sorted(df_accounts["Account Status"].unique().tolist())
all_agents = sorted(df_accounts["Agent"].unique().tolist())

agent_filter = st.sidebar.selectbox("Filter by Agent", ["All Agents"] + all_agents)
status_filter = st.sidebar.multiselect("Filter by Status", all_statuses, default=all_statuses)

filtered = df_accounts[df_accounts["Account Status"].isin(status_filter)]
if agent_filter != "All Agents":
    filtered = filtered[filtered["Agent"] == agent_filter]

# --- Overall KPIs ---
summary = get_account_summary(filtered)
total = summary.get("total", 0)
active = summary.get("active", 0)
active_pct = summary.get("active_pct", 0)
locked = sum(v for k, v in summary.get("by_status", {}).items() if "Locked" in k)
disabled = summary.get("by_status", {}).get("Disabled", 0)
new_acct = summary.get("by_status", {}).get("New Account", 0)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Accounts", f"{total:,}")
c2.metric("Active", f"{active:,}", delta=f"{active_pct}%")
c3.metric("New Accounts", f"{new_acct:,}")
c4.metric("Locked", f"{locked:,}")
c5.metric("Disabled", f"{disabled:,}")

st.divider()

# --- Status Breakdown ---
col_pie, col_bar = st.columns([1, 1])

with col_pie:
    st.markdown("### Account Status Distribution")
    status_counts = filtered["Account Status"].value_counts()
    fig_pie = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        hole=0.5,
        color=status_counts.index,
        color_discrete_map=ACCOUNT_STATUS_COLORS,
    )
    fig_pie.update_layout(
        template="plotly_dark", height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
    )
    fig_pie.update_traces(textposition="inside", textinfo="value+percent+label")
    st.plotly_chart(fig_pie, use_container_width=True)

with col_bar:
    st.markdown("### Accounts by Agent")
    agent_status = filtered.groupby(["Agent", "Account Status"]).size().reset_index(name="Count")
    fig_bar = px.bar(
        agent_status,
        x="Agent", y="Count", color="Account Status",
        barmode="stack",
        color_discrete_map=ACCOUNT_STATUS_COLORS,
    )
    fig_bar.update_traces(texttemplate="%{value}", textposition="inside")
    fig_bar.update_layout(
        template="plotly_dark", height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.05),
        xaxis_title="", yaxis_title="Accounts",
        uniformtext_minsize=8, uniformtext_mode="hide",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# --- Agent Health Table ---
st.divider()
st.markdown("### Agent Account Health")
agent_summary = get_account_by_agent(filtered)

if not agent_summary.empty:
    display = agent_summary.copy()
    display = display.reset_index()

    # Health status indicator
    def health_label(pct):
        if pct >= 80:
            return "Healthy"
        elif pct >= 60:
            return "Fair"
        else:
            return "At Risk"

    if "Active %" in display.columns:
        display["Health"] = display["Active %"].apply(health_label)

    st.dataframe(display, use_container_width=True, height=350)

    # Health comparison bar
    if "Active %" in display.columns:
        fig_health = px.bar(
            display.sort_values("Active %", ascending=True),
            x="Active %", y="Agent",
            orientation="h",
            color="Active %",
            color_continuous_scale=["#EF553B", "#FECB52", "#00CC96"],
            range_color=[0, 100],
        )
        fig_health.add_vline(x=80, line_dash="dash", line_color="white", annotation_text="Target 80%")
        fig_health.update_traces(texttemplate="%{x:.1f}%", textposition="inside")
        fig_health.update_layout(
            template="plotly_dark", height=350,
            margin=dict(l=20, r=20, t=30, b=20),
            yaxis_title="", xaxis_title="Active %",
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_health, use_container_width=True)

# --- Account Creation Timeline ---
st.divider()
st.markdown("### Account Creation Timeline")
timeline = get_account_creation_timeline(filtered)

if not timeline.empty:
    fig_tl = px.bar(
        timeline,
        x="Month", y="Count", color="Agent",
        barmode="stack",
    )
    fig_tl.update_traces(texttemplate="%{value}", textposition="inside")
    fig_tl.update_layout(
        template="plotly_dark", height=350,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.05),
        xaxis_title="", yaxis_title="Accounts Created",
        uniformtext_minsize=8, uniformtext_mode="hide",
    )
    st.plotly_chart(fig_tl, use_container_width=True)
else:
    st.info("No creation date data available.")
