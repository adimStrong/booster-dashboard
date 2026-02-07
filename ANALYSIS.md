# Booster Team Dashboard - Project Analysis

## 1. DATA ANALYSIS

### Source: Google Sheet (9 sheets)

| Sheet | Purpose | Rows | Key Fields |
|-------|---------|------|------------|
| `_AgentList` | Master list of 13 agents | 14 | Agent names |
| `_RawDaily` | Daily totals (all agents) | 7 | Date, Comments, Reactions, Shares, Total |
| `_RawAgentDaily` | Per-agent daily breakdown | 51 | Date, Agent, Comments, Reactions, Shares, Total |
| `_RawMonthly` | Monthly aggregates | 2 | Month, Comments, Reactions, Shares, Total |
| `Dashboard` | Formatted dashboard view | 43 | Filters, KPIs, Rankings, Trends |
| `Executive Summary` | KPIs + period stats | 24 | Metrics, Daily Avg, Composition % |
| `Agent Rankings` | Ranked agents | 17 | Rank, Agent, Total, % Contribution, Avg/Day |
| `Daily Totals` | Daily with trend indicators | 13 | Date, Metrics, vs Avg, Trend arrows |

### Data Profile

- **Date Range**: Feb 1-6, 2026 (6 days of data)
- **Dates stored as**: Excel serial numbers (46054 = 2026-02-01)
- **13 Registered Agents**: Alecs, Carlo, Jillian, Jullian, Kim, Mhay, Moja, Rapi, Roxan, Sheena, Tisha, Trisha, Valerie
- **7 Active Agents** (during current period): Carlo, Jullian, Mhay, Rapi, Roxan, Trisha, Valerie
- **2 Inactive Agents**: Alecs, Moja (all zeros)
- **4 Agents not in raw data**: Jillian, Kim, Sheena, Tisha

### Engagement Metrics

| Metric | Total | % of Total | Daily Avg |
|--------|-------|-----------|-----------|
| **Total Engagement** | **20,421** | 100% | 3,404 |
| Reactions | 10,207 | 50.0% | 1,701 |
| Comments | 6,413 | 31.4% | 1,069 |
| Shares | 3,801 | 18.6% | 634 |

### Agent Performance Rankings

| Rank | Agent | Total | % Contribution | Avg/Day |
|------|-------|-------|---------------|---------|
| 1 | Trisha | 4,239 | 20.8% | 707 |
| 2 | Rapi | 4,219 | 20.7% | 703 |
| 3 | Roxan | 3,341 | 16.4% | 557 |
| 4 | Mhay | 2,925 | 14.3% | 488 |
| 5 | Jullian | 2,371 | 11.6% | 395 |
| 6 | Carlo | 2,349 | 11.5% | 392 |
| 7 | Valerie | 977 | 4.8% | 163 |

### Key Observations

1. **Top 2 agents (Trisha + Rapi) generate 41.5%** of all engagement
2. **Reactions are the dominant metric** at 50% of total engagement
3. **Valerie is significantly underperforming** at only 4.8% contribution
4. **Daily variation is moderate** - range from 3,091 to 3,822 (23.6% swing)
5. **Best day was Feb 3** (3,822 total) driven by high Reactions (2,025)
6. **Worst day was Feb 2** (3,091 total)
7. **Agent availability varies** - not all agents work every day (e.g., Roxan had 0 on Feb 2)

---

## 2. CASE STUDIES & ALIGNED FRAMEWORKS

### Case Study 1: Sprout Social's Multi-Tier Reporting Framework
**Alignment**: Daily/Weekly/Monthly reporting cadence
- Daily dashboards for real-time content performance monitoring
- Weekly reports for campaign-level analysis and A/B comparisons
- Monthly reports for strategic review and goal-setting
- Supports individual team member performance tracking
- **Takeaway**: Our dashboard should mirror this tiered approach with drill-down capability

### Case Study 2: Productivity Dashboard (Streamlit + Google Sheets)
**Alignment**: Same tech stack we'll use
- GitHub project (areshytko/productivity-dashboard) demonstrates Streamlit + Google Sheets integration
- Uses red/yellow/green KPI indicators for quick status assessment
- Auto-generates historical trends and suggested actions
- **Takeaway**: Proven pattern for our exact use case - Google Sheets as data source, Streamlit as visualization layer

### Case Study 3: Hootsuite's Team Performance Dashboard
**Alignment**: Multi-agent performance tracking
- Tracks individual team members' contribution to overall engagement
- Provides share-of-voice analysis per team member
- Automated scheduled reporting (daily/weekly/monthly)
- **Takeaway**: Our % Contribution column aligns with this - expand to include trend analysis per agent

### Case Study 4: Social Media Benchmarks 2025-2026
**Alignment**: Industry standard metrics
- Comments, Reactions, Shares are the standard social media engagement KPIs
- TikTok engagement rate ~3.70%, Instagram ~0.48%, Facebook ~0.15%
- **Takeaway**: Our agents' daily averages (163-707) are trackable against industry benchmarks when we know the platform

### Case Study 5: Whatagraph Team Reporting Dashboard
**Alignment**: Visual reporting for stakeholders
- Color-coded performance tiers (top/mid/low performers)
- Automated PDF report generation for distribution
- Period-over-period comparison (WoW, MoM)
- **Takeaway**: Include exportable reports and visual performance tiers

---

## 3. RECOMMENDED TECHNOLOGY STACK

| Component | Technology | Reason |
|-----------|-----------|--------|
| **Frontend/Dashboard** | Streamlit | Fast to build, Python-native, interactive widgets |
| **Data Source** | Google Sheets API via `gspread` | Already set up with service account |
| **Data Processing** | Pandas | Data manipulation, aggregation, time-series |
| **Visualization** | Plotly | Interactive charts, better than matplotlib for dashboards |
| **Deployment** | Streamlit Cloud or Local | Easy deployment, free tier available |
| **Auth** | Google Service Account | Already configured |

---

## 4. DASHBOARD FEATURE PLAN

### Page 1: Overview Dashboard
- KPI cards (Total Engagement, Comments, Reactions, Shares)
- Daily trend line chart
- Engagement mix pie/donut chart
- Top performers leaderboard
- Date range filter + Agent filter

### Page 2: Daily Report
- Today's metrics vs yesterday's (with % change)
- Per-agent breakdown for today
- Hourly heatmap (if data available)
- Red/Yellow/Green status indicators

### Page 3: Weekly Report
- Week-over-week comparison
- Weekly totals by agent (stacked bar chart)
- Top/bottom performers of the week
- Weekly engagement trend

### Page 4: Monthly Report
- Month-to-date metrics
- Month-over-month comparison
- Monthly agent leaderboard
- Engagement composition trends over months

### Page 5: Individual Agent View
- Agent selector dropdown
- Agent's daily performance line chart
- Agent's engagement breakdown (Comments/Reactions/Shares)
- Agent's rank among peers
- Agent's contribution % trend over time
- Consistency score (std deviation analysis)

---

## 5. SOURCES

- [Social Media Benchmarks 2026 - Enrich Labs](https://www.enrichlabs.ai/blog/social-media-benchmarks-2025)
- [Social Media Dashboard Guide - Improvado](https://improvado.io/blog/social-media-dashboard)
- [Social Media Engagement Rates - Planable](https://planable.io/blog/social-media-engagement-rate/)
- [Social Media Reporting - Sprout Social](https://sproutsocial.com/insights/social-media-reporting/)
- [Social Media Dashboard Templates - Sprout Social](https://sproutsocial.com/insights/social-media-dashboard/)
- [Productivity Dashboard (Streamlit + Sheets) - GitHub](https://github.com/areshytko/productivity-dashboard)
- [KPI Dashboard Templates - Monday.com](https://monday.com/blog/project-management/kpi-dashboard-template/)
- [Social Media Dashboard - Rival IQ](https://www.rivaliq.com/blog/social-media-dashboard/)
- [Social Media Dashboards - Hootsuite](https://blog.hootsuite.com/social-media-dashboard/)
- [Social Media Metrics to Track - Sprout Social](https://sproutsocial.com/insights/social-media-metrics/)
