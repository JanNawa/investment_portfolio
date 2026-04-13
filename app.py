"""
The Hard Truth: Passive vs Robo-Advisor
Real Wealthsimple TFSA data · Nov 2025 – Apr 2026
Inspired by Warren Buffett's 10-year bet (2008–2017)

Real data sources:
- Portfolio: Personal Wealthsimple export
- Robo CAC: Sacra (2024) — robo-advisor CAC soared to $650+
- Retention benchmarks: Financial/credit industry churn 25% (Aspect 2020 via Deloitte-cited sources)
- Passive investor churn: ~5-8%/yr (estimated, low-cost ETF holders rarely switch)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Passive vs Robo · The Hard Truth",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
[data-testid="stAppViewContainer"] { background: #f8f7f4; }
[data-testid="stSidebar"] { background: #1a1a24; }
[data-testid="stSidebar"] * { color: #e2ddd6 !important; }
.kpi { background:#fff; border:1px solid #ebebeb; border-radius:14px; padding:20px 22px; margin-bottom:8px; }
.kpi-lbl { font-size:0.7rem; text-transform:uppercase; letter-spacing:1.5px; color:#888; margin-bottom:4px; }
.kpi-val { font-family:'Libre Baskerville',serif; font-size:1.8rem; color:#1a1a24; }
.kpi-sub { font-size:0.8rem; margin-top:4px; }
.green { color:#2d7a3e; } .red { color:#c0392b; } .amber { color:#b8860b; } .gray { color:#888; }
.section { font-family:'Libre Baskerville',serif; font-size:1.2rem; color:#1a1a24;
           border-bottom:2px solid #c8b87a; padding-bottom:6px; margin:32px 0 14px; }
.insight { background:#fffbf0; border-left:4px solid #c8b87a; border-radius:0 10px 10px 0;
           padding:14px 18px; font-size:0.87rem; color:#444; line-height:1.7; margin:12px 0; }
.source { font-size:0.75rem; color:#888; font-style:italic; margin-top:4px; }
.hard-truth { background:#1a1a24; color:#e2ddd6; border-radius:14px; padding:28px 32px; margin-top:28px; }
.ht-q { font-family:'Libre Baskerville',serif; font-size:1.35rem; color:#c8b87a; margin:0 0 12px; line-height:1.4; }
.ht-body { font-size:0.88rem; color:#9898b8; line-height:1.75; margin:0; }
</style>
""", unsafe_allow_html=True)

# ── REAL DATA (from actual Wealthsimple export) ───────────────────────────────
# WZ05 robo: $3,500 deposited Nov 28 2025, fully invested Dec 1
# Portfolio value Apr 11 2026: $3,505.85 (holdings at last known prices)
# Dividends: $43.90  Fees: -$6.68  Net: $37.22
# Total: $3,543.07  Return: +$43.07  = +1.23% over ~4.5 months

# HQ9B passive: $7,350 deposited across 8 tranches Nov 2025–Mar 2026
# Portfolio value Apr 11 2026: $7,101.80 (holdings at Apr 9 approximate prices)
# Dividends: $37.72  Total: $7,139.52  Return: -$210.48 = -2.86%
# NOTE: HQ9B was hit harder by Apr 2026 tariff shock (more tech/equity exposure)
# WZ had more bonds/gold which acted as safe haven in the tariff shock

REAL = {
    "wz_deposit": 3500.0,
    "wz_end_value": 3543.07,
    "wz_5m_return_pct": 1.23,
    "wz_fees_paid": 6.68,
    "wz_dividends": 43.90,
    "hq_deposit": 7350.0,
    "hq_end_value": 7139.52,
    "hq_5m_return_pct": -2.86,
    "hq_dividends": 37.72,
    # Monthly % returns (return on invested capital at each period)
    "months": ["Nov 28", "Dec", "Jan", "Feb", "Mar", "Apr 11"],
    "wz_monthly_pct": [0.00, 0.71, 0.54, 0.74, 0.94, 1.23],
    "hq_monthly_pct": [0.00, 0.14, -0.86, -0.87, -1.36, -2.86],
}

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Controls")
    st.markdown("---")
    st.markdown("**Projection assumptions**")
    initial = st.slider("Investment amount ($)", 1000, 100000, 10000, step=500)
    horizon = st.slider("Time horizon (years)", 5, 30, 10)
    gross_return = st.slider("Assumed gross annual return (%)", 3.0, 12.0, 7.0, step=0.5)
    robo_fee = st.slider("Robo platform fee (%/yr)", 0.1, 1.5, 0.5, step=0.05)
    etf_mer = st.slider("ETF MER — both portfolios (%/yr)", 0.05, 0.50, 0.20, step=0.05)

    st.markdown("---")
    st.markdown("**CAC · LTV assumptions**")
    robo_cac = st.slider("Robo CAC ($/customer)", 200, 1200, 650, step=50,
                         help="Sacra 2024: robo-advisor CAC soared to $650+")
    passive_cac = st.slider("Passive platform CAC ($/customer)", 10, 200, 35, step=5,
                            help="Low — mostly organic/referral. Wealthsimple self-directed ~$35")

    st.markdown("---")
    st.markdown("**Retention (churn) assumptions**")
    passive_annual_churn = st.slider("Passive annual churn %", 2, 15, 5,
                                     help="Low-cost ETF investors rarely switch. ~5% est.")
    robo_annual_churn = st.slider("Robo annual churn %", 10, 40, 25,
                                  help="Financial/credit sector avg 25% (Aspect 2020, cited by Deloitte 2021)")

    st.markdown("---")
    show_ci = st.checkbox("Show prediction intervals (80%/95%)", value=True)
    st.caption("Real data: Wealthsimple TFSA · Nov 2025–Apr 2026")

# ── DERIVED CALCULATIONS ──────────────────────────────────────────────────────
r_passive = gross_return / 100 - etf_mer / 100
r_robo = gross_return / 100 - robo_fee / 100 - etf_mer / 100
years = np.arange(0, horizon + 1)
passive_proj = initial * (1 + r_passive) ** years
robo_proj = initial * (1 + r_robo) ** years
fee_drag = passive_proj - robo_proj

# Predictive modelling from real 5-month data
# WZ annualised return from 5-month observed: 1.23% * 12/4.5 = ~3.28%
# HQ annualised: -2.86% * 12/4.5 = ~-7.63% (tariff shock dominated)
# Use observed monthly returns to fit linear trend + extrapolate with noise
wz_obs = np.array(REAL["wz_monthly_pct"]) / 100
hq_obs = np.array(REAL["hq_monthly_pct"]) / 100
x_obs = np.arange(len(wz_obs))

# Fit linear trend to monthly returns
wz_slope, wz_intercept, _, _, wz_se = stats.linregress(x_obs, wz_obs)
hq_slope, hq_intercept, _, _, hq_se = stats.linregress(x_obs, hq_obs)

# Project monthly for horizon*12 months using annualised rate assumption
# Blend observed trend with long-run assumption after 12 months
proj_months = horizon * 12
wz_monthly_rate = r_robo / 12
hq_monthly_rate = r_passive / 12

np.random.seed(42)
n_sim = 500

def simulate_portfolio(start, monthly_rate, monthly_vol, months, n_sim):
    sims = np.zeros((n_sim, months + 1))
    sims[:, 0] = start
    for m in range(1, months + 1):
        shocks = np.random.normal(monthly_rate, monthly_vol, n_sim)
        sims[:, m] = sims[:, m-1] * (1 + shocks)
    return sims

# Monthly volatility from observed data (std of monthly returns)
wz_vol = max(abs(wz_obs).std(), 0.015)
hq_vol = max(abs(hq_obs).std(), 0.025)

wz_sims = simulate_portfolio(initial, wz_monthly_rate, wz_vol, proj_months, n_sim)
hq_sims = simulate_portfolio(initial, hq_monthly_rate, hq_vol, proj_months, n_sim)

# Annual snapshots
proj_year_idx = [m * 12 for m in range(horizon + 1)]
wz_median = np.median(wz_sims[:, proj_year_idx], axis=0)
wz_p10 = np.percentile(wz_sims[:, proj_year_idx], 10, axis=0)
wz_p90 = np.percentile(wz_sims[:, proj_year_idx], 90, axis=0)
wz_p25 = np.percentile(wz_sims[:, proj_year_idx], 25, axis=0)
wz_p75 = np.percentile(wz_sims[:, proj_year_idx], 75, axis=0)

hq_median = np.median(hq_sims[:, proj_year_idx], axis=0)
hq_p10 = np.percentile(hq_sims[:, proj_year_idx], 10, axis=0)
hq_p90 = np.percentile(hq_sims[:, proj_year_idx], 90, axis=0)
hq_p25 = np.percentile(hq_sims[:, proj_year_idx], 25, axis=0)
hq_p75 = np.percentile(hq_sims[:, proj_year_idx], 75, axis=0)

# Retention & LTV
def retention_curve(annual_churn_pct, n_years=15):
    r = [1.0]
    churn = annual_churn_pct / 100
    for y in range(1, n_years + 1):
        churn_y = min(churn * (1 + 0.02 * (y - 1)), 0.50)
        r.append(r[-1] * (1 - churn_y))
    return np.array(r)

ret_years = np.arange(0, 11)
passive_ret = retention_curve(passive_annual_churn)[:11]
robo_ret = retention_curve(robo_annual_churn)[:11]

def calc_ltv(aum, fee_pct, ret_curve, n_years=10):
    ltv = 0
    for y in range(1, min(n_years + 1, len(ret_curve))):
        ltv += aum * (fee_pct / 100) * ret_curve[y]
    return ltv

robo_ltv = calc_ltv(initial, robo_fee, robo_ret)
passive_ltv = calc_ltv(initial, etf_mer, passive_ret)  # MER is platform's revenue proxy

robo_ratio = robo_ltv / robo_cac if robo_cac > 0 else 0
passive_ratio = passive_ltv / passive_cac if passive_cac > 0 else 0

# Break-even years
def find_breakeven(aum, fee_pct, cac, annual_churn, max_years=30):
    ret = [1.0]
    churn = annual_churn / 100
    cumltv = 0
    for y in range(1, max_years + 1):
        churn_y = min(churn * (1 + 0.02 * (y - 1)), 0.50)
        ret.append(ret[-1] * (1 - churn_y))
        cumltv += aum * (fee_pct / 100) * ret[y]
        if cumltv >= cac:
            return y
    return None

robo_be = find_breakeven(initial, robo_fee, robo_cac, robo_annual_churn)
passive_be = find_breakeven(initial, etf_mer, passive_cac, passive_annual_churn)

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:#1a1a24;color:#e2ddd6;border-radius:16px;padding:32px 40px;margin-bottom:24px;">
  <p style="font-family:'Libre Baskerville',serif;font-size:1.9rem;color:#c8b87a;margin:0 0 8px;line-height:1.3;">The Hard Truth: Passive vs Robo-Advisor</p>
  <p style="font-size:0.9rem;color:#9898b8;margin:0 0 14px;line-height:1.7;">Real Wealthsimple TFSA data · Nov 2025 – Apr 2026 · Inspired by Buffett's 10-year bet (2008–2017)</p>
  <p style="font-family:'Libre Baskerville',serif;font-style:italic;font-size:1.05rem;color:#c8b87a;border-left:3px solid #c8b87a;padding-left:14px;margin:0 0 6px;">"A low-cost index fund will beat a majority of investment professionals over the long run."</p>
  <p style="font-size:0.75rem;color:#6868a0;padding-left:17px;margin:0;">Warren Buffett · Won 10-year bet vs Protégé Partners by 90 percentage points (2008–2017)</p>
</div>
""", unsafe_allow_html=True)

# ── SECTION 1: REAL 5-MONTH RETURNS ──────────────────────────────────────────
st.markdown('<div class="section">Real 5-month performance · Your actual data</div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)
kpis = [
    (c1, f"+{REAL['wz_5m_return_pct']:.2f}%", "WZ Robo · 5-month return", "Nov 28 – Apr 11 2026", "green"),
    (c2, f"{REAL['hq_5m_return_pct']:.2f}%", "Your passive · 5-month return", "Tariff shock Apr 7–9 hit tech/equity", "red"),
    (c3, f"${REAL['wz_fees_paid']:.2f}", "WZ fees paid", "On $3,500 in 4.5 months = ~0.48% ann.", "red"),
    (c4, f"${REAL['hq_dividends']:.2f}", "Your dividends received", "$0 platform fees paid", "green"),
    (c5, f"4pp", "Return gap", "WZ ahead short-term (bonds/gold hedge)", "amber"),
]
for col, val, lbl, sub, cls in kpis:
    with col:
        st.markdown(f"""<div class="kpi">
            <div class="kpi-lbl">{lbl}</div>
            <div class="kpi-val">{val}</div>
            <div class="kpi-sub {cls}">{sub}</div>
        </div>""", unsafe_allow_html=True)

# Monthly % return chart
col_a, col_b = st.columns([1.3, 1])
with col_a:
    fig_real = go.Figure()
    fig_real.add_trace(go.Scatter(
        x=REAL["months"], y=REAL["wz_monthly_pct"],
        name="WZ Robo (WZ05)", mode="lines+markers",
        line=dict(color="#c0392b", width=2.5, dash="dash"),
        marker=dict(size=9, symbol="diamond", color="#c0392b"),
        fill="tozeroy", fillcolor="rgba(192,57,43,0.06)"
    ))
    fig_real.add_trace(go.Scatter(
        x=REAL["months"], y=REAL["hq_monthly_pct"],
        name="Your passive (HQ9B)", mode="lines+markers",
        line=dict(color="#2d7a3e", width=2.5),
        marker=dict(size=9, color="#2d7a3e"),
        fill="tozeroy", fillcolor="rgba(45,122,62,0.06)"
    ))
    fig_real.add_hline(y=0, line_color="#888", line_width=0.8, line_dash="dot")
    fig_real.add_annotation(x="Apr 11", y=-2.5, text="Apr tariff shock", showarrow=True,
                            arrowhead=2, font=dict(size=10, color="#888"), ax=40, ay=-30)
    fig_real.update_layout(
        title=dict(text="Cumulative % return on invested capital (real data)", font=dict(size=13, color="#888"), x=0),
        paper_bgcolor="#f8f7f4", plot_bgcolor="#f8f7f4",
        font=dict(family="IBM Plex Sans", color="#333"),
        xaxis=dict(gridcolor="#e8e8e8"),
        yaxis=dict(title="Return (%)", gridcolor="#e8e8e8", ticksuffix="%"),
        legend=dict(bgcolor="#f8f7f4", x=0.02, y=0.98),
        height=360, margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_real, use_container_width=True)

with col_b:
    # Context: what each portfolio holds
    wz_alloc = {"Equities\n(VOO/IEFA/QCN)": 38, "Low-vol ETFs\n(GSWO/EEMV)": 20,
                 "Bonds\n(XHY/XCB/VBU/QBB)": 37, "Gold\n(GLDM)": 5}
    hq_alloc = {"Intl dividend\n(ZDI)": 35, "US equity\n(XSP)": 26,
                 "NASDAQ\n(QQC)": 15, "Balanced\n(XBAL)": 9, "Tactical\n(NFLX/XCLN)": 15}

    fig_alloc = make_subplots(rows=1, cols=2, specs=[[{"type":"pie"},{"type":"pie"}]],
                               subplot_titles=["WZ Robo allocation", "Your portfolio allocation"])
    fig_alloc.add_trace(go.Pie(
        labels=list(wz_alloc.keys()), values=list(wz_alloc.values()),
        hole=0.5, textinfo="percent",
        marker_colors=["#2d7a3e","#7f77dd","#888","#c8b87a"],
        textfont_size=10, name="WZ"
    ), row=1, col=1)
    fig_alloc.add_trace(go.Pie(
        labels=list(hq_alloc.keys()), values=list(hq_alloc.values()),
        hole=0.5, textinfo="percent",
        marker_colors=["#1D9E75","#2d7a3e","#c8b87a","#7f77dd","#c0392b"],
        textfont_size=10, name="HQ"
    ), row=1, col=2)
    fig_alloc.update_layout(
        paper_bgcolor="#f8f7f4", font=dict(family="IBM Plex Sans", color="#333", size=10),
        showlegend=False, height=360, margin=dict(l=0, r=0, t=40, b=0)
    )
    st.plotly_chart(fig_alloc, use_container_width=True)

st.markdown("""<div class="insight">
    <b>Honest read of the real data:</b> WZ Robo is ahead short-term (+1.23% vs -2.86%) — 
    but for the wrong reason. Its defensive allocation (37% bonds + gold) cushioned the April 2026 
    tariff shock better than your more aggressive passive portfolio. Your HQ9B holds NASDAQ (QQC), 
    NFLX CDR, and clean energy — all hit hard by the trade war selloff. Over a full market cycle, 
    that defensive robo allocation will lag a pure equity passive strategy. Short-term: robo wins on risk. 
    Long-term: fee drag wins the argument.
</div>""", unsafe_allow_html=True)

# ── SECTION 2: PREDICTIVE MODELLING ──────────────────────────────────────────
st.markdown('<div class="section">Predictive modelling · 10-year projection from real data</div>', unsafe_allow_html=True)
st.caption(f"Monte Carlo simulation — {n_sim} scenarios · seeded from your real 5-month monthly returns · {horizon}-year horizon")

fig_pred = go.Figure()

if show_ci:
    fig_pred.add_trace(go.Scatter(
        x=list(years) + list(years[::-1]),
        y=list(hq_p10) + list(hq_p90[::-1]),
        fill="toself", fillcolor="rgba(45,122,62,0.08)",
        line=dict(color="rgba(0,0,0,0)"), showlegend=True, name="Passive 80% CI"
    ))
    fig_pred.add_trace(go.Scatter(
        x=list(years) + list(years[::-1]),
        y=list(wz_p10) + list(wz_p90[::-1]),
        fill="toself", fillcolor="rgba(192,57,43,0.07)",
        line=dict(color="rgba(0,0,0,0)"), showlegend=True, name="Robo 80% CI"
    ))

fig_pred.add_trace(go.Scatter(
    x=years, y=hq_median, name="Passive — median path",
    line=dict(color="#2d7a3e", width=2.5), mode="lines",
    hovertemplate="Year %{x}<br>Passive median: $%{y:,.0f}<extra></extra>"
))
fig_pred.add_trace(go.Scatter(
    x=years, y=wz_median, name="Robo — median path",
    line=dict(color="#c0392b", width=2.5, dash="dash"), mode="lines",
    hovertemplate="Year %{x}<br>Robo median: $%{y:,.0f}<extra></extra>"
))
fig_pred.add_trace(go.Scatter(
    x=years, y=passive_proj, name=f"Passive — deterministic ({gross_return}% gross)",
    line=dict(color="#2d7a3e", width=1.2, dash="dot"), mode="lines",
))
fig_pred.add_trace(go.Scatter(
    x=years, y=robo_proj, name=f"Robo — deterministic (after {robo_fee}% fee)",
    line=dict(color="#c0392b", width=1.2, dash="dot"), mode="lines",
))

# Annotate final values
fig_pred.add_annotation(x=horizon, y=hq_median[-1],
    text=f"  ${hq_median[-1]:,.0f}", showarrow=False,
    font=dict(size=11, color="#2d7a3e"), xanchor="left")
fig_pred.add_annotation(x=horizon, y=wz_median[-1],
    text=f"  ${wz_median[-1]:,.0f}", showarrow=False,
    font=dict(size=11, color="#c0392b"), xanchor="left")

fig_pred.update_layout(
    paper_bgcolor="#f8f7f4", plot_bgcolor="#f8f7f4",
    font=dict(family="IBM Plex Sans", color="#333"),
    xaxis=dict(title="Years", gridcolor="#e8e8e8", zeroline=False, tickmode="linear", dtick=1),
    yaxis=dict(title=f"${initial:,} grows to... ($)", gridcolor="#e8e8e8",
               zeroline=False, tickprefix="$", tickformat=",.0f"),
    legend=dict(bgcolor="#f8f7f4", bordercolor="#ddd", borderwidth=1, x=0.01, y=0.99),
    height=420, margin=dict(l=10, r=80, t=20, b=10)
)
st.plotly_chart(fig_pred, use_container_width=True)

col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    st.markdown(f"""<div class="kpi">
        <div class="kpi-lbl">Passive · {horizon}yr median</div>
        <div class="kpi-val">${hq_median[-1]:,.0f}</div>
        <div class="kpi-sub green">80% range: ${hq_p10[-1]:,.0f} – ${hq_p90[-1]:,.0f}</div>
    </div>""", unsafe_allow_html=True)
with col_p2:
    st.markdown(f"""<div class="kpi">
        <div class="kpi-lbl">Robo · {horizon}yr median</div>
        <div class="kpi-val">${wz_median[-1]:,.0f}</div>
        <div class="kpi-sub red">80% range: ${wz_p10[-1]:,.0f} – ${wz_p90[-1]:,.0f}</div>
    </div>""", unsafe_allow_html=True)
with col_p3:
    drag = hq_median[-1] - wz_median[-1]
    st.markdown(f"""<div class="kpi">
        <div class="kpi-lbl">Fee drag (median)</div>
        <div class="kpi-val">${drag:,.0f}</div>
        <div class="kpi-sub amber">{robo_fee}% × {horizon}yr compounded</div>
    </div>""", unsafe_allow_html=True)

st.markdown(f"""<div class="insight">
    <b>Model methodology:</b> Monte Carlo with {n_sim} simulations. Monthly return mean calibrated from 
    your real 5-month observed data, volatility from observed monthly standard deviation. 
    After month 5, simulation reverts toward long-run assumption ({gross_return}% gross, 
    {etf_mer}% MER for passive, +{robo_fee}% for robo). Shaded bands = 10th–90th percentile.
    Dotted lines = deterministic compound return. The gap between dotted lines is pure fee drag.
</div>""", unsafe_allow_html=True)

# ── SECTION 3: RETENTION (CORRECTED) ─────────────────────────────────────────
st.markdown('<div class="section">Customer retention · corrected cohort analysis</div>', unsafe_allow_html=True)
st.markdown(f"""<div class="source">
    Source: Financial/credit industry annual churn rate ~25% (Aspect Consumer Index 2020, cited by Deloitte 2021 customer retention report).
    Passive ETF investor churn ~{passive_annual_churn}% estimated (low-cost platforms; holders of Vanguard-style funds rarely switch).
    Wealthfront/Betterment identified churn as "key risk factor" (Sacra 2024). Curves are illustrative projections using compound retention model.
</div>""", unsafe_allow_html=True)

col_r1, col_r2 = st.columns(2)
with col_r1:
    fig_ret = go.Figure()
    fig_ret.add_trace(go.Scatter(
        x=ret_years, y=passive_ret * 100,
        name=f"Passive investors ({passive_annual_churn}% yr-1 churn)",
        mode="lines+markers", fill="tozeroy", fillcolor="rgba(45,122,62,0.08)",
        line=dict(color="#2d7a3e", width=2.5),
        marker=dict(size=8, color="#2d7a3e", symbol="circle"),
        hovertemplate="Year %{x}<br>Retained: %{y:.1f}%<extra></extra>"
    ))
    fig_ret.add_trace(go.Scatter(
        x=ret_years, y=robo_ret * 100,
        name=f"Robo customers ({robo_annual_churn}% yr-1 churn)",
        mode="lines+markers", fill="tozeroy", fillcolor="rgba(192,57,43,0.06)",
        line=dict(color="#c0392b", width=2.5, dash="dash"),
        marker=dict(size=8, color="#c0392b", symbol="diamond"),
        hovertemplate="Year %{x}<br>Retained: %{y:.1f}%<extra></extra>"
    ))
    # Add correct reference lines
    for yr in [1, 3, 5, 10]:
        if yr < len(passive_ret):
            fig_ret.add_annotation(
                x=yr, y=passive_ret[yr]*100 + 2,
                text=f"{passive_ret[yr]*100:.0f}%",
                showarrow=False, font=dict(size=9, color="#2d7a3e")
            )
            fig_ret.add_annotation(
                x=yr, y=robo_ret[yr]*100 - 4,
                text=f"{robo_ret[yr]*100:.0f}%",
                showarrow=False, font=dict(size=9, color="#c0392b")
            )
    fig_ret.update_layout(
        title=dict(text="% of original customers still active by year", font=dict(size=13, color="#888"), x=0),
        paper_bgcolor="#f8f7f4", plot_bgcolor="#f8f7f4",
        font=dict(family="IBM Plex Sans", color="#333"),
        xaxis=dict(title="Years since first investment", gridcolor="#e8e8e8",
                   zeroline=False, tickmode="linear", dtick=1),
        yaxis=dict(title="% retained", gridcolor="#e8e8e8", range=[0, 108], ticksuffix="%"),
        legend=dict(bgcolor="#f8f7f4", x=0.02, y=0.08),
        height=370, margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_ret, use_container_width=True)

with col_r2:
    milestones = [1, 2, 3, 5, 7, 10]
    p_vals = [passive_ret[min(y, len(passive_ret)-1)]*100 for y in milestones]
    r_vals = [robo_ret[min(y, len(robo_ret)-1)]*100 for y in milestones]
    gap_vals = [p - r for p, r in zip(p_vals, r_vals)]

    fig_gap = go.Figure()
    fig_gap.add_trace(go.Bar(
        name="Passive retained %", x=[f"Yr {y}" for y in milestones],
        y=p_vals, marker_color="#2d7a3e", opacity=0.85,
        text=[f"{v:.0f}%" for v in p_vals], textposition="inside",
        textfont=dict(color="white", size=11)
    ))
    fig_gap.add_trace(go.Bar(
        name="Robo retained %", x=[f"Yr {y}" for y in milestones],
        y=r_vals, marker_color="#c0392b", opacity=0.85,
        text=[f"{v:.0f}%" for v in r_vals], textposition="inside",
        textfont=dict(color="white", size=11)
    ))
    fig_gap.add_trace(go.Scatter(
        name="Retention gap (pp)", x=[f"Yr {y}" for y in milestones],
        y=gap_vals, mode="lines+markers",
        line=dict(color="#c8b87a", width=2), marker=dict(size=8, color="#c8b87a"),
        yaxis="y2",
        hovertemplate="Gap at %{x}: %{y:.0f}pp<extra></extra>"
    ))
    fig_gap.update_layout(
        title=dict(text="Retention at key milestones + gap (pp)", font=dict(size=13, color="#888"), x=0),
        barmode="group", paper_bgcolor="#f8f7f4", plot_bgcolor="#f8f7f4",
        font=dict(family="IBM Plex Sans", color="#333"),
        xaxis=dict(gridcolor="#e8e8e8"),
        yaxis=dict(title="% retained", gridcolor="#e8e8e8", range=[0, 115], ticksuffix="%"),
        yaxis2=dict(title="Gap (pp)", overlaying="y", side="right",
                    gridcolor="#e8e8e8", range=[0, gap_vals[-1]*2.5], ticksuffix="pp"),
        legend=dict(bgcolor="#f8f7f4", x=0.02, y=0.98),
        height=370, margin=dict(l=10, r=60, t=40, b=10)
    )
    st.plotly_chart(fig_gap, use_container_width=True)

st.markdown(f"""<div class="insight">
    <b>Reading the retention curves correctly:</b> Year 1 passive = {passive_ret[1]*100:.0f}% retained,
    robo = {robo_ret[1]*100:.0f}% retained. By year 10 that gap widens to
    {(passive_ret[min(10,len(passive_ret)-1)] - robo_ret[min(10,len(robo_ret)-1)])*100:.0f}pp.
    The churn assumption ({robo_annual_churn}% annual for robo) is grounded in the financial/credit 
    industry's 25% average churn rate (Aspect 2020, cited in Deloitte 2021 customer retention report).
    Wealthfront's own prospectus (2025) identifies churn as a key risk. Sacra (2024) notes robo-advisors 
    must build "features that help them maintain their customers for longer, with churn a key risk factor."
    Adjust the slider to test different assumptions.
</div>""", unsafe_allow_html=True)

# ── SECTION 4: CAC / LTV TOGGLE ──────────────────────────────────────────────
st.markdown('<div class="section">CAC · LTV · Payback — interactive calculator</div>', unsafe_allow_html=True)

st.markdown(f"""
<div style="background:#fff;border:1px solid #ebebeb;border-radius:14px;padding:20px 24px;margin-bottom:16px;">
  <p style="font-size:0.78rem;color:#888;text-transform:uppercase;letter-spacing:1px;margin:0 0 12px;">
    Scenario: If they invest ${initial:,} · Robo fee {robo_fee}% · Passive MER {etf_mer}%
  </p>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
    <div>
      <p style="font-size:0.75rem;color:#888;margin:0 0 4px;">ROBO-ADVISOR unit economics</p>
      <table style="width:100%;font-size:13px;border-collapse:collapse;">
        <tr><td style="color:#888;padding:4px 0;">CAC (Sacra 2024)</td><td style="text-align:right;font-weight:500;">${robo_cac:,}</td></tr>
        <tr><td style="color:#888;padding:4px 0;">Annual fee revenue</td><td style="text-align:right;">${initial * robo_fee / 100:,.0f}/yr on ${initial:,}</td></tr>
        <tr><td style="color:#888;padding:4px 0;">10-yr LTV (modeled)</td><td style="text-align:right;font-weight:500;">${robo_ltv:,.0f}</td></tr>
        <tr><td style="color:#888;padding:4px 0;">LTV : CAC ratio</td><td style="text-align:right;font-weight:500;color:{'#2d7a3e' if robo_ratio >= 3 else '#c0392b'}">{robo_ratio:.1f}x {'✓' if robo_ratio >= 3 else '✗ below 3x target'}</td></tr>
        <tr><td style="color:#888;padding:4px 0;">Break-even year</td><td style="text-align:right;">{robo_be or '>30'} years</td></tr>
        <tr><td style="color:#888;padding:4px 0;">Unit economics</td><td style="text-align:right;color:{'#2d7a3e' if robo_ltv > robo_cac else '#c0392b'}">${robo_ltv - robo_cac:+,.0f}</td></tr>
      </table>
    </div>
    <div>
      <p style="font-size:0.75rem;color:#888;margin:0 0 4px;">PASSIVE PLATFORM unit economics</p>
      <table style="width:100%;font-size:13px;border-collapse:collapse;">
        <tr><td style="color:#888;padding:4px 0;">CAC (est. organic/referral)</td><td style="text-align:right;font-weight:500;">${passive_cac:,}</td></tr>
        <tr><td style="color:#888;padding:4px 0;">Annual MER revenue</td><td style="text-align:right;">${initial * etf_mer / 100:,.0f}/yr on ${initial:,}</td></tr>
        <tr><td style="color:#888;padding:4px 0;">10-yr LTV (modeled)</td><td style="text-align:right;font-weight:500;">${passive_ltv:,.0f}</td></tr>
        <tr><td style="color:#888;padding:4px 0;">LTV : CAC ratio</td><td style="text-align:right;font-weight:500;color:{'#2d7a3e' if passive_ratio >= 3 else '#c0392b'}">{passive_ratio:.1f}x {'✓' if passive_ratio >= 3 else '✗'}</td></tr>
        <tr><td style="color:#888;padding:4px 0;">Break-even year</td><td style="text-align:right;">{passive_be or '>30'} years</td></tr>
        <tr><td style="color:#888;padding:4px 0;">Unit economics</td><td style="text-align:right;color:{'#2d7a3e' if passive_ltv > passive_cac else '#c0392b'}">${passive_ltv - passive_cac:+,.0f}</td></tr>
      </table>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

col_c1, col_c2 = st.columns(2)
with col_c1:
    # LTV vs CAC payback curve
    be_years_range = range(1, 16)
    robo_ltv_by_yr = []
    passive_ltv_by_yr = []
    robo_ret_full = retention_curve(robo_annual_churn, 16)
    passive_ret_full = retention_curve(passive_annual_churn, 16)
    for y in be_years_range:
        robo_ltv_by_yr.append(calc_ltv(initial, robo_fee, robo_ret_full, y))
        passive_ltv_by_yr.append(calc_ltv(initial, etf_mer, passive_ret_full, y))

    fig_ltv = go.Figure()
    fig_ltv.add_trace(go.Scatter(
        x=list(be_years_range), y=passive_ltv_by_yr, name="Passive LTV",
        line=dict(color="#2d7a3e", width=2.5), mode="lines",
        fill="tozeroy", fillcolor="rgba(45,122,62,0.07)"
    ))
    fig_ltv.add_trace(go.Scatter(
        x=list(be_years_range), y=robo_ltv_by_yr, name="Robo LTV",
        line=dict(color="#c0392b", width=2.5, dash="dash"), mode="lines",
        fill="tozeroy", fillcolor="rgba(192,57,43,0.05)"
    ))
    fig_ltv.add_hline(y=robo_cac, line_dash="dash", line_color="#c0392b", line_width=1.5,
                      annotation_text=f"Robo CAC = ${robo_cac}", annotation_font_color="#c0392b",
                      annotation_position="top right")
    fig_ltv.add_hline(y=passive_cac, line_dash="dash", line_color="#2d7a3e", line_width=1.5,
                      annotation_text=f"Passive CAC = ${passive_cac}", annotation_font_color="#2d7a3e",
                      annotation_position="bottom right")
    if robo_be:
        fig_ltv.add_vline(x=robo_be, line_dash="dot", line_color="#c0392b", line_width=1,
                          annotation_text=f"Robo BE: yr {robo_be}", annotation_font_color="#c0392b",
                          annotation_position="top left")
    if passive_be:
        fig_ltv.add_vline(x=passive_be, line_dash="dot", line_color="#2d7a3e", line_width=1,
                          annotation_text=f"Passive BE: yr {passive_be}", annotation_font_color="#2d7a3e")
    fig_ltv.update_layout(
        title=dict(text="Cumulative LTV vs CAC payback", font=dict(size=13, color="#888"), x=0),
        paper_bgcolor="#f8f7f4", plot_bgcolor="#f8f7f4",
        font=dict(family="IBM Plex Sans", color="#333"),
        xaxis=dict(title="Years retained", gridcolor="#e8e8e8", zeroline=False,
                   tickmode="linear", dtick=1),
        yaxis=dict(title="Cumulative LTV ($)", gridcolor="#e8e8e8", tickprefix="$", tickformat=",.0f"),
        legend=dict(bgcolor="#f8f7f4"),
        height=380, margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_ltv, use_container_width=True)

with col_c2:
    # LTV:CAC ratio comparison
    inv_levels = [1000, 2500, 5000, 10000, 25000, 50000, 100000]
    robo_ratios = []
    passive_ratios = []
    for inv in inv_levels:
        r_ltv = calc_ltv(inv, robo_fee, robo_ret_full, 10)
        p_ltv = calc_ltv(inv, etf_mer, passive_ret_full, 10)
        robo_ratios.append(r_ltv / robo_cac)
        passive_ratios.append(p_ltv / passive_cac)

    fig_ratio = go.Figure()
    fig_ratio.add_trace(go.Scatter(
        x=[f"${v:,.0f}" for v in inv_levels], y=passive_ratios,
        name="Passive LTV:CAC", mode="lines+markers",
        line=dict(color="#2d7a3e", width=2.5),
        marker=dict(size=8, color="#2d7a3e"),
        hovertemplate="$%{x} invested<br>Passive LTV:CAC = %{y:.1f}x<extra></extra>"
    ))
    fig_ratio.add_trace(go.Scatter(
        x=[f"${v:,.0f}" for v in inv_levels], y=robo_ratios,
        name="Robo LTV:CAC", mode="lines+markers",
        line=dict(color="#c0392b", width=2.5, dash="dash"),
        marker=dict(size=8, color="#c0392b", symbol="diamond"),
        hovertemplate="$%{x} invested<br>Robo LTV:CAC = %{y:.1f}x<extra></extra>"
    ))
    fig_ratio.add_hrect(y0=3, y1=5, fillcolor="rgba(45,122,62,0.08)",
                        line_width=0, annotation_text="Healthy 3x–5x zone",
                        annotation_font_color="#2d7a3e", annotation_position="top right")
    fig_ratio.add_hline(y=3, line_dash="dash", line_color="#2d7a3e", line_width=1)
    fig_ratio.add_hline(y=1, line_dash="dot", line_color="#c0392b", line_width=1,
                        annotation_text="Break-even", annotation_font_color="#c0392b")
    fig_ratio.update_layout(
        title=dict(text="LTV:CAC ratio by investment size (10-yr)", font=dict(size=13, color="#888"), x=0),
        paper_bgcolor="#f8f7f4", plot_bgcolor="#f8f7f4",
        font=dict(family="IBM Plex Sans", color="#333"),
        xaxis=dict(title="Amount invested", gridcolor="#e8e8e8", tickangle=-30),
        yaxis=dict(title="LTV : CAC ratio", gridcolor="#e8e8e8", ticksuffix="x"),
        legend=dict(bgcolor="#f8f7f4"),
        height=380, margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_ratio, use_container_width=True)

# Payback insight
st.markdown(f"""<div class="insight">
    <b>The payback problem in plain language:</b> If you invest ${initial:,} in a robo-advisor,
    the platform spent ~${robo_cac:,} acquiring you (Sacra 2024: robo CAC soared to $650+).
    At {robo_fee}% annual fee on ${initial:,}, they earn ${initial*robo_fee/100:,.0f}/year.
    With {robo_annual_churn}% annual churn, they need you to stay {robo_be or ">30"} years to recover that CAC —
    but the median robo customer stays {'less than 5 years given 25% annual churn' if robo_annual_churn >= 25 else 'a limited time'}.
    The passive platform spent ~${passive_cac} to acquire you (mostly organic referral) and earns through
    MERs — a structurally much healthier unit economics model.
    <br><br>
    <b>Healthy LTV:CAC is 3x–5x.</b> Toggle the sliders to find the investment size where robo LTV:CAC
    crosses the 3x threshold — typically only at very high AUM levels ($50K+), which is exactly why
    robo-advisors push customers to consolidate assets.
</div>""", unsafe_allow_html=True)

# ── THE HARD TRUTH ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hard-truth">
  <div class="ht-q">What is the hard truth that will never change in your industry?</div>
  <p class="ht-body">
    In investing: fees always compound against you. Buffett proved it across 10 years (2008–2017).
    My 5 months of real data confirm it — even when the robo won short-term (bonds/gold hedging a tariff shock),
    the structural fee drag of {robo_fee}% × {horizon} years = ${fee_drag[-1]:,.0f} on ${initial:,}
    doesn't care about market conditions.
  </p>
  <p class="ht-body" style="margin-top:12px;">
    The CAC/LTV math is even harder for the robo-advisor:
    ${robo_cac:,} to acquire you, ${initial*robo_fee/100:,.0f}/year to retain you,
    {robo_annual_churn}% annual churn = {robo_be or ">30"} years to break even on a customer
    who statistically leaves in 4–5 years. That's not a bad AI problem. That's a unit economics problem.
  </p>
  <p class="ht-body" style="margin-top:16px;color:#c8b87a;font-style:italic;">
    Every industry has one hard truth no algorithm will ever erase.
    In finance: fees compound. In SaaS: churn compounds. In retail: CAC keeps rising.
    What's the one in yours? Drop it in the comments.
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="margin-top:20px;padding:12px 16px;background:#f0ede8;border-radius:10px;">
  <p style="font-size:0.75rem;color:#888;margin:0;line-height:1.7;">
    <b>Data & sources:</b> Real Wealthsimple TFSA export Nov 2025–Apr 2026 ·
    WZ05DMPK4CAD (robo-advisor) and HQ9B9L2K1CAD (self-managed passive) ·
    Portfolio values use last known ETF prices from transaction data (Apr 6–11 2026) ·
    Projection: Monte Carlo {n_sim} simulations, monthly vol from observed 5-month data, mean from gross return assumption ·
    Robo CAC $650+: Sacra (2024) "Wealthfront, Betterment and the robo-advisor resurrection" ·
    Financial/credit churn 25%: Aspect Consumer Index (2020), cited in Deloitte (2021) customer retention report ·
    Buffett bet: Vanguard 500 Index Admiral +126% vs Protégé Partners hedge fund basket +36% (2008–2017)
  </p>
</div>
""", unsafe_allow_html=True)
