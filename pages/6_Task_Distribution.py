import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.sheets_connector import fetch_task_daily, fetch_raw_daily
from utils.data_processor import (
    get_task_distribution, get_task_by_agent,
    get_task_daily_trend, get_task_agent_matrix, filter_by_date,
)
from config.settings import TASK_COLORS

st.set_page_config(page_title="Task Distribution", page_icon="📊", layout="wide")

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

st.title("Task Distribution")

with st.spinner("Loading task data..."):
    df_task = fetch_task_daily()
    df_daily = fetch_raw_daily()

if df_task.empty:
    st.error("No task data available. Run the PBI export with task data first.")
    st.stop()

# --- Sidebar Filters ---
available_dates = sorted(df_task["Date"].dt.date.unique())
start_date = st.sidebar.date_input(
    "Start Date",
    value=available_dates[0],
    min_value=available_dates[0],
    max_value=available_dates[-1],
)
end_date = st.sidebar.date_input(
    "End Date",
    value=available_dates[-1],
    min_value=available_dates[0],
    max_value=available_dates[-1],
)

task_options = ["All Tasks"] + sorted(df_task["Task"].dropna().unique().tolist())
selected_task = st.sidebar.selectbox("Task Type", task_options)

# --- KPIs ---
dist = get_task_distribution(df_task, start_date, end_date)
if dist.empty:
    st.warning("No data for selected date range.")
    st.stop()

grand_total = int(dist["Total"].sum())

# Show KPI per task type
cols = st.columns(min(len(dist), 6))
for i, row in dist.iterrows():
    if i < len(cols):
        cols[i].metric(row["Task"], f"{int(row['Total']):,}", delta=f"{row['% of Total']}%")

st.divider()

# --- Row 1: Pie Chart + Stacked Bar ---
col_pie, col_bar = st.columns([1, 1])

with col_pie:
    st.markdown("### Comment Distribution by Task")
    fig_pie = px.pie(
        dist, values="Total", names="Task",
        color="Task", color_discrete_map=TASK_COLORS,
        hole=0.4,
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    fig_pie.update_layout(
        template="plotly_dark",
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_bar:
    st.markdown("### Task Breakdown by Agent")
    task_by_agent = get_task_by_agent(df_task, start_date, end_date)
    if not task_by_agent.empty:
        # Sort agents by total descending
        agent_order = task_by_agent.groupby("Agent")["Total"].sum().sort_values(ascending=True).index.tolist()
        fig_bar = px.bar(
            task_by_agent, x="Total", y="Agent", color="Task",
            orientation="h",
            color_discrete_map=TASK_COLORS,
            category_orders={"Agent": agent_order},
        )
        fig_bar.update_layout(
            template="plotly_dark",
            height=400,
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.15),
            xaxis_title="Total Engagement",
            yaxis_title="",
            barmode="stack",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# --- Row 2: Daily Trend ---
st.markdown("### Daily Trend by Task")
trend_data = get_task_daily_trend(df_task, start_date, end_date)
if not trend_data.empty:
    fig_trend = px.line(
        trend_data, x="Date", y="Total", color="Task",
        color_discrete_map=TASK_COLORS,
    )
    fig_trend.update_layout(
        template="plotly_dark",
        height=350,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis_title="", yaxis_title="Total Engagement",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# --- Row 3: Agent x Task Matrix ---
st.markdown("### Agent x Task Matrix")
matrix = get_task_agent_matrix(df_task, start_date, end_date)
if not matrix.empty:
    # Format with commas
    styled = matrix.style.format("{:,.0f}")
    st.dataframe(styled, use_container_width=True, height=400)

    # Heatmap
    st.markdown("### Heatmap")
    heat_data = matrix.drop(columns=["Grand Total"], errors="ignore")
    fig_heat = px.imshow(
        heat_data,
        color_continuous_scale="Blues",
        aspect="auto",
        text_auto=True,
    )
    fig_heat.update_layout(
        template="plotly_dark",
        height=max(300, len(heat_data) * 35 + 100),
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Task", yaxis_title="Agent",
    )
    st.plotly_chart(fig_heat, use_container_width=True)
