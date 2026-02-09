import os
import json
import tempfile

# For Railway/cloud: credentials come from GOOGLE_CREDENTIALS env var
# For local: falls back to the JSON file
_LOCAL_CRED_FILE = r"C:\Users\us\Downloads\gen-lang-client-0641615854-1617a1750c07.json"

def get_service_account_file():
    cred_json = os.environ.get("GOOGLE_CREDENTIALS")
    if cred_json:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        tmp.write(cred_json)
        tmp.close()
        return tmp.name
    return _LOCAL_CRED_FILE

SERVICE_ACCOUNT_FILE = get_service_account_file()

ENGAGEMENT_SHEET_ID = "1Mzm8sbn7C2qpfNunNdAwnA1rutDaHzWCHVz7mjdXPGA"
ACCOUNTS_SHEET_ID = "13L7-Z_GDxXvP0SFNCQXzcN7DzW8zc65ABRcEc1jL2bs"

ENGAGEMENT_TYPES = ["Comments", "Reactions", "Shares"]
EXCLUDED_AGENTS = ["Alecs", "Moja", "Valerie"]
METRIC_COLORS = {
    "Comments": "#636EFA",
    "Reactions": "#EF553B",
    "Shares": "#00CC96",
    "Total": "#AB63FA",
}

TASK_TYPES = ["SocMed", "Live", "JuanBingo (SocMed)", "Studio/Host", "Comunity Group", "Review", "Cs Complain", "Ads", "JuanSports"]
TASK_COLORS = {
    "SocMed": "#636EFA",
    "Live": "#EF553B",
    "JuanBingo (SocMed)": "#FFA15A",
    "Studio/Host": "#AB63FA",
    "Comunity Group": "#00CC96",
    "Review": "#FECB52",
    "Cs Complain": "#19D3F3",
    "Ads": "#FF6692",
    "JuanSports": "#B6E880",
}

ACCOUNT_STATUS_COLORS = {
    "Active": "#00CC96",
    "New Account": "#636EFA",
    "Locked FB": "#EF553B",
    "Disabled": "#FF6692",
    "Locked Account": "#FFA15A",
    "For Verification": "#FECB52",
    "INDIAN ACCOUNT": "#19D3F3",
    "NEW INDIAN": "#B6E880",
}
