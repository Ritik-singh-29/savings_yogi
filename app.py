import json

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
import base64

# ==========================================
# PAGE CONFIGURATION & THEME
# ==========================================
st.set_page_config(
    page_title="Institutional Markets Dashboard", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Professional Banking/Corporate CSS Theme
st.markdown("""
<style>
    /* Global Background and Fonts */
    .stApp { background-color: #f8fafc; font-family: 'Inter', 'Segoe UI', sans-serif; }
    
    /* Typography */
    h1, h2, h3 { color: #0f172a; font-weight: 700; }
    .title-area { padding-bottom: 5px; margin-bottom: 0px; }
    .dashboard-title { font-size: 26px; color: #0f172a; font-weight: 700; margin: 0; padding: 0; letter-spacing: -0.5px;}
    .dashboard-subtitle { font-size: 14px; color: #64748b; margin-top: 4px; font-weight: 500;}
    
    .section-title { font-size: 14px; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.08em; margin: 32px 0 16px 0; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0; }
    
    /* Header Container for Logo and Title */
    .header-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding-left: 1%; 
        margin-bottom: 5px;
    }

    /* KPI Cards */
    .kpi-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); transition: transform 0.2s ease, box-shadow 0.2s ease; }
    .kpi-card:hover { box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); transform: translateY(-1px); }
    .kpi-label { font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
    .kpi-value { font-size: 24px; font-weight: 700; color: #0f172a; line-height: 1.2; margin-bottom: 4px; }
    .kpi-sub { font-size: 12px; font-weight: 500; display: flex; align-items: center; gap: 4px; }
    
    /* Value Colors */
    .up { color: #10b981; }
    .down { color: #ef4444; }
    .neutral { color: #64748b; }
    .up-bg { background: #d1fae5; padding: 2px 6px; border-radius: 4px; }
    .down-bg { background: #fee2e2; padding: 2px 6px; border-radius: 4px; }
    
    /* Insight Boxes */
    .insight-box { background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #3b82f6; padding: 16px; border-radius: 4px; font-size: 13px; color: #334155; line-height: 1.6; margin-top: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.02); }
    .insight-box strong { color: #0f172a; font-weight: 600; }
    
    /* Volatility Zones */
    .vol-zone { display: flex; align-items: center; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; border: 1px solid transparent; }
    .vol-zone.low { background: #f0fdf4; border-color: #d1fae5; }
    .vol-zone.mid { background: #fffbeb; border-color: #fef3c7; }
    .vol-zone.high { background: #fef2f2; border-color: #fee2e2; }
    .vol-title { font-size: 14px; font-weight: 600; width: 60px; }
    .vol-desc { flex-grow: 1; font-size: 12px; color: #475569; }
    .vol-pct { font-size: 14px; font-weight: 600; text-align: right; }
    
    /* Hide Streamlit components */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
            
    /* Reduce space in right-side controls */
div[data-testid="stRadio"] > div {
    flex-direction: row;
    gap: 10px;
}

div[data-testid="stRadio"] label {
    margin-bottom: 0px !important;
    font-size: 12px;
}

/* Reduce selectbox height */
div[data-testid="stSelectbox"] {
    margin-bottom: -10px;
}

/* Remove extra padding from columns */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 0rem !important;
}

/* Tighten spacing between inputs */
.stColumn {
    gap: 5px !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# HELPERS & DATA LOADING
# ==========================================
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# @st.cache_data(ttl=3600)
# def load_and_prep_data():
#     scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
#     creds = Credentials.from_service_account_file("key.json", scopes=scope)
#     client = gspread.authorize(creds)
#     sheet = client.open("Scrap_data").worksheet("MASTER")
#     df = pd.DataFrame(sheet.get_all_records())
#     df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
#     df = df.dropna(subset=["Value", "Date"])
#     df["Metric"] = df["Metric"].astype(str).str.strip()
#     df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
#     wide_df = df.pivot_table(index="Date", columns="Metric", values="Value", aggfunc='last')
#     wide_df = wide_df.sort_index().ffill()
#     return wide_df

@st.cache_data(ttl=3600)
def load_and_prep_data():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # NEW: Pull the secure credentials from Streamlit Secrets
    google_creds_str = st.secrets["GOOGLE_CREDENTIALS_JSON"]
    creds_dict = json.loads(google_creds_str)
    
    # NEW: Use from_service_account_info instead of from_service_account_file
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    
    # The rest stays exactly the same
    sheet = client.open("Scrap_data").worksheet("MASTER")
    df = pd.DataFrame(sheet.get_all_records())
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Value", "Date"])
    df["Metric"] = df["Metric"].astype(str).str.strip()
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    wide_df = df.pivot_table(index="Date", columns="Metric", values="Value", aggfunc='last')
    wide_df = wide_df.sort_index().ffill()
    return wide_df


try:
    data = load_and_prep_data()
    logo_base64 = get_base64_of_bin_file("img.jpeg")
except Exception as e:
    st.error(f"Error loading assets: {e}")
    st.stop()

# ==========================================
# COLUMN AUTO-DETECTION
# ==========================================
def find_column(df_cols, exact_matches, partial_matches):
    for exact in exact_matches:
        if exact in df_cols: return exact
    for partial in partial_matches:
        for c in df_cols:
            if partial.upper() in c.upper(): return c
    return None

cols = list(data.columns)
SP500 = find_column(cols, ["SP500", "S&P 500"], ["SP500"])
NASDAQ = find_column(cols, ["NASDAQCOM", "NASDAQ"], ["NASDAQ"])
DJIA = find_column(cols, ["DJIA", "DOW"], ["DJIA"])
VIX = find_column(cols, ["VIXCLS", "VIX"], ["VIX"])
VXV = find_column(cols, ["VXVCLS", "VXV"], ["VXV"])
EFFR = find_column(cols, ["EFFR-Rate (%)", "EFFR"], ["EFFR"])
OBFR = find_column(cols, ["OBFR"], ["OBFR"])
SOFR = find_column(cols, ["SOFR"], ["SOFR"])
TGCR = find_column(cols, ["TGCR"], ["TGCR"])
BGCR = find_column(cols, ["BGCR"], ["BGCR"])

# ==========================================
# CALCULATION HELPERS
# ==========================================
def get_kpi_metrics(df, col_name, is_rate=False):
    if not col_name or col_name not in df.columns: return 0, 0, "0"
    s = df[col_name].dropna()
    if len(s) < 2: return (s.iloc[0], 0, "0") if not s.empty else (0,0,"0")
    val, prev = s.iloc[-1], s.iloc[0]
    if is_rate:
        chg = (val - prev) * 100
        return val, chg, f"{chg:+.1f} bps"
    chg = ((val - prev) / prev) * 100 if prev != 0 else 0
    return val, chg, f"{chg:+.2f}%"

def get_rate_stats(df, col_name):
    if not col_name or col_name not in df.columns: return "-", "-", "-"
    s = df[col_name].dropna()
    return (f"{s.iloc[-1]:.2f}%", f"{s.mean():.2f}%", f"{s.max():.2f}%") if not s.empty else ("-","-","-")

def render_kpi_card(label, value, chg_val, chg_str, format_str="{:,.2f}", is_rate=False, mode="Period"):
    cls, bg, arr = ("up", "up-bg", "▲") if chg_val > 0 else (("down", "down-bg", "▼") if chg_val < 0 else ("neutral", "", "▬"))
    v_str = format_str.format(value) + ("%" if is_rate else "")
    return f"""<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{v_str}</div><div class="kpi-sub {cls}"><span class="{bg}">{arr} {chg_str}</span> <span style="color:#94a3b8; margin-left:4px;"> {mode}</span></div></div>"""

def summary_kpi(label, val, sub):
    return f"""<div class="kpi-card" style="padding: 14px 16px;"><div class="kpi-label">{label}</div><div class="kpi-value" style="font-size: 20px;">{val}</div><div class="kpi-sub neutral" style="font-size: 11px;">{sub}</div></div>"""

def apply_plotly_layout(fig, title="", y_title=""):
    fig.update_layout(title=dict(text=title, font=dict(size=14, color="#1e293b")), plot_bgcolor="white", paper_bgcolor="white", margin=dict(l=10, r=10, t=40, b=10), hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), xaxis=dict(showgrid=False, linecolor="#cbd5e1"), yaxis=dict(showgrid=True, gridcolor="#f1f5f9", title=dict(text=y_title, font=dict(size=11))), font_family="Inter")
    return fig

# ==========================================
# DATE SELECTION LOGIC
# ==========================================
col_head, col_date, col_download = st.columns([3.2, 1, 0.8])

# Prepare list of dates for dropdown (Recent first)
available_dates = data.index.strftime('%Y-%m-%d').tolist()[::-1]

with col_date:
    st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
    view_mode = st.radio("Selection Mode:", ["Date Range", "Single Date"], horizontal=True)
    
    c_start, c_end = st.columns(2)
    
    if view_mode == "Date Range":
        with c_start:
            start_choice = st.selectbox("Start Date:", available_dates, index=len(available_dates)-1)
        with c_end:
            end_choice = st.selectbox("End Date:", available_dates, index=0)
        
        start_dt = pd.to_datetime(start_choice)
        end_dt = pd.to_datetime(end_choice)
        
        if start_dt > end_dt:
            st.error("Error: Start > End")
            st.stop()
            
        filtered_data = data.loc[start_dt:end_dt]
        display_label = f"{start_dt.strftime('%b %d, %Y')} to {end_dt.strftime('%b %d, %Y')}"
        kpi_sub_mode = "Period"
    else:
        with c_start:
            target_choice = st.selectbox("Target Date:", available_dates, index=0)
        target_dt = pd.to_datetime(target_choice)
        
        # In Single Date mode, we grab the target date and the one day before it 
        prev_idx = data.index.get_loc(target_dt)
        if prev_idx > 0:
            filtered_data = data.iloc[prev_idx-1 : prev_idx+1]
        else:
            filtered_data = data.loc[target_dt:target_dt]
            
        display_label = f"Snapshot: {target_dt.strftime('%b %d, %Y')}"
        kpi_sub_mode = "1D"

with col_download:
    st.markdown("<div style='margin-top:25px'></div>", unsafe_allow_html=True)

    csv = filtered_data.to_csv().encode('utf-8')

    st.download_button(
        label="Download",
        data=csv,
        file_name="dashboard_data.csv",
        mime="text/csv"
    )        

# ==========================================
# HEADER RENDERING
# ==========================================
with col_head:
    st.markdown(f"""
<div class="header-container">
    <img src="data:image/jpeg;base64,{logo_base64}" width="100" style="border-radius: 50%; border: 2px solid #e2e8f0;">
    <div class="title-area">
        <h1 class="dashboard-title">Institutional Markets Dashboard</h1>
        <div class="dashboard-subtitle">Real-time daily reporting layer • {display_label} • {len(filtered_data):,} Trading Days Evaluated</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='border-bottom: 1px solid #e2e8f0; margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# ==========================================
# DASHBOARD CONTENT
# ==========================================

# 1. Market Snapshot KPIs
st.markdown(f'<div class="section-title" style="margin-top:0;">Market Snapshot ({kpi_sub_mode} Change)</div>', unsafe_allow_html=True)
k1, k2, k3, k4, k5 = st.columns(5)
metrics_list = [("S&P 500", SP500, False), ("NASDAQ Comp", NASDAQ, False), ("Dow Jones (DJIA)", DJIA, False), ("CBOE Volatility (VIX)", VIX, False), ("Effective Fed Funds", EFFR, True)]
cols_list = [k1, k2, k3, k4, k5]

for i, (label, col, is_rate) in enumerate(metrics_list):
    val, chg, chg_s = get_kpi_metrics(filtered_data, col, is_rate)
    with cols_list[i]: st.markdown(render_kpi_card(label, val, chg, chg_s, is_rate=is_rate, mode=kpi_sub_mode), unsafe_allow_html=True)

# 2. Performance & Volatility Regime
c1, c2 = st.columns([1.8, 1])
with c1:
    st.markdown('<div class="section-title">Relative Index Performance (Base = 100)</div>', unsafe_allow_html=True)
    fig_p = go.Figure()
    colors = ['#3b82f6', '#10b981', '#f59e0b']
    for i, col in enumerate([SP500, NASDAQ, DJIA]):
        if col in filtered_data.columns:
            s = filtered_data[col].dropna()
            if not s.empty:
                rebased_vals = (s / s.iloc[0]) * 100
                fig_p.add_trace(go.Scatter(x=rebased_vals.index, y=rebased_vals, name=col, line=dict(width=2, color=colors[i]), fill='tozeroy', fillcolor=colors[i].replace('rgb','rgba').replace(')',',0.05)')))
    st.plotly_chart(apply_plotly_layout(fig_p, y_title="Index Level"), width='stretch', config={'displayModeBar': False})

with c2:
    st.markdown('<div class="section-title">Volatility Regime (VIX)</div>', unsafe_allow_html=True)
    v_data = filtered_data[VIX].dropna()
    if not v_data.empty:
        l, m, h = (len(v_data[v_data < 15])/len(v_data))*100, (len(v_data[(v_data >= 15) & (v_data <= 25)])/len(v_data))*100, (len(v_data[v_data > 25])/len(v_data))*100
        st.markdown(f"""<div class="vol-zone low"><div class="vol-title" style="color:#059669;">LOW</div><div class="vol-desc">VIX < 15 (Bullish)</div><div class="vol-pct">{l:.1f}%</div></div><div class="vol-zone mid"><div class="vol-title" style="color:#d97706;">MID</div><div class="vol-desc">VIX 15-25 (Normal)</div><div class="vol-pct">{m:.1f}%</div></div><div class="vol-zone high"><div class="vol-title" style="color:#dc2626;">HIGH</div><div class="vol-desc">VIX > 25 (Fear)</div><div class="vol-pct">{h:.1f}%</div></div>""", unsafe_allow_html=True)
        fig_h = px.histogram(v_data, x=VIX, nbins=30, color_discrete_sequence=['#94a3b8'])
        fig_h.update_layout(plot_bgcolor="white", paper_bgcolor="white", margin=dict(l=0, r=0, t=10, b=0), xaxis=dict(showgrid=False, title=""), yaxis=dict(showgrid=False, showticklabels=False), height=140)
        st.plotly_chart(fig_h, width='stretch', config={'displayModeBar': False})

# 3. Volatility Term Structure
st.markdown('<div class="section-title">Volatility Term Structure — VIX & VXVCLS</div>', unsafe_allow_html=True)
cv = filtered_data[[VIX, VXV]].dropna()
if not cv.empty:
    vc1, vc2, vc3, vc4, vc5 = st.columns(5)
    with vc1: st.markdown(summary_kpi("VIX Mean", f"{cv[VIX].mean():.2f}", f"Med: {cv[VIX].median():.2f}"), unsafe_allow_html=True)
    with vc2: st.markdown(summary_kpi("VIX Range", f"{cv[VIX].min():.1f}-{cv[VIX].max():.1f}", f"Peak: {cv[VIX].idxmax().strftime('%b %d')}"), unsafe_allow_html=True)
    with vc3: st.markdown(summary_kpi("VXVCLS Mean", f"{cv[VXV].mean():.2f}", "3-Month Vol"), unsafe_allow_html=True)
    with vc4: st.markdown(summary_kpi("VIX-VXV Corr", f"{cv[VIX].corr(cv[VXV]):.3f}", f"Spread: {(cv[VXV]-cv[VIX]).mean():.2f}"), unsafe_allow_html=True)
    cp = ((cv[VXV] >= cv[VIX]).sum()/len(cv))*100
    with vc5: st.markdown(summary_kpi("Contango Days", f"{cp:.1f}%", f"{100-cp:.1f}% Stress"), unsafe_allow_html=True)
    fig_v = go.Figure()
    fig_v.add_trace(go.Scatter(x=cv.index, y=cv[VXV], name="VXVCLS", line=dict(color="#6366f1")))
    fig_v.add_trace(go.Scatter(x=cv.index, y=cv[VIX], name="VIX", line=dict(color="#ef4444"), fill='tozeroy', fillcolor='rgba(239,68,68,0.05)'))
    st.plotly_chart(apply_plotly_layout(fig_v, y_title="Vol Level"), width='stretch')

# 4. Macro & Correlations

# 4. Macro & Correlations
st.markdown('<div class="section-title">Macroeconomic Overlay & Correlation</div>', unsafe_allow_html=True)

# Define the pairs (Label, Left Axis Asset, Right Axis Asset)
# Note: I put EFFR vs S&P 500 first so it defaults to your original view
ps = [
    ("EFFR ↔ S&P 500", EFFR, SP500),
    ("S&P 500 ↔ NASDAQ", SP500, NASDAQ), 
    ("S&P 500 ↔ DJIA", SP500, DJIA), 
    ("S&P 500 ↔ VIX", SP500, VIX)
]

mc1, mc2 = st.columns([1.5, 1])

with mc2:
    st.markdown("<p style='font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 0px;'>Asset Pearson Correlations</p>", unsafe_allow_html=True)
    
    # Hidden label selectbox to capture the user's choice
    selected_pair_label = st.selectbox("Select pair to chart:", [p[0] for p in ps], label_visibility="collapsed")
    
    h_c = ""
    for label, a, b in ps:
        if a in filtered_data.columns and b in filtered_data.columns:
            df_p = filtered_data[[a,b]].dropna()
            if len(df_p) > 2:
                v = df_p.corr().iloc[0,1]
                clr = "#3b82f6" if v > 0 else "#ef4444"
                
                # Dynamic CSS to highlight the currently selected row
                is_selected = (label == selected_pair_label)
                bg_col = "#f1f5f9" if is_selected else "transparent"
                border_left = f"4px solid {clr}" if is_selected else "4px solid transparent"
                font_w = "700" if is_selected else "400"
                
                h_c += f'<div style="display:flex; justify-content:space-between; font-size:12px; border-bottom:1px solid #f1f5f9; padding:8px; background-color:{bg_col}; border-left:{border_left}; margin-bottom:4px; border-radius: 0 4px 4px 0; transition: all 0.2s;"><span style="width:140px; font-weight:{font_w};">{label}</span><div style="flex-grow:1; margin:0 12px; height:6px; background:#e2e8f0; border-radius:3px; position:relative; top:6px;"><div style="position:absolute; height:100%; width:{abs(v)*100}%; background:{clr}; border-radius:3px;"></div></div><span style="font-weight:600; color:{clr};">{v:+.2f}</span></div>'
                
    st.markdown(f"<div style='background:white; border: 1px solid #e2e8f0; padding: 12px; border-radius: 8px;'>{h_c if h_c else 'Insufficient data for correlation'}</div>", unsafe_allow_html=True)

with mc1:
    # Find the data for the selected pair
    selected_pair_data = next((p for p in ps if p[0] == selected_pair_label), None)
    
    if selected_pair_data:
        _, asset1, asset2 = selected_pair_data
        
        fig_m = go.Figure()
        
        # Plot Asset 1 (Left Y-Axis)
        if asset1 in filtered_data.columns:
            # Check if it's a rate (make it dotted green) or an index (solid blue)
            dash_style_1 = "dot" if asset1 == EFFR else "solid"
            color_1 = "#10b981" if asset1 == EFFR else "#3b82f6"
            fig_m.add_trace(go.Scatter(x=filtered_data.index, y=filtered_data[asset1], name=asset1, line=dict(color=color_1, dash=dash_style_1), yaxis="y1"))
        
        # Plot Asset 2 (Right Y-Axis)
        if asset2 in filtered_data.columns:
            # Assign distinct colors so lines don't blend in
            dash_style_2 = "dot" if asset2 == EFFR else "solid"
            color_2 = "#10b981" if asset2 == EFFR else ("#ef4444" if asset2 == VIX else "#6366f1")
            fig_m.add_trace(go.Scatter(x=filtered_data.index, y=filtered_data[asset2], name=asset2, line=dict(color=color_2, dash=dash_style_2), yaxis="y2"))
        
        # Dynamically update the layout titles based on selected assets
        fig_m.update_layout(
            plot_bgcolor="white", paper_bgcolor="white", 
            margin=dict(l=10, r=10, t=30, b=10), 
            hovermode="x unified", 
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), 
            yaxis=dict(title=f"{asset1} Level" if asset1 != EFFR else f"{asset1} %", showgrid=True, gridcolor="#f1f5f9"), 
            yaxis2=dict(title=f"{asset2} Level" if asset2 != EFFR else f"{asset2} %", overlaying="y", side="right")
        )
        st.plotly_chart(fig_m, width='stretch')

# 5. Federal Reserve & Overnight Rates
st.markdown('<div class="section-title">Federal Reserve rate cycle & Overnight Rates</div>', unsafe_allow_html=True)
f1, f2, f3 = st.columns(3)
with f1: st.markdown(summary_kpi("Rate range (EFFR)", "0.05% → 5.33%", "Cycle 2022-2023"), unsafe_allow_html=True)
with f2: st.markdown(summary_kpi("Total hikes", "12 hikes", "+525 bps total"), unsafe_allow_html=True)
with f3: st.markdown(summary_kpi("Total cuts", "2 cuts so far", "-75 bps total"), unsafe_allow_html=True)

ec, em, ex = get_rate_stats(filtered_data, EFFR); oc, om, ox = get_rate_stats(filtered_data, OBFR); sc, sm, sx = get_rate_stats(filtered_data, SOFR); tc, tm, tx = get_rate_stats(filtered_data, TGCR); bc, bm, bx = get_rate_stats(filtered_data, BGCR)

st.markdown(f"""<div style="font-size:13px; font-weight:600; color:#475569; margin-top:20px; text-transform:uppercase;">ALL 5 OVERNIGHT RATES — SNAPSHOT</div><table style="width:100%; text-align:left; border-collapse:collapse; font-size:14px; margin-top:12px;"><tr style="color:#64748b; font-size:12px; text-transform:uppercase; border-bottom:1px solid #e2e8f0;"><th style="padding-bottom:10px;">Rate</th><th>Meaning</th><th>Current</th><th>Mean (Period)</th><th>Max (Period)</th><th>Volume</th></tr><tr><td style="padding:12px 0; font-weight:600;">EFFR</td><td>Fed funds</td><td style="color:#10b981; font-weight:600;">{ec}</td><td>{em}</td><td>{ex}</td><td>$96B</td></tr><tr style="border-top:1px solid #f1f5f9;"><td style="padding:12px 0; font-weight:600;">OBFR</td><td>Bank funding</td><td style="color:#3b82f6; font-weight:600;">{oc}</td><td>{om}</td><td>{ox}</td><td>$200B</td></tr><tr style="border-top:1px solid #f1f5f9;"><td style="padding:12px 0; font-weight:600;">SOFR</td><td>Secured O/N</td><td style="color:#8b5cf6; font-weight:600;">{sc}</td><td>{sm}</td><td>{sx}</td><td>$3,014B</td></tr><tr style="border-top:1px solid #f1f5f9;"><td style="padding:12px 0; font-weight:600;">TGCR</td><td>Tri-party repo</td><td style="color:#f59e0b; font-weight:600;">{tc}</td><td>{tm}</td><td>{tx}</td><td>$1,261B</td></tr><tr style="border-top:1px solid #f1f5f9;"><td style="padding:12px 0; font-weight:600;">BGCR</td><td>Broad GC repo</td><td style="color:#ea580c; font-weight:600;">{bc}</td><td>{bm}</td><td>{bx}</td><td>$1,293B</td></tr></table><div class="insight-box"><strong>SOFR dominates by volume</strong> — $3T/day vs EFFR's $96B. All five cluster tightly within the Fed target band.</div>""", unsafe_allow_html=True)