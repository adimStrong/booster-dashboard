import pandas as pd
from config.settings import ENGAGEMENT_TYPES


def filter_by_date(df, start_date, end_date):
    mask = (df["Date"] >= pd.Timestamp(start_date)) & (df["Date"] <= pd.Timestamp(end_date))
    return df[mask].copy()


def filter_by_agent(df, agent):
    if agent and agent != "All Agents":
        return df[df["Agent"] == agent].copy()
    return df.copy()


def get_daily_summary(df_daily, start_date, end_date):
    filtered = filter_by_date(df_daily, start_date, end_date)
    if filtered.empty:
        return filtered, {}

    total = filtered[ENGAGEMENT_TYPES + ["Total"]].sum()
    days = len(filtered)
    daily_avg = total / days if days > 0 else total * 0

    summary = {
        "total_engagement": int(total["Total"]),
        "comments": int(total["Comments"]),
        "reactions": int(total["Reactions"]),
        "shares": int(total["Shares"]),
        "days": days,
        "daily_avg": int(daily_avg["Total"]),
        "daily_avg_comments": int(daily_avg["Comments"]),
        "daily_avg_reactions": int(daily_avg["Reactions"]),
        "daily_avg_shares": int(daily_avg["Shares"]),
    }
    return filtered, summary


def get_agent_rankings(df_agent_daily, start_date, end_date):
    filtered = filter_by_date(df_agent_daily, start_date, end_date)
    if filtered.empty:
        return pd.DataFrame()

    grouped = filtered.groupby("Agent")[ENGAGEMENT_TYPES + ["Total"]].sum().reset_index()
    grand_total = grouped["Total"].sum()
    grouped["% Contribution"] = (grouped["Total"] / grand_total * 100).round(1) if grand_total > 0 else 0

    days = filtered["Date"].nunique()
    grouped["Avg/Day"] = (grouped["Total"] / days).round(0).astype(int) if days > 0 else 0
    grouped = grouped.sort_values("Total", ascending=False).reset_index(drop=True)
    grouped.index = grouped.index + 1
    grouped.index.name = "Rank"
    return grouped


def get_weekly_data(df_daily):
    if df_daily.empty:
        return pd.DataFrame()
    df = df_daily.copy()
    df["Week"] = df["Date"].dt.isocalendar().week.astype(int)
    df["Year"] = df["Date"].dt.isocalendar().year.astype(int)
    weekly = df.groupby(["Year", "Week"]).agg(
        Comments=("Comments", "sum"),
        Reactions=("Reactions", "sum"),
        Shares=("Shares", "sum"),
        Total=("Total", "sum"),
        Start=("Date", "min"),
        End=("Date", "max"),
        Days=("Date", "count"),
    ).reset_index()
    weekly["Is_Complete"] = weekly["Days"] >= 7
    weekly["Week_Label"] = weekly.apply(
        lambda r: (
            f"W{r['Week']} ({r['Start'].strftime('%b %d')} - {r['End'].strftime('%b %d')})"
            + ("" if r["Is_Complete"] else " *")
        ), axis=1
    )
    weekly["Week_Range"] = weekly.apply(
        lambda r: f"{r['Start'].strftime('%b %d, %Y')} - {r['End'].strftime('%b %d, %Y')}", axis=1
    )
    for metric in ENGAGEMENT_TYPES + ["Total"]:
        weekly[f"Avg_{metric}"] = (weekly[metric] / weekly["Days"]).round(0).astype(int)
    return weekly.sort_values(["Year", "Week"]).reset_index(drop=True)


def get_weekly_agent_data(df_agent_daily):
    if df_agent_daily.empty:
        return pd.DataFrame()
    df = df_agent_daily.copy()
    df["Week"] = df["Date"].dt.isocalendar().week.astype(int)
    df["Year"] = df["Date"].dt.isocalendar().year.astype(int)
    weekly = df.groupby(["Year", "Week", "Agent"])[ENGAGEMENT_TYPES + ["Total"]].sum().reset_index()
    return weekly


def get_day_comparison(df_daily, target_date):
    """Get metrics for target_date and previous day, with deltas."""
    df = df_daily.sort_values("Date")
    today = df[df["Date"] == pd.Timestamp(target_date)]
    prev_dates = df[df["Date"] < pd.Timestamp(target_date)]

    today_metrics = {}
    prev_metrics = {}
    deltas = {}

    if not today.empty:
        row = today.iloc[0]
        today_metrics = {k: int(row[k]) for k in ENGAGEMENT_TYPES + ["Total"]}
    if not prev_dates.empty:
        row = prev_dates.iloc[-1]
        prev_metrics = {k: int(row[k]) for k in ENGAGEMENT_TYPES + ["Total"]}

    for k in ENGAGEMENT_TYPES + ["Total"]:
        t = today_metrics.get(k, 0)
        p = prev_metrics.get(k, 0)
        deltas[k] = t - p

    return today_metrics, prev_metrics, deltas


def get_account_summary(df_accounts):
    """Overall account status summary."""
    if df_accounts.empty:
        return {}
    total = len(df_accounts)
    by_status = df_accounts["Account Status"].value_counts().to_dict()
    active = by_status.get("Active", 0)
    return {
        "total": total,
        "active": active,
        "active_pct": round(active / total * 100, 1) if total > 0 else 0,
        "by_status": by_status,
    }


def get_account_by_agent(df_accounts):
    """Account breakdown per agent."""
    if df_accounts.empty:
        return pd.DataFrame()
    pivot = df_accounts.groupby(["Agent", "Account Status"]).size().unstack(fill_value=0)
    pivot["Total"] = pivot.sum(axis=1)
    active_col = "Active" if "Active" in pivot.columns else None
    if active_col:
        pivot["Active %"] = (pivot[active_col] / pivot["Total"] * 100).round(1)
    else:
        pivot["Active %"] = 0
    return pivot.sort_values("Total", ascending=False)


def get_account_creation_timeline(df_accounts):
    """Monthly account creation counts."""
    if df_accounts.empty:
        return pd.DataFrame()
    df = df_accounts.dropna(subset=["Created Date"]).copy()
    df["Month"] = df["Created Date"].dt.to_period("M").astype(str)
    timeline = df.groupby(["Month", "Agent"]).size().reset_index(name="Count")
    return timeline
