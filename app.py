"""
The Hard Truth: Passive vs Robo-Advisor
Real Wealthsimple data · Nov 2025 – Apr 2026
Inspired by Warren Buffett's 10-year bet (2008–2017)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

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

.serif { font-family: 'Libre Baskerville', serif; }

.hero { background: #1a1a24; color: #e2ddd6; border-radius: 16px; padding: 36px 40px; margin-bottom: 28px; }
.hero-title { font-family: 'Libre Baskerville', serif; font-size: 2rem; color: #e2ddd6; margin: 0 0 10px; line-height: 1.3; }
.hero-sub { font-size: 0.95rem; color: #9898b8; margin: 0; line-height: 1.7; }
.buffett-quote { font-family: 'Libre Baskerville', serif; font-style: italic; font-size: 1.1rem; color: #c8b87a; margin: 16px 0 6px; border-left: 3px solid #c8b87a; padding-left: 16px; }
.buffett-attr { font-size: 0.78rem; color: #6868a0; margin: 0; padding-left: 19px; }

.kpi { background: #fff; border: 1px solid #ebebeb; border-radius: 14px; padding: 20px 22px; }
.kpi-lbl { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1.5px; color: #888; margin-bottom: 4px; }
.kpi-val { font-family: 'Libre Baskerville', serif; font-size: 1.9rem; color: #1a1a24; }
.kpi-sub { font-size: 0.82rem; margin-top: 4px; }
.green { color: #2d7a3e; } .red { color: #c0392b; } .amber { color: #b8860b; } .gray { color: #888; }

.section { font-family: 'Libre Baskerville', serif; font-size: 1.2rem; color: #1a1a24;
           border-bottom: 2px solid #c8b87a; padding-bottom: 6px; margin: 32px 0 16px; }
.insight { background: #fffbf0; border-left: 4px solid #c8b87a; border-radius: 0 10px 10px 0;
           padding: 14px 18px; font-size: 0.88rem; color: #444; line-height: 1.7; margin: 12px 0; }
.hard-truth { background: #1a1a24; color: #e2ddd6; border-radius: 14px; padding: 28px 32px; margin-top: 28px; }
.ht-q { font-family: 'Libre Baskerville', serif; font-size: 1.4rem; color: #c8b87a; margin: 0 0 12px; line-height: 1.4; }
.ht-body { font-size: 0.9rem; color: #9898b8; line-height: 1.75; margin: 0; }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Assumptions")
    st.markdown("---")
    initial = st.slider("Initial investment ($)", 1000, 500000, 10000, step=500)
    gross_return = st.slider("Gross annual return (%)", 3.0, 12.0, 7.0, step=0.5)
    robo_fee = st.slider("Robo-advisor fee (%/yr)", 0.1, 1.5, 0.5, step=0.1)
    etf_mer = st.slider("ETF MER — both portfolios (%/yr)", 0.05, 0.5, 0.20, step=0.05)
    horizon = st.slider("Time horizon (years)", 1, 30, 10)
    st.markdown("---")
    robo_cac = st.slider("Robo CAC ($/customer)", 100, 800, 400, step=50)
    robo_aum_fee_pct = robo_fee / 100
    st.markdown("---")
    st.markdown("**Churn assumptions**")
    passive_yr1_churn = st.slider("Passive yr-1 churn %", 1, 20, 5)
    robo_yr1_churn = st.slider("Robo yr-1 churn %", 1, 20, 5)
    st.markdown("---")

# ── CALCULATIONS ──────────────────────────────────────────────────────────────
r_gross = gross_return / 100
r_passive = r_gross - etf_mer / 100
r_robo = r_gross - robo_fee / 100 - etf_mer / 100

years = np.arange(0, horizon + 1)
passive_val = initial * (1 + r_passive) ** years
robo_val = initial * (1 + r_robo) ** years
fee_drag = passive_val - robo_val

passive_final = passive_val[-1]
robo_final = robo_val[-1]
total_drag = fee_drag[-1]
total_fees = initial * ((1 + r_passive) ** horizon - (1 + r_robo) ** horizon)

# Cohort retention
def retention_curve(yr1_churn, base_annual_add=0.02, years=10):
    ret = [1.0]
    churn = yr1_churn / 100
    for y in range(1, years + 1):
        churn_y = min(churn + base_annual_add * (y - 1), 0.35)
        ret.append(ret[-1] * (1 - churn_y))
    return np.array(ret)

passive_ret = retention_curve(passive_yr1_churn, base_annual_add=0.01)
robo_ret = retention_curve(robo_yr1_churn, base_annual_add=0.025)
ret_years = np.arange(0, 11)

# LTV calculation
def calc_ltv(initial_aum, fee_pct, retention_curve, years=10):
    ltv = 0
    for y in range(1, years + 1):
        if y <= len(retention_curve) - 1:
            ltv += initial_aum * fee_pct * retention_curve[y]
    return ltv

robo_ltv = calc_ltv(initial, robo_aum_fee_pct, robo_ret)
robo_unit_econ = robo_ltv - robo_cac
breakeven_yr = None
for y in range(1, 31):
    rv = np.array([retention_curve(robo_yr1_churn, 0.025, y)])
    ltv_y = calc_ltv(initial, robo_aum_fee_pct, rv[0], y)
    if ltv_y >= robo_cac:
        breakeven_yr = y
        break

# Alpha needed
alpha_needed = robo_fee + etf_mer

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
  <div class="hero-title">The Hard Truth: Passive vs Robo-Advisor</div>
  <div class="hero-sub">Inspired by Buffett's 10-year bet (2008–2017)</div>
  <div class="buffett-quote">"A low-cost index fund will beat a majority of investment professionals over the long run."</div>
  <div class="buffett-attr">Warren Buffett won the 10-year bet vs Protégé Partners by 90 percentage points</div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
kpis = [
    (c1, f"${passive_final:,.0f}", "Passive portfolio", f"${initial:,} over {horizon}yr", "green"),
    (c2, f"${robo_final:,.0f}",    "Robo-advisor",      f"After {robo_fee}% annual fee", "red"),
    (c3, f"${total_drag:,.0f}",    "Fee drag cost",     f"Over {horizon} years", "red"),
    (c4, f"{robo_ltv/robo_cac:.1f}x", "Robo LTV:CAC",  f"${robo_cac} CAC to recover", "amber" if robo_ltv/robo_cac >= 1 else "red"),
    (c5, f"{breakeven_yr or '>30'}yr", "Break-even horizon", "Yrs to recover CAC", "gray"),
]
for col, val, lbl, sub, cls in kpis:
    with col:
        st.markdown(f"""<div class="kpi">
            <div class="kpi-lbl">{lbl}</div>
            <div class="kpi-val">{val}</div>
            <div class="kpi-sub {cls}">{sub}</div>
        </div>""", unsafe_allow_html=True)

# ── SECTION 1: GROWTH ─────────────────────────────────────────────────────────
st.markdown('<div class="section">$10,000 portfolio growth comparison</div>', unsafe_allow_html=True)

col_a, col_b = st.columns([1.4, 1])

with col_a:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=years, y=passive_val, name="Passive (no platform fee)",
        line=dict(color="#2d7a3e", width=2.5),
        mode="lines", fill="tozeroy", fillcolor="rgba(45,122,62,0.06)"
    ))
    fig1.add_trace(go.Scatter(
        x=years, y=robo_val, name=f"Robo-advisor ({robo_fee}% fee)",
        line=dict(color="#c0392b", width=2.5, dash="dash"),
        mode="lines", fill="tozeroy", fillcolor="rgba(192,57,43,0.04)"
    ))
    fig1.add_trace(go.Scatter(
        x=years, y=fee_drag, name="Fee drag gap",
        line=dict(color="#c8b87a", width=1.5, dash="dot"),
        mode="lines",
    ))
    fig1.add_annotation(
        x=horizon, y=passive_final,
        text=f"  ${passive_final:,.0f}", showarrow=False,
        font=dict(size=12, color="#2d7a3e"), xanchor="left"
    )
    fig1.add_annotation(
        x=horizon, y=robo_final,
        text=f"  ${robo_final:,.0f}", showarrow=False,
        font=dict(size=12, color="#c0392b"), xanchor="left"
    )
    fig1.update_layout(
        paper_bgcolor="#f8f7f4", plot_bgcolor="#f8f7f4",
        font=dict(family="IBM Plex Sans", color="#333"),
        xaxis=dict(title="Years", gridcolor="#e8e8e8", zeroline=False, tickmode="linear", dtick=2),
        yaxis=dict(title="Portfolio value ($)", gridcolor="#e8e8e8", zeroline=False,
                   tickformat="$,.0f"),
        legend=dict(bgcolor="#f8f7f4", bordercolor="#ddd", borderwidth=1, x=0.02, y=0.98),
        height=380, margin=dict(l=10, r=60, t=20, b=10),
        showlegend=True
    )
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    buffett_data = {
        "Strategy": ["S&P 500\n(Vanguard)", "Hedge funds\n(Protégé)"],
        "Return": [126, 36],
        "Colors": ["#2d7a3e", "#c0392b"]
    }
    fig2 = go.Figure(go.Bar(
        x=buffett_data["Strategy"], y=buffett_data["Return"],
        marker_color=buffett_data["Colors"],
        text=[f"+{v}%" for v in buffett_data["Return"]],
        textposition="outside", textfont=dict(size=14, color="#333"),
        width=0.5
    ))
    fig2.add_annotation(
        x=0.5, y=90, xref="paper",
        text="Buffett's 10-year bet<br>2008–2017", showarrow=False,
        font=dict(size=11, color="#888"), align="center"
    )
    fig2.update_layout(
        title=dict(text="The original proof", font=dict(size=13, color="#888"), x=0),
        paper_bgcolor="#f8f7f4", plot_bgcolor="#f8f7f4",
        font=dict(family="IBM Plex Sans", color="#333"),
        xaxis=dict(gridcolor="#e8e8e8"),
        yaxis=dict(title="10-year return (%)", gridcolor="#e8e8e8", range=[0, 155]),
        height=380, margin=dict(l=10, r=10, t=40, b=10), showlegend=False
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown(f"""<div class="insight">
    With a ${initial:,} investment at {gross_return}% gross return over {horizon} years:
    the passive portfolio grows to <b>${passive_final:,.0f}</b> vs the robo-advisor's <b>${robo_final:,.0f}</b>.
    The {robo_fee}% annual fee, which seems tiny but compounds into a <b>${total_drag:,.0f} drag</b>.
    That's not the robo failing at investing. That's just math. Fees always compound against you.
</div>""", unsafe_allow_html=True)

# ── SECTION 2: COHORT RETENTION ────────────────────────────────────────────────
st.markdown('<div class="section">Cohort retention - who stays longer?</div>', unsafe_allow_html=True)

col_c, col_d = st.columns(2)

with col_c:
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=ret_years, y=passive_ret * 100,
        name="Passive investors", mode="lines+markers",
        line=dict(color="#2d7a3e", width=2.5),
        marker=dict(size=7, color="#2d7a3e"),
        fill="tozeroy", fillcolor="rgba(45,122,62,0.07)"
    ))
    fig3.add_trace(go.Scatter(
        x=ret_years, y=robo_ret * 100,
        name="Robo-advisor customers", mode="lines+markers",
        line=dict(color="#c0392b", width=2.5, dash="dash"),
        marker=dict(size=7, symbol="diamond", color="#c0392b"),
        fill="tozeroy", fillcolor="rgba(192,57,43,0.05)"
    ))
    fig3.update_layout(
        title=dict(text="Customer retention by year", font=dict(size=13, color="#888"), x=0),
        paper_bgcolor="#f8f7f4", plot_bgcolor="#f8f7f4",
        font=dict(family="IBM Plex Sans", color="#333"),
        xaxis=dict(title="Years since acquisition", gridcolor="#e8e8e8", zeroline=False,
                   tickmode="linear", dtick=1),
        yaxis=dict(title="% still active", gridcolor="#e8e8e8", range=[0, 105], ticksuffix="%"),
        legend=dict(bgcolor="#f8f7f4", x=0.02, y=0.05),
        height=340, margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig3, use_container_width=True)

with col_d:
    yr10_passive = passive_ret[min(10, len(passive_ret)-1)] * 100
    yr10_robo = robo_ret[min(10, len(robo_ret)-1)] * 100
    yr5_passive = passive_ret[min(5, len(passive_ret)-1)] * 100
    yr5_robo = robo_ret[min(5, len(robo_ret)-1)] * 100

    fig4 = go.Figure()
    cats = ["Year 1", "Year 3", "Year 5", "Year 10"]
    p_vals = [passive_ret[min(y, len(passive_ret)-1)]*100 for y in [1,3,5,10]]
    r_vals = [robo_ret[min(y, len(robo_ret)-1)]*100 for y in [1,3,5,10]]

    fig4.add_trace(go.Bar(name="Passive", x=cats, y=p_vals, marker_color="#2d7a3e",
                          opacity=0.85, text=[f"{v:.0f}%" for v in p_vals], textposition="outside"))
    fig4.add_trace(go.Bar(name="Robo", x=cats, y=r_vals, marker_color="#c0392b",
                          opacity=0.85, text=[f"{v:.0f}%" for v in r_vals], textposition="outside"))
    fig4.update_layout(
        title=dict(text="Retention at key milestones", font=dict(size=13, color="#888"), x=0),
        barmode="group", paper_bgcolor="#f8f7f4", plot_bgcolor="#f8f7f4",
        font=dict(family="IBM Plex Sans", color="#333"),
        xaxis=dict(gridcolor="#e8e8e8"),
        yaxis=dict(title="% retained", gridcolor="#e8e8e8", range=[0, 115], ticksuffix="%"),
        legend=dict(bgcolor="#f8f7f4"),
        height=340, margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig4, use_container_width=True)

st.markdown(f"""<div class="insight">
    The churn gap compounds just like fees. A passive investor has less reason to switch. A robo-advisor customer who watches the market beat their managed portfolio
    for 2–3 years will start asking why they're paying {robo_fee}%. By year 10, the modeled robo retention
    is {yr10_robo:.0f}% vs {yr10_passive:.0f}% for passive. A 
    {yr10_passive - yr10_robo:.0f}pp retention gap.
    Lower retention = shorter LTV window = harder to recover CAC.
</div>""", unsafe_allow_html=True)

# ── SECTION 3: BREAK-EVEN & CAC/LTV ───────────────────────────────────────────
st.markdown('<div class="section">CAC · LTV · break-even analysis</div>', unsafe_allow_html=True)

col_e, col_f = st.columns(2)

with col_e:
    be_years = range(1, 16)
    ltv_by_yr = []
    for y in be_years:
        rv = retention_curve(robo_yr1_churn, 0.025, y)
        ltv_by_yr.append(calc_ltv(initial, robo_aum_fee_pct, rv, y))

    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(
        x=list(be_years), y=ltv_by_yr, name="Cumulative LTV",
        mode="lines+markers", line=dict(color="#2d7a3e", width=2.5),
        marker=dict(size=7, color="#2d7a3e"),
        fill="tozeroy", fillcolor="rgba(45,122,62,0.07)"
    ))
    fig5.add_hline(y=robo_cac, line_dash="dash", line_color="#c0392b", line_width=1.5,
                   annotation_text=f"CAC = ${robo_cac}", annotation_font_color="#c0392b",
                   annotation_position="top right")
    if breakeven_yr:
        fig5.add_vline(x=breakeven_yr, line_dash="dot", line_color="#c8b87a", line_width=1.5,
                       annotation_text=f"Break-even yr {breakeven_yr}",
                       annotation_font_color="#c8b87a", annotation_position="top left")
    fig5.update_layout(
        title=dict(text=f"LTV accumulation vs ${robo_cac} CAC", font=dict(size=13, color="#888"), x=0),
        paper_bgcolor="#f8f7f4", plot_bgcolor="#f8f7f4",
        font=dict(family="IBM Plex Sans", color="#333"),
        xaxis=dict(title="Years retained", gridcolor="#e8e8e8", zeroline=False,
                   tickmode="linear", dtick=1),
        yaxis=dict(title="Cumulative LTV ($)", gridcolor="#e8e8e8", zeroline=False,
                   tickprefix="$", tickformat=",.0f"),
        legend=dict(bgcolor="#f8f7f4"),
        height=340, margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig5, use_container_width=True)

with col_f:
    alpha_vals = np.arange(0, 2.1, 0.25)
    breakeven_fees = [robo_fee + etf_mer + a for a in alpha_vals]
    net_returns = [gross_return - f for f in breakeven_fees]

    fig6 = go.Figure()
    fig6.add_trace(go.Bar(
        x=[f"+{a:.2f}%" for a in alpha_vals],
        y=[gross_return - (robo_fee + etf_mer) - a for a in alpha_vals],
        marker_color=["#c0392b" if v < 0 else "#2d7a3e" for v in
                      [gross_return - (robo_fee + etf_mer) - a for a in alpha_vals]],
        text=[f"{gross_return - (robo_fee + etf_mer) - a:.1f}%" for a in alpha_vals],
        textposition="outside",
    ))
    fig6.add_hline(y=0, line_color="#333", line_width=0.8)
    fig6.add_annotation(x=1, y=-(robo_fee + etf_mer) * 0.5, xref="paper",
                        text=f"Robo must generate >{robo_fee+etf_mer:.2f}%<br>alpha just to match passive",
                        showarrow=False, font=dict(size=11, color="#888"),
                        align="center", bgcolor="#f8f7f4")
    fig6.update_layout(
        title=dict(text="Net return after fees by alpha generated", font=dict(size=13, color="#888"), x=0),
        paper_bgcolor="#f8f7f4", plot_bgcolor="#f8f7f4",
        font=dict(family="IBM Plex Sans", color="#333"),
        xaxis=dict(title="Alpha generated above passive", gridcolor="#e8e8e8"),
        yaxis=dict(title="Net return to investor (%)", gridcolor="#e8e8e8", ticksuffix="%"),
        height=340, margin=dict(l=10, r=10, t=40, b=10), showlegend=False
    )
    st.plotly_chart(fig6, use_container_width=True)

col_g, col_h, col_i = st.columns(3)
with col_g:
    st.markdown(f"""<div class="kpi" style="text-align:center;">
        <div class="kpi-lbl">Robo CAC</div>
        <div class="kpi-val">${robo_cac:,}</div>
        <div class="kpi-sub gray">To acquire 1 customer</div>
    </div>""", unsafe_allow_html=True)
with col_h:
    st.markdown(f"""<div class="kpi" style="text-align:center;">
        <div class="kpi-lbl">10-yr LTV (modeled)</div>
        <div class="kpi-val {'green' if robo_ltv > robo_cac else 'red'}">${robo_ltv:,.0f}</div>
        <div class="kpi-sub {'green' if robo_ltv > robo_cac else 'red'}">{'Above' if robo_ltv > robo_cac else 'Below'} CAC threshold</div>
    </div>""", unsafe_allow_html=True)
with col_i:
    unit_econ = robo_ltv - robo_cac
    st.markdown(f"""<div class="kpi" style="text-align:center;">
        <div class="kpi-lbl">Unit economics</div>
        <div class="kpi-val {'green' if unit_econ > 0 else 'red'}">${unit_econ:+,.0f}</div>
        <div class="kpi-sub {'green' if unit_econ > 0 else 'red'}">LTV minus CAC</div>
    </div>""", unsafe_allow_html=True)

# ── THE HARD TRUTH ────────────────────────────────────────────────────────────
st.markdown("""
<div class="hard-truth">
  <div class="ht-q">What is the hard truth that will never change in your industry?</div>
  <p class="ht-body">
    In investing, it's this: fees always compound against you. Buffett proved it with a 10-year bet in 2008.
    I confirmed it with 5 months of real data in 2025-2026 (will continue observing). The math doesn't care how good the algorithm is,
    how beautiful the dashboard is, or how compelling the sales pitch is. A {robo_fee:.1f}% annual fee
    on ${initial:,} costs you ${total_drag:,.0f} over {horizon} years. 
  </p>
  <p class="ht-body" style="margin-top: 16px; color: #c8b87a; font-style: italic;">
    Every industry has one hard truth that no technology will ever erase. What's yours?
  </p>
</div>
""".format(
    robo_fee=robo_fee, initial=initial, total_drag=total_drag,
    horizon=horizon, be_yr=breakeven_yr or ">30"
), unsafe_allow_html=True)

st.markdown(f"""
<div style="margin-top:24px; padding: 12px 16px; background: #f0ede8; border-radius: 10px;">
  <p style="font-size:0.78rem; color:#888; margin:0; line-height:1.7;">
    <b>Data:</b> 10-year projections assume {gross_return}% gross annual return · Robo fee = {robo_fee}% AUM/yr ·
    ETF MER = {etf_mer}% both portfolios · Retention curves illustrative based on Deloitte (2023) robo-advisor benchmarks ·
    CAC benchmark: industry average $300–500 (Fintech Futures 2024) ·
    Buffett bet returns: Vanguard 500 Index Admiral +126%, Protégé hedge fund basket +36% (2008–2017)
  </p>
</div>
""", unsafe_allow_html=True)
