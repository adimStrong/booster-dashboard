import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from config.settings import SERVICE_ACCOUNT_FILE, ENGAGEMENT_SHEET_ID, ACCOUNTS_SHEET_ID, EXCLUDED_AGENTS


def _get_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
    ]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    return gspread.authorize(creds)


def _serial_to_date(value):
    """Convert Excel serial date number or date string to datetime."""
    if not value or not str(value).strip():
        return None
    value = str(value).strip().replace(",", "")
    # Try parsing as a date string first (e.g., "2026-01-20")
    try:
        return pd.Timestamp(value).to_pydatetime()
    except (ValueError, TypeError):
        pass
    # Fall back to Excel serial number
    try:
        serial = int(float(value))
        if serial > 40000:  # Sanity check for valid serial dates
            return datetime(1899, 12, 30) + timedelta(days=serial)
    except (ValueError, TypeError):
        pass
    return None


@st.cache_data(ttl=300)
def fetch_agent_list():
    client = _get_client()
    sheet = client.open_by_key(ENGAGEMENT_SHEET_ID)
    ws = sheet.worksheet("_AgentList")
    data = ws.get_all_values()
    agents = [row[0] for row in data[1:] if row[0].strip() and row[0].strip() not in EXCLUDED_AGENTS]
    return agents


@st.cache_data(ttl=300)
def fetch_raw_daily():
    client = _get_client()
    sheet = client.open_by_key(ENGAGEMENT_SHEET_ID)
    ws = sheet.worksheet("_RawDaily")
    data = ws.get_all_values()
    if len(data) <= 1:
        return pd.DataFrame(columns=["Date", "Comments", "Reactions", "Shares", "Total"])

    df = pd.DataFrame(data[1:], columns=data[0])
    df["Date"] = df["Date"].apply(_serial_to_date)
    df = df.dropna(subset=["Date"])
    for col in ["Comments", "Reactions", "Shares", "Total"]:
        df[col] = pd.to_numeric(df[col].str.replace(",", ""), errors="coerce").fillna(0).astype(int)
    df = df.sort_values("Date").reset_index(drop=True)
    return df


@st.cache_data(ttl=300)
def fetch_raw_agent_daily():
    client = _get_client()
    sheet = client.open_by_key(ENGAGEMENT_SHEET_ID)
    ws = sheet.worksheet("_RawAgentDaily")
    data = ws.get_all_values()
    if len(data) <= 1:
        return pd.DataFrame(columns=["Date", "Agent", "Comments", "Reactions", "Shares", "Total"])

    df = pd.DataFrame(data[1:], columns=data[0])
    df["Date"] = df["Date"].apply(_serial_to_date)
    df = df.dropna(subset=["Date"])
    for col in ["Comments", "Reactions", "Shares", "Total"]:
        df[col] = pd.to_numeric(df[col].str.replace(",", ""), errors="coerce").fillna(0).astype(int)
    df = df[~df["Agent"].isin(EXCLUDED_AGENTS)]
    df = df.sort_values(["Date", "Agent"]).reset_index(drop=True)
    return df


@st.cache_data(ttl=300)
def fetch_raw_monthly():
    client = _get_client()
    sheet = client.open_by_key(ENGAGEMENT_SHEET_ID)
    ws = sheet.worksheet("_RawMonthly")
    data = ws.get_all_values()
    if len(data) <= 1:
        return pd.DataFrame(columns=["Month", "Comments", "Reactions", "Shares", "Total"])

    df = pd.DataFrame(data[1:], columns=data[0])
    for col in ["Comments", "Reactions", "Shares", "Total"]:
        df[col] = pd.to_numeric(df[col].str.replace(",", ""), errors="coerce").fillna(0).astype(int)
    return df


@st.cache_data(ttl=300)
def fetch_account_data():
    """Fetch account data from all agent sheets in the accounts spreadsheet.
    Blank usernames are excluded."""
    client = _get_client()
    sheet = client.open_by_key(ACCOUNTS_SHEET_ID)

    all_accounts = []
    for ws in sheet.worksheets():
        agent_name = ws.title
        data = ws.get_all_values()
        if len(data) <= 2:
            continue

        header = data[2]
        has_locked_col = "LOCKED DATE" in header

        for row in data[3:]:
            if has_locked_col:
                username_idx = 4
                created_idx = 2
                status_idx = 12
                dummy_idx = 11
            else:
                username_idx = 3
                created_idx = 2
                status_idx = 11
                dummy_idx = 10

            username = row[username_idx].strip() if len(row) > username_idx else ""
            if not username:
                continue

            status = row[status_idx].strip() if len(row) > status_idx else ""
            if not status:
                continue

            created_date = row[created_idx].strip() if len(row) > created_idx else ""
            dummy_name = row[dummy_idx].strip() if len(row) > dummy_idx else ""

            all_accounts.append({
                "Agent": agent_name.title(),
                "Username": username,
                "Created Date": created_date,
                "Dummy Name": dummy_name,
                "Account Status": status,
            })

    df = pd.DataFrame(all_accounts)
    if not df.empty:
        df = df[~df["Agent"].isin(EXCLUDED_AGENTS)]
        df["Created Date"] = pd.to_datetime(df["Created Date"], format="mixed", dayfirst=True, errors="coerce")
    return df
