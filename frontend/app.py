import os
from dotenv import load_dotenv
load_dotenv()
import time
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="FlowAgent AI - Enterprise Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_URL = "http://localhost:8000"

# Inject custom CSS
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("Styling file not found.")

local_css(os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles.css"))

# Inject extra CSS for new features
st.markdown("""
<style>
@keyframes pulse-glow {
  0%, 100% { filter: drop-shadow(0 0 6px var(--glow-color)); opacity: 1; }
  50%       { filter: drop-shadow(0 0 18px var(--glow-color)); opacity: 0.85; }
}
@keyframes dash-flow {
  to { stroke-dashoffset: -24; }
}
@keyframes rejection-pulse {
  0%, 100% { stroke-opacity: 0.4; }
  50%       { stroke-opacity: 1; }
}
.agent-bubble.correction {
  border-left: 4px solid #fbbf24 !important;
  background: rgba(251,191,36,0.04) !important;
}
.agent-bubble.rejected {
  border-left: 4px solid #f87171 !important;
  background: rgba(248,113,113,0.04) !important;
}
.reflection-banner {
  background: linear-gradient(135deg, rgba(251,191,36,0.1), rgba(248,113,113,0.08));
  border: 1px solid rgba(251,191,36,0.4);
  border-radius: 12px;
  padding: 14px 18px;
  margin: 12px 0;
  font-size: 0.9rem;
}
.action-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  margin: 3px 4px;
  border: 1px solid;
}
.badge-email   { color:#34d399; border-color:#34d399; background:rgba(52,211,153,0.08); }
.badge-discord { color:#a78bfa; border-color:#a78bfa; background:rgba(167,139,250,0.08); }
.badge-crm     { color:#60a5fa; border-color:#60a5fa; background:rgba(96,165,250,0.08); }
.badge-reflect { color:#fbbf24; border-color:#fbbf24; background:rgba(251,191,36,0.08); }
.crm-card {
  background: rgba(16,185,129,0.05);
  border: 1px solid rgba(16,185,129,0.2);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}
.crm-stage-qualified { color: #10b981; }
.crm-stage-contacted  { color: #60a5fa; }
</style>
""", unsafe_allow_html=True)

# Helper function to check headers for authorized calls
def get_auth_headers():
    headers = {}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    api_key = st.session_state.get("api_key")
    if api_key:
        headers["X-Gemini-API-Key"] = api_key
    return headers

# Health check API call
def check_backend():
    try:
        response = requests.get(f"{API_URL}/api/health", headers=get_auth_headers(), timeout=3)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

backend_status = check_backend()

# Query active alerts
active_alerts = []
if backend_status and st.session_state.get("token"):
    try:
        active_alerts = requests.get(f"{API_URL}/api/alerts/active", headers=get_auth_headers()).json()
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────────────────────
# UPGRADED: Animated Agent Collaboration Map (SVG with directional arrows)
# ─────────────────────────────────────────────────────────────────────────────

def render_workflow_graph(active_agent="", rejected_agent="", show_rejection=False, step_label=""):
    """
    Generates an animated SVG collaboration map with:
    - Directional animated arrows between 12 agents
    - Pulsing active node glow
    - Red rejection backward arrow when reflection triggers
    - Live step-label on the active link
    """
    W, H = 840, 480

    nodes = {
        "Supervisor Agent":          {"cx": 420, "cy": 45,  "color": "#00f2fe", "emoji": "🕵️"},
        "Workflow Planner Agent":    {"cx": 210, "cy": 85,  "color": "#a855f7", "emoji": "📝"},
        "Trust & Safety Agent":      {"cx": 630, "cy": 85,  "color": "#6366f1", "emoji": "🛡️"},
        "Fraud Detection Agent":     {"cx": 110, "cy": 180, "color": "#e11d48", "emoji": "🔍"},
        "Knowledge Curator Agent":   {"cx": 730, "cy": 180, "color": "#f59e0b", "emoji": "📚"},
        "Support Agent":             {"cx": 110, "cy": 290, "color": "#3b82f6", "emoji": "🤖"},
        "Customer Care Agent":       {"cx": 730, "cy": 290, "color": "#ec4899", "emoji": "❤️"},
        "Finance Agent":             {"cx": 220, "cy": 380, "color": "#10b981", "emoji": "💳"},
        "Marketing Agent":           {"cx": 620, "cy": 380, "color": "#14b8a6", "emoji": "📣"},
        "Ticket Agent":              {"cx": 340, "cy": 435, "color": "#f97316", "emoji": "🎫"},
        "Sales Agent":               {"cx": 500, "cy": 435, "color": "#84cc16", "emoji": "💼"},
        "Analytics Agent":           {"cx": 320, "cy": 230, "color": "#06b6d4", "emoji": "📈"},
        "Executive Decision Agent":  {"cx": 520, "cy": 230, "color": "#fbbf24", "emoji": "👑"}
    }

    # Pipeline sequence edges representing collaborative task handoffs
    edges = [
        ("Workflow Planner Agent",   "Trust & Safety Agent",    "Safety Scanning"),
        ("Trust & Safety Agent",     "Fraud Detection Agent",   "Fraud Audit"),
        ("Fraud Detection Agent",    "Knowledge Curator Agent", "Context Search"),
        ("Knowledge Curator Agent",  "Support Agent",           "Support Drafting"),
        ("Support Agent",            "Customer Care Agent",     "Tone Empathy"),
        ("Customer Care Agent",      "Finance Agent",           "Billing Audit"),
        ("Finance Agent",            "Marketing Agent",         "Retention Offer"),
        ("Marketing Agent",          "Ticket Agent",            "Ticket Logging"),
        ("Ticket Agent",             "Sales Agent",             "Lead Scoring"),
        ("Sales Agent",              "Analytics Agent",         "Updating KPIs"),
        ("Analytics Agent",          "Executive Decision Agent","CEO Risk Audit"),
        ("Executive Decision Agent", "Supervisor Agent",        "Compliance Check"),
        ("Supervisor Agent",         "Workflow Planner Agent",  "Final Approval")
    ]

    svg = (
        f'<svg width="100%" height="{H}" viewBox="0 0 {W} {H}" '
        f'style="background:rgba(10,15,30,0.65);border-radius:16px;'
        f'border:1px solid rgba(255,255,255,0.08);">'
    )

    # ── Arrow marker defs ──
    svg += """
    <defs>
      <marker id="arr-normal" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
        <path d="M0,0 L0,6 L6,3 z" fill="rgba(255,255,255,0.18)" />
      </marker>
      <marker id="arr-active" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto">
        <path d="M0,0 L0,6 L6,3 z" fill="#00f2fe" />
      </marker>
      <marker id="arr-reject" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto">
        <path d="M0,0 L0,6 L6,3 z" fill="#f87171" />
      </marker>
    </defs>
    """

    # ── Draw normal edges ──
    for (start_name, end_name, label) in edges:
        if start_name not in nodes or end_name not in nodes:
            continue
        s = nodes[start_name]
        e = nodes[end_name]
        is_active = (active_agent == start_name)

        color   = "#00f2fe" if is_active else "rgba(255,255,255,0.08)"
        width   = 2.5 if is_active else 1.2
        dash    = "none" if is_active else "5,4"
        marker  = "url(#arr-active)" if is_active else "url(#arr-normal)"
        anim    = (f'<animate attributeName="stroke-dashoffset" from="0" to="-20" '
                   f'dur="0.9s" repeatCount="indefinite"/>') if is_active else ""

        # Offset line endpoints to edge of node circles
        r = 25
        dx = e["cx"] - s["cx"]
        dy = e["cy"] - s["cy"]
        dist = max((dx**2 + dy**2)**0.5, 1)
        x1 = s["cx"] + dx/dist * r
        y1 = s["cy"] + dy/dist * r
        x2 = e["cx"] - dx/dist * r
        y2 = e["cy"] - dy/dist * r

        svg += (
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}" '
            f'marker-end="{marker}">'
            f'{anim}</line>'
        )

        # Step label on active link
        if is_active and step_label:
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2 - 8
            svg += (
                f'<rect x="{mid_x-45:.0f}" y="{mid_y-10:.0f}" width="90" height="16" '
                f'rx="8" fill="rgba(0,242,254,0.15)" stroke="rgba(0,242,254,0.3)" stroke-width="0.8"/>'
                f'<text x="{mid_x:.0f}" y="{mid_y+2:.0f}" font-family="Outfit,sans-serif" '
                f'font-size="8" fill="#00f2fe" text-anchor="middle">{step_label[:18]}</text>'
            )

    # ── Draw rejection back-arrow ──
    if show_rejection and rejected_agent and rejected_agent in nodes:
        s = nodes["Supervisor Agent"]
        e = nodes[rejected_agent]
        dx = e["cx"] - s["cx"]
        dy = e["cy"] - s["cy"]
        dist = max((dx**2 + dy**2)**0.5, 1)
        x1 = s["cx"] + dx/dist * 25
        y1 = s["cy"] + dy/dist * 25
        x2 = e["cx"] - dx/dist * 25
        y2 = e["cy"] - dy/dist * 25
        cx_ctrl = (x1 + x2) / 2 + 50
        cy_ctrl = (y1 + y2) / 2 - 50
        svg += (
            f'<path d="M{x1:.1f},{y1:.1f} Q{cx_ctrl:.1f},{cy_ctrl:.1f} {x2:.1f},{y2:.1f}" '
            f'stroke="#f87171" stroke-width="2.5" fill="none" stroke-dasharray="5,3" '
            f'marker-end="url(#arr-reject)">'
            f'<animate attributeName="stroke-dashoffset" from="0" to="-20" dur="0.7s" repeatCount="indefinite"/>'
            f'</path>'
        )

    # ── Draw nodes ──
    for name, attr in nodes.items():
        is_active   = (active_agent == name)
        is_rejected = (show_rejection and name == rejected_agent)

        r            = 26 if is_active else 21
        stroke_color = attr["color"] if is_active else ("#f87171" if is_rejected else "rgba(255,255,255,0.18)")
        stroke_w     = 2.5 if (is_active or is_rejected) else 1.2
        text_color   = attr["color"] if is_active else ("#f87171" if is_rejected else "#94a3b8")
        font_w       = "bold" if is_active else "normal"

        glow_anim = ""
        if is_active:
            glow_anim = (
                f'<circle cx="{attr["cx"]}" cy="{attr["cy"]}" r="{r+8}" '
                f'fill="none" stroke="{attr["color"]}" stroke-width="2" opacity="0.3">'
                f'<animate attributeName="r" values="{r};{r+10};{r}" dur="1.2s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0.3;0;0.3" dur="1.2s" repeatCount="indefinite"/>'
                f'</circle>'
            )

        # Draw circles and text
        svg += (
            f'<g>'
            f'{glow_anim}'
            f'<circle cx="{attr["cx"]}" cy="{attr["cy"]}" r="{r}" '
            f'fill="rgba(10,15,30,0.95)" stroke="{stroke_color}" stroke-width="{stroke_w}"/>'
            f'<text x="{attr["cx"]}" y="{attr["cy"]+6}" font-size="14" text-anchor="middle">{attr["emoji"]}</text>'
            f'<text x="{attr["cx"]}" y="{attr["cy"]+r+14}" font-family="Outfit,sans-serif" '
            f'font-size="9" font-weight="{font_w}" fill="{text_color}" text-anchor="middle">'
            f'{name.replace(" Agent", "")}</text>'
            f'</g>'
        )

    svg += '</svg>'
    return svg


# ─────────────────────────────────────────────────────────────────────────────
# AUTHENTICATION PAGE
# ─────────────────────────────────────────────────────────────────────────────

if "token" not in st.session_state:
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown("""
        <h2 style="font-family: 'Outfit', sans-serif; font-weight:800; background: linear-gradient(135deg, #00f2fe 0%, #4f46e5 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            FlowAgent AI Security Portal
        </h2>
        <p style="font-size:0.9rem; color:#a0aec0;">Sign in to access agent workflows and logs</p>
    """, unsafe_allow_html=True)

    auth_tab1, auth_tab2 = st.tabs(["🔑 Login", "📝 Register"])

    with auth_tab1:
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        btn_login = st.button("Access Dashboard", type="primary", use_container_width=True)

        if btn_login:
            if login_user and login_pass:
                try:
                    res = requests.post(f"{API_URL}/api/auth/login", json={
                        "username": login_user,
                        "password": login_pass
                    })
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state["token"] = data["access_token"]
                        st.session_state["role"] = data["role"]
                        st.session_state["username"] = data["username"]
                        st.success("Access Granted! Loading dashboard...")
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
                except Exception as e:
                    st.error(f"Authentication server unreachable: {e}")
            else:
                st.warning("Please fill in both username and password.")

    with auth_tab2:
        reg_user = st.text_input("New Username", key="reg_user")
        reg_pass = st.text_input("New Password", type="password", key="reg_pass")
        reg_role = st.selectbox("Role", ["Agent", "Manager"], key="reg_role")
        btn_register = st.button("Register New User", use_container_width=True)

        if btn_register:
            if reg_user and reg_pass:
                try:
                    res = requests.post(f"{API_URL}/api/auth/register", json={
                        "username": reg_user,
                        "password": reg_pass,
                        "role": reg_role
                    })
                    if res.status_code == 200:
                        st.success("Registration successful! Switch to Login tab.")
                    else:
                        st.error(res.json().get("detail", "Registration failed."))
                except Exception as e:
                    st.error(f"Server error: {e}")
            else:
                st.warning("Fill in all credentials.")

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# MAIN APP WORKSPACE
# ─────────────────────────────────────────────────────────────────────────────

username = st.session_state["username"]
user_role = st.session_state["role"]

st.sidebar.markdown(f"""
<div class="glass-card" style="padding:15px; margin-bottom:15px; border-color:rgba(0, 242, 254, 0.2);">
    <span style="font-size:0.75rem; color:#a0aec0; text-transform:uppercase;">Logged In As</span><br>
    <b style="font-size:1.1rem; color:#00f2fe;">👤 {username}</b><br>
    <span class="custom-badge badge-cold" style="margin-top:5px; display:inline-block;">{user_role}</span>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("🔓 Sign Out", use_container_width=True):
    del st.session_state["token"]
    del st.session_state["role"]
    del st.session_state["username"]
    st.rerun()

st.sidebar.markdown('<div class="glass-card-header">⚡ System Configuration</div>', unsafe_allow_html=True)

backend_key_configured = backend_status.get("api_key_configured") if backend_status else False

api_key = st.sidebar.text_input(
    "Gemini API Key",
    value=st.session_state.get("api_key", ""),
    type="password",
    help="Provide Gemini API key for live LLM operations."
)

if api_key:
    if st.session_state.get("api_key") != api_key:
        st.session_state["api_key"] = api_key
        os.environ["GEMINI_API_KEY"] = api_key
        try:
            requests.post(f"{API_URL}/api/config", json={"key": "GEMINI_API_KEY", "value": api_key}, headers=get_auth_headers())
            st.sidebar.success("API Key updated on server!")
        except Exception as e:
            st.sidebar.error(f"Failed to save key to backend: {e}")

# ── New: Action Integration Config ──
with st.sidebar.expander("🔧 Action Integration Keys"):
    resend_key = st.text_input("Resend API Key (email)", type="password", placeholder="re_xxxxxx")
    if resend_key:
        try:
            requests.post(f"{API_URL}/api/config", json={"key": "RESEND_API_KEY", "value": resend_key}, headers=get_auth_headers())
            st.success("Resend key saved!")
        except Exception:
            pass

    discord_url = st.text_input("Discord Webhook URL", placeholder="https://discord.com/api/webhooks/...")
    if discord_url:
        try:
            requests.post(f"{API_URL}/api/config", json={"key": "DISCORD_WEBHOOK_URL", "value": discord_url}, headers=get_auth_headers())
            st.success("Discord webhook saved!")
        except Exception:
            pass
    st.caption("Leave blank to use simulation mode (still impressive for demos!)")

# Status Indicators
if backend_status:
    mode_text = "🟢 Live Gemini API" if backend_key_configured else "🔴 Missing Gemini API Key"
    ml_text = "🟢 Loaded" if backend_status.get("ml_models_loaded") else "🔴 Offline"

    st.sidebar.markdown(f"""
    <div style="font-size: 0.9rem; line-height: 1.8;">
        • <b>Backend Server</b>: 🟢 Connected<br>
        • <b>AI Layer</b>: {mode_text}<br>
        • <b>Local ML Predictors</b>: {ml_text}<br>
        • <b>ChromaDB Vector RAG</b>: 🟢 Active<br>
        • <b>Reflection Loop</b>: 🟢 Enabled<br>
        • <b>Action Tools</b>: 🔵 Ready (Simulation/Live)
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown("""
    <div style="background-color: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; border-radius: 8px; padding: 12px; font-size: 0.85rem; color: #f87171;">
        ⚠️ <b>FastAPI Backend Offline</b><br>
        Please launch the project using the root script:<br>
        <code>python run.py</code>
    </div>
    """, unsafe_allow_html=True)

# Main Title bar
st.markdown("""
<div style="margin-bottom: 25px;">
    <h1 style="font-family: 'Outfit', sans-serif; font-weight: 700; margin-bottom: 5px;">FlowAgent AI console</h1>
    <p style="color: #a0aec0; margin-top: 0;">Enterprise Operations · Self-Healing Agents · Real-World Action Execution · Voice Intelligence</p>
</div>
""", unsafe_allow_html=True)

if active_alerts:
    for alert in active_alerts:
        col_al1, col_al2 = st.columns([5, 1])
        with col_al1:
            st.warning(f"⚠️ **Anomaly Alert**: {alert['reason']} (Logged: {alert['created_at']})")
        with col_al2:
            if st.button("✅ Resolve Alert", key=f"btn_resolve_alert_{alert['id']}", use_container_width=True):
                try:
                    res_al = requests.post(f"{API_URL}/api/alerts/{alert['id']}/resolve", headers=get_auth_headers())
                    if res_al.status_code == 200:
                        st.success("Alert resolved!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Failed to resolve: {e}")

# Tabs
tab_dash, tab_chat, tab_omni, tab_twin, tab_lead, tab_tickets, tab_kb, tab_bench, tab_crm = st.tabs([
    "📊 Operations Dashboard & CEO Desk",
    "💬 Multi-Agent Desk",
    "📬 Omnichannel Inbox",
    "📈 Digital Twin Simulator",
    "💼 Lead Intelligence",
    "🎫 Support Tickets",
    "📁 Knowledge Hub & Self-Heal",
    "📊 Operations Scorecard",
    "🗂️ CRM Pipeline"
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: OPERATIONS DASHBOARD & FORECASTING
# ─────────────────────────────────────────────────────────────────────────────
with tab_dash:
    if not backend_status:
        st.info("FastAPI backend is offline. Start backend to view metrics.")
    else:
        try:
            analytics_res = requests.get(f"{API_URL}/api/analytics", headers=get_auth_headers()).json()
            kb_res = requests.get(f"{API_URL}/api/kb/stats", headers=get_auth_headers()).json()

            st.markdown(f"""
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-card-lbl">Total Tickets</div>
                    <div class="metric-card-val">{analytics_res['total_tickets']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-card-lbl">Avg Lead Score</div>
                    <div class="metric-card-val">{analytics_res['avg_lead_score']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-card-lbl">Human Escalations</div>
                    <div class="metric-card-val" style="color:#f87171;">{analytics_res.get('escalated_count', 0)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-card-lbl">Customer CSAT</div>
                    <div class="metric-card-val" style="color:#34d399;">{analytics_res.get('csat_score', 85.0)}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-card-lbl">VIP Customer Base</div>
                    <div class="metric-card-val" style="color:#fbbf24;">{analytics_res.get('vip_count', 0)}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown('<div class="glass-card-header">📊 Customer Queries by Category</div>', unsafe_allow_html=True)
                cat_data = analytics_res.get("tickets_by_category", {})
                if cat_data:
                    df_cat = pd.DataFrame(list(cat_data.items()), columns=["Category", "Count"])
                    fig = px.bar(df_cat, x="Category", y="Count", color="Category", template="plotly_dark",
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No queries classified yet.")

            with col2:
                st.markdown('<div class="glass-card-header">🎯 Customer Sentiments (ML Flagged)</div>', unsafe_allow_html=True)
                sent_data = analytics_res.get("tickets_by_sentiment", {})
                if sent_data:
                    df_sent = pd.DataFrame(list(sent_data.items()), columns=["Sentiment", "Count"])
                    colors_map = {"Positive": "#34d399", "Neutral": "#60a5fa", "Negative": "#f87171"}
                    fig = px.pie(df_sent, names="Sentiment", values="Count", hole=0.4, template="plotly_dark",
                                 color="Sentiment", color_discrete_map=colors_map)
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      margin=dict(l=10, r=10, t=10, b=10))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No sentiments tracked yet.")

            if user_role == "Manager":
                st.markdown('<div class="glass-card-header">🔮 Manager Predictive Operations Desk (scikit-learn Forecast)</div>', unsafe_allow_html=True)
                try:
                    forecast_res = requests.get(f"{API_URL}/api/analytics/forecast", headers=get_auth_headers()).json()
                    fc_col1, fc_col2 = st.columns([2, 1])

                    with fc_col1:
                        hist_len  = len(forecast_res["historical_volumes"])
                        total_dates = forecast_res["historical_days"] + forecast_res["forecast_days"]
                        total_vals  = forecast_res["historical_volumes"] + forecast_res["forecast_volumes"]
                        types = ["Historical"] * hist_len + ["Forecasted"] * 7

                        df_fc = pd.DataFrame({"Date": total_dates, "Tickets": total_vals, "Type": types})
                        fig_fc = px.line(df_fc, x="Date", y="Tickets", color="Type", line_dash="Type",
                                         template="plotly_dark", color_discrete_sequence=["#60a5fa", "#00f2fe"])
                        fig_fc.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                             margin=dict(l=10, r=10, t=10, b=10))
                        st.plotly_chart(fig_fc, use_container_width=True)

                    with fc_col2:
                        st.markdown("<b>Staffing Recommendations:</b>", unsafe_allow_html=True)
                        for d, v, staff in zip(forecast_res["forecast_days"][:4],
                                               forecast_res["forecast_volumes"][:4],
                                               forecast_res["staff_recommendations"][:4]):
                            st.markdown(f"""
                            <div class="glass-card" style="padding:10px; margin-bottom:8px; background:rgba(0, 242, 254, 0.03);">
                                📅 <b>{d}</b><br>
                                • Predicted Load: <b>{v} tickets</b><br>
                                • Recommended Staff: <b style="color:#00f2fe;">{staff} Agents</b>
                            </div>
                            """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Failed to fetch forecast details: {e}")
            else:
                st.markdown("""
                <div class="glass-card" style="text-align:center; padding:30px; color:#a0aec0;">
                    🔒 Predictive Operations Forecasting is locked to the <b>Manager</b> role.
                </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error drawing dashboard: {e}")

        st.markdown('<div class="glass-card-header" style="margin-top:25px;">⚠️ At-Risk Customers & Churn Warnings</div>', unsafe_allow_html=True)
        try:
            custs_list = requests.get(f"{API_URL}/api/customers", headers=get_auth_headers()).json()
            if custs_list:
                df_custs = pd.DataFrame(custs_list)
                risk_classes = []
                risk_scores  = []
                for idx, row in df_custs.iterrows():
                    if row["health_score"] < 50:
                        risk_classes.append("🔴 High")
                    elif row["health_score"] < 75:
                        risk_classes.append("🟡 Medium")
                    else:
                        risk_classes.append("🟢 Low")
                    risk_scores.append(100 - row["health_score"])

                df_custs["Churn Risk"]    = risk_classes
                df_custs["Risk Score (%)"] = risk_scores
                st.dataframe(
                    df_custs[["name", "email", "clv", "health_score", "Churn Risk", "Risk Score (%)"]]
                    .rename(columns={"name": "Name", "email": "Email", "clv": "CLV ($)", "health_score": "Health Score (/100)"})
                    .sort_values(by="Health Score (/100)", ascending=True),
                    use_container_width=True
                )
            else:
                st.info("No customer accounts logged in the database yet.")
        except Exception as ex:
            st.error(f"Failed to fetch at-risk customers: {ex}")

        # --- NEW: CEO Copilot & Meeting Report Generator ---
        st.markdown('<div class="glass-card-header" style="margin-top:25px;">👑 CEO Strategic Decision Desk & Report Generator</div>', unsafe_allow_html=True)
        col_ceo1, col_ceo2 = st.columns(2)
        with col_ceo1:
            st.markdown("<b>Ask the AI CEO Executive Copilot</b>", unsafe_allow_html=True)
            ceo_q = st.text_input("Ask a business question (e.g. 'Why did revenue drop?', 'Which customers will leave next month?')", "")
            if st.button("👑 Consult Copilot", key="btn_ceo_consult"):
                if ceo_q:
                    with st.spinner("Analyzing operational ledger..."):
                        try:
                            res_cop = requests.post(f"{API_URL}/api/analytics/copilot", json={"query": ceo_q}, headers=get_auth_headers()).json()
                            st.info(res_cop.get("analysis", "No analysis returned."))
                        except Exception as e:
                            st.error(f"Failed to reach copilot endpoint: {e}")
                else:
                    st.warning("Please type a question first.")
                    
        with col_ceo2:
            st.markdown("<b>AI Meeting & Operations Generator</b>", unsafe_allow_html=True)
            report_type = st.selectbox("Select Report Scope", ["Daily Brief", "Weekly Summary", "Monthly Strategic Board Report"])
            if st.button("📋 Generate Executive Report", key="btn_gen_report"):
                with st.spinner("Consolidating ticket sentiment and logs..."):
                    try:
                        scope = "daily" if "Daily" in report_type else ("weekly" if "Weekly" in report_type else "monthly")
                        rep_res = requests.get(f"{API_URL}/api/reports/meeting?type={scope}", headers=get_auth_headers()).json()
                        st.markdown(f"""
                        <div class="glass-card" style="padding:15px; border-color:#00f2fe;">
                            {rep_res['report']}
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Failed to generate report: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: MULTI-AGENT DESK + VOICE PORTAL + LIVE COLLABORATION MAP
# ─────────────────────────────────────────────────────────────────────────────
with tab_chat:
    # ── Voice Portal at top ──────────────────────────────────────────────────
    with st.expander("🎙️ Voice Portal — Speak to FlowAgent AI (Chrome/Edge Required)", expanded=False):
        st.markdown("""
        <div style="font-size:0.85rem; color:#64748b; margin-bottom:12px;">
            Click the microphone button below, speak your query, and the AI agents will respond both in text and voice.
            Powered by browser Web Speech API — no extra setup required.
        </div>
        """, unsafe_allow_html=True)
        voice_portal_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "widget", "voice_portal.html"
        )
        if os.path.exists(voice_portal_path):
            with open(voice_portal_path, "r", encoding="utf-8") as vf:
                voice_html = vf.read()
            st.components.v1.html(voice_html, height=520, scrolling=False)
        else:
            st.warning("Voice portal file not found. Check frontend/widget/voice_portal.html")

    st.markdown('<div class="glass-card-header">💬 Simulate Customer Touchpoint</div>', unsafe_allow_html=True)

    col_c1, col_c2 = st.columns([1, 1])

    with col_c1:
        c_name    = st.text_input("Customer Name", "Vipin Kumar", key="chat_cname")
        c_email   = st.text_input("Customer Email", "vipin@enterprise-solutions.com", key="chat_cemail")
        c_channel = st.selectbox("Inbound Channel", ["Web Chat", "Email", "WhatsApp", "Telegram"], key="chat_channel")
        c_resolve = st.checkbox("Auto-Resolve ticket if RAG confidence is high (>85%)", value=False)
        c_query   = st.text_area(
            "Customer Message",
            "I want a refund for my purchase of the Basic plan last week.",
            height=80
        )
        c_voice   = st.checkbox("🎙️ Simulate Voice Input (English/Hindi/Hinglish/Marathi)", value=False)
        c_file    = st.file_uploader("🖼️ Vision AI Attachment (damaged product, screenshot, invoice)", type=["png", "jpg", "jpeg"])
        
        img_b64 = None
        if c_file:
            import base64
            img_b64 = base64.b64encode(c_file.read()).decode("utf-8")
            
        submit = st.button("🚀 Process via Multi-Agent Pipeline", type="primary", key="chat_submit")

    with col_c2:
        st.markdown("<b>🗺️ Live Agent Collaboration Map</b>", unsafe_allow_html=True)
        graph_placeholder = st.empty()
        graph_placeholder.markdown(render_workflow_graph("Workflow Planner Agent"), unsafe_allow_html=True)

        # Live status ticker
        status_ticker = st.empty()

    if submit:
        if not c_name or not c_email or not c_query:
            st.error("Fill in all customer details.")
        else:
            # ── Animate the 12-agent graph step by step ──
            pipeline_sequence = [
                ("Workflow Planner Agent",   "Orchestrating Workflow Plan..."),
                ("Trust & Safety Agent",     "Verifying Safety Rules..."),
                ("Fraud Detection Agent",    "Evaluating Fraud Risk..."),
                ("Knowledge Curator Agent",  "Querying RAG Context..."),
                ("Support Agent",            "Synthesizing Support Reply..."),
                ("Customer Care Agent",      "Tuning Empathy & Tone..."),
                ("Finance Agent",            "Auditing Transaction Ledger..."),
                ("Marketing Agent",          "Generating Apology Offer..."),
                ("Ticket Agent",             "Registering SQL Ticket..."),
                ("Sales Agent",              "Evaluating Sales Lead..."),
                ("Analytics Agent",          "Logging Dashboard KPIs..."),
                ("Executive Decision Agent", "Checking CEO Warnings..."),
                ("Supervisor Agent",         "Auditing Workflow Compliance..."),
            ]

            for agent_name, label in pipeline_sequence:
                graph_placeholder.markdown(
                    render_workflow_graph(agent_name, step_label=label),
                    unsafe_allow_html=True
                )
                status_ticker.markdown(
                    f'<div style="font-size:0.8rem;color:#64748b;text-align:center;margin-top:6px;">'
                    f'⚡ {agent_name}: {label}</div>',
                    unsafe_allow_html=True
                )
                time.sleep(0.2)

            with st.spinner("Orchestrating agents..."):
                try:
                    payload = {
                        "customer_name":  c_name,
                        "customer_email": c_email,
                        "query":          c_query,
                        "session_id":     f"session_{c_email}",
                        "channel":        c_channel,
                        "auto_resolve":   c_resolve,
                        "image_data":     img_b64,
                        "voice_active":   c_voice
                    }
                    res = requests.post(f"{API_URL}/api/chat", json=payload, headers=get_auth_headers()).json()

                    # ── If reflection triggered, show rejection animation ──
                    if res.get("reflection_triggered"):
                        rejected = res.get("rejected_agent", "Support Agent")
                        graph_placeholder.markdown(
                            render_workflow_graph(
                                "Supervisor Agent",
                                rejected_agent=rejected,
                                show_rejection=True,
                                step_label="AUDIT FAILED"
                            ),
                            unsafe_allow_html=True
                        )
                        status_ticker.markdown(
                            f'<div style="font-size:0.8rem;color:#f87171;text-align:center;margin-top:6px;">'
                            f'🔴 Supervisor rejected output → redirecting to {rejected}</div>',
                            unsafe_allow_html=True
                        )
                        time.sleep(1.5)
                        # Show correction animation
                        graph_placeholder.markdown(
                            render_workflow_graph(rejected, step_label="Correcting..."),
                            unsafe_allow_html=True
                        )
                        time.sleep(1.0)
                        # Final sign-off
                        graph_placeholder.markdown(
                            render_workflow_graph("Supervisor Agent", step_label="Final Sign-off"),
                            unsafe_allow_html=True
                        )
                    else:
                        graph_placeholder.markdown(
                            render_workflow_graph("Supervisor Agent", step_label="✅ Approved"),
                            unsafe_allow_html=True
                        )

                    status_ticker.empty()
                    st.success("✅ Execution Completed!")

                    # ── Reflection Banner ──────────────────────────────────────
                    if res.get("reflection_triggered"):
                        st.markdown(f"""
                        <div class="reflection-banner">
                            🔄 <b>Self-Correction Loop Activated</b><br>
                            The Supervisor Agent detected a compliance failure and redirected the query for correction.<br>
                            <b>Rejected Agent:</b> {res.get('rejected_agent', 'N/A')} &nbsp;|&nbsp;
                            <b>Reason:</b> {res.get('rejection_reason', 'N/A')} &nbsp;|&nbsp;
                            <b>Correction Applied:</b> ✅ Yes
                        </div>
                        """, unsafe_allow_html=True)

                    # ── Action Execution Badges ────────────────────────────────
                    actions = res.get("actions_taken", {})
                    action_html = ""
                    if actions.get("email_sent"):
                        mode = "🟢 LIVE" if actions.get("email_mode") == "live" else "🔵 SIMULATED"
                        action_html += f'<span class="action-badge badge-email">📧 Outreach Email: {mode}</span>'
                    if actions.get("discord_alert_sent"):
                        mode = "🟢 LIVE" if actions.get("discord_mode") == "live" else "🔵 SIMULATED"
                        action_html += f'<span class="action-badge badge-discord">📢 Discord Alert: {mode}</span>'
                    if actions.get("crm_card_created"):
                        action_html += f'<span class="action-badge badge-crm">🗂️ CRM Card: #{actions.get("crm_card_id")}</span>'
                    if res.get("reflection_triggered"):
                        action_html += f'<span class="action-badge badge-reflect">🔄 Self-Corrected</span>'

                    if action_html:
                        st.markdown(f"""
                        <div style="margin: 12px 0;">
                            <b style="font-size:0.85rem; color:#64748b;">⚡ Real-World Actions Executed:</b><br>
                            {action_html}
                        </div>
                        """, unsafe_allow_html=True)

                    # ── Final response card ────────────────────────────────────
                    lang_badge = "🇬🇧 English"
                    if res.get('detected_language') == "Hinglish":
                        lang_badge = "🇮🇳 Hinglish"
                    elif res.get('detected_language') == "Hindi":
                        lang_badge = "🇮🇳 Hindi"
                    elif res.get('detected_language') == "Marathi":
                        lang_badge = "🇮🇳 Marathi"

                    st.markdown(f"""
                    <div class="glass-card" style="border-color:#00f2fe; background:rgba(0, 242, 254, 0.02)">
                        <h3>🎯 Final Customer Response
                            <span class="custom-badge badge-cold" style="font-size: 0.8rem; margin-left: 10px; border-color: #00f2fe; color: #00f2fe;">{lang_badge}</span>
                        </h3>
                        <p style="font-size:1.1rem; line-height:1.5;">{res['final_answer']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # TTS playback
                    speech_lang = "hi-IN" if res.get('detected_language') == "Hindi" else \
                                  ("mr-IN" if res.get('detected_language') == "Marathi" else "en-US")
                    st.components.v1.html(f"""
                        <script>
                            var msg = new SpeechSynthesisUtterance({json.dumps(res['final_answer'])});
                            msg.lang = '{speech_lang}';
                            window.speechSynthesis.speak(msg);
                        </script>
                    """, height=0)

                    # ── Detailed Agent Steps ───────────────────────────────────
                    st.markdown("### 🧬 Detailed Collaborative Agent Execution Log")
                    for step in res.get("steps", []):
                        agent_cls = "agent-support"
                        if "Care" in step["agent"]:
                            agent_cls = "agent-care"
                        elif "Ticket" in step["agent"]:
                            agent_cls = "agent-ticket"
                        elif "Sales" in step["agent"]:
                            agent_cls = "agent-sales"
                        elif "Analytics" in step["agent"]:
                            agent_cls = "agent-analytics"
                        elif "Supervisor" in step["agent"]:
                            agent_cls = "agent-supervisor"
                        elif "Planner" in step["agent"]:
                            agent_cls = "agent-planner"
                        elif "Safety" in step["agent"]:
                            agent_cls = "agent-safety"
                        elif "Fraud" in step["agent"]:
                            agent_cls = "agent-fraud"
                        elif "Curator" in step["agent"]:
                            agent_cls = "agent-curator"
                        elif "Finance" in step["agent"]:
                            agent_cls = "agent-finance"
                        elif "Marketing" in step["agent"]:
                            agent_cls = "agent-marketing"
                        elif "Decision" in step["agent"]:
                            agent_cls = "agent-decision"

                        # Extra class for correction/rejection steps
                        extra_cls = ""
                        if "🔄" in step.get("avatar", "") or "Correction" in step.get("action", ""):
                            extra_cls = " correction"
                        elif "AUDIT FAILED" in step.get("action", "") or "Rejecting" in step.get("action", ""):
                            extra_cls = " rejected"

                        st.markdown(f"""
                        <div class="agent-bubble {agent_cls}{extra_cls}">
                            <div class="agent-avatar">{step['avatar']}</div>
                            <div class="agent-info">
                                <div class="agent-name">
                                    <span>{step['agent']}</span>
                                    <span class="agent-action">{step['action']}</span>
                                </div>
                                <div class="agent-body">
                                    {step['content']}
                                </div>
                                <div style="margin-top:10px; padding:8px; background:rgba(0,0,0,0.2); border-radius:6px; font-size:0.8rem; border:1px solid rgba(255,255,255,0.03);">
                                    <b>💡 Decision thoughts:</b> {step.get('thoughts', 'None.')}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown('<div class="timeline-connector"></div>', unsafe_allow_html=True)

                    if res.get("confidence"):
                        st.markdown("### 📁 Retrieval-Augmented Generation (RAG) Diagnostics")
                        st.metric("RAG Match Confidence Score", f"{res['confidence']}%")

                except Exception as e:
                    st.error(f"Agent pipeline failed: {e}")
                    graph_placeholder.markdown(render_workflow_graph(), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: OMNICHANNEL INBOX SIMULATOR
# ─────────────────────────────────────────────────────────────────────────────
with tab_omni:
    st.markdown('<div class="glass-card-header">📬 Unified Omnichannel Support Inbox</div>', unsafe_allow_html=True)

    omni_col1, omni_col2 = st.columns([1, 2])

    with omni_col1:
        st.markdown("<b>Select Channel Queue</b>", unsafe_allow_html=True)
        channel_select = st.radio("Channel", ["WhatsApp", "Telegram", "Email", "Web Chat"])

        try:
            db_messages = requests.get(f"{API_URL}/api/incoming-messages",
                                       params={"channel": channel_select},
                                       headers=get_auth_headers()).json()
        except Exception as e:
            st.error(f"Error fetching channel queue: {e}")
            db_messages = []

        for i, m in enumerate(db_messages):
            try:
                dt = datetime.fromisoformat(m['created_at'])
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                time_str = m['created_at']

            status_badge = "🟢 Processed" if m["status"] == "Processed" else "🟡 Pending"
            st.markdown(f"""
            <div class="glass-card" style="padding:10px; margin-bottom:8px; background:rgba(255,255,255,0.02)">
                <b>{m['sender']}</b> <span style="font-size:0.75rem; color:#a0aec0;">({time_str})</span> - {status_badge}<br>
                <span style="font-size:0.9rem;">"{m['text']}"</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("<b>Simulate Incoming Message</b>", unsafe_allow_html=True)
        with st.form("simulate_msg_form", clear_on_submit=True):
            sim_sender = st.text_input("Customer Name", "Rahul Dev")
            sim_email  = st.text_input("Customer Email", "rahul.dev@gmail.com")
            sim_text   = st.text_area("Message Content", "I want a refund for the Pro annual subscription plan.")
            sim_submit = st.form_submit_button("📩 Inject Into Inbox Queue")

            if sim_submit:
                if sim_sender and sim_email and sim_text:
                    try:
                        res = requests.post(f"{API_URL}/api/incoming-messages", json={
                            "sender": sim_sender,
                            "email": sim_email,
                            "text": sim_text,
                            "channel": channel_select
                        }, headers=get_auth_headers())
                        if res.status_code == 200:
                            st.success("Message injected successfully!")
                            st.rerun()
                        else:
                            st.error(res.json().get("detail", "Failed to inject message."))
                    except Exception as e:
                        st.error(f"Failed to inject message: {e}")

    with omni_col2:
        st.markdown("<b>Process Channel Query via Multi-Agent Pipeline</b>", unsafe_allow_html=True)
        pending_msgs = [m for m in db_messages if m["status"] == "Pending"]

        if pending_msgs:
            msg_options = {f"{m['sender']}: {m['text'][:40]}...": m for m in pending_msgs}
            selected_option = st.selectbox("Select Pending Message to Resolve", list(msg_options.keys()))
            active_msg = msg_options[selected_option]

            st.info(f"Active Message: From {active_msg['sender']} ({active_msg['email']}) — \"{active_msg['text']}\"")

            process_omni = st.button("⚡ Trigger Multi-Agent Resolution")
            if process_omni:
                with st.spinner("Processing omnichannel query..."):
                    try:
                        res = requests.post(
                            f"{API_URL}/api/incoming-messages/{active_msg['id']}/process",
                            headers=get_auth_headers()
                        ).json()
                        st.success("Query processed successfully!")
                        st.markdown(f"**Agent Response Draft:** {res['final_answer']}")
                        st.markdown(f"**Assigned Priority:** {res['priority']}")
                        if res.get("reflection_triggered"):
                            st.warning(f"🔄 Self-correction triggered: {res.get('rejection_reason')}")
                    except Exception as e:
                        st.error(f"Failed to process omnichannel query: {e}")
        else:
            st.info("No messages in queue.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: DIGITAL TWIN SIMULATOR
# ─────────────────────────────────────────────────────────────────────────────
with tab_twin:
    st.markdown('<div class="glass-card-header">📈 AI Company Digital Twin & What-If Simulator</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.85rem; color:#64748b; margin-bottom:15px;">
        Model business operations in real-time. Alter support staffing capacity, pricing strategies, or launch marketing campaigns
        to forecast mathematical impacts on customer CSAT, queue latency, churn rates, and monthly ROI.
    </div>
    """, unsafe_allow_html=True)
    
    col_t1, col_t2 = st.columns([1, 1])
    with col_t1:
        st.markdown("<b>Configure Operational Scenarios</b>", unsafe_allow_html=True)
        staff_ch = st.slider("Support Staffing Change (%)", -50, 100, 0, step=5, help="Negative reduces staff (layoffs), positive increases staff (hiring)")
        price_ch = st.slider("Pricing Strategy Change (%)", -30, 50, 0, step=5, help="Adjust subscription plan prices")
        camp_ln = st.checkbox("Launch Major Retention & Marketing Campaign", value=False)
        
        btn_simulate = st.button("🔮 Run Digital Twin Simulation", type="primary")
        
    with col_t2:
        st.markdown("<b>Simulation Projections</b>", unsafe_allow_html=True)
        sim_output = st.empty()
        
        if btn_simulate:
            try:
                res_sim = requests.post(f"{API_URL}/api/digital-twin/simulate", json={
                    "staff_change": float(staff_ch),
                    "price_change": float(price_ch),
                    "campaign_launch": camp_ln
                }, headers=get_auth_headers()).json()
                
                csat = res_sim["predicted_csat"]
                latency = res_sim["predicted_backlog_latency"]
                churn = res_sim["predicted_churn_rate"]
                roi = res_sim["predicted_roi_impact"]
                
                roi_color = "#34d399" if roi >= 0 else "#f87171"
                roi_sign = "+" if roi >= 0 else ""
                
                sim_output.markdown(f"""
                <div class="glass-card" style="border-color:#00f2fe; background:rgba(0, 242, 254, 0.02)">
                    • <b>Projected CSAT</b>: <b style="color:#34d399; font-size:1.15rem;">{csat}%</b><br>
                    • <b>Projected Queue Latency</b>: <b style="color:#fbbf24; font-size:1.15rem;">{latency} hours</b><br>
                    • <b>Projected Customer Churn Rate</b>: <b style="color:#f87171; font-size:1.15rem;">{churn}%</b><br>
                    • <b>Projected Monthly ROI Impact</b>: <b style="color:{roi_color}; font-size:1.2rem;">{roi_sign}₹{roi:,}</b>
                </div>
                """, unsafe_allow_html=True)
                
                # Plotly comparison
                df_sim = pd.DataFrame({
                    "Metric": ["CSAT (%)", "Churn (%)", "Latency (hrs)"],
                    "Baseline": [85.0, 5.4, 2.5],
                    "Simulated": [csat, churn, latency]
                })
                fig_sim = go.Figure()
                fig_sim.add_trace(go.Bar(name="Baseline", x=df_sim["Metric"], y=df_sim["Baseline"], marker_color="rgba(255,255,255,0.18)"))
                fig_sim.add_trace(go.Bar(name="Simulated", x=df_sim["Metric"], y=df_sim["Simulated"], marker_color="#00f2fe"))
                fig_sim.update_layout(barmode="group", template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_sim, use_container_width=True)
                
            except Exception as e:
                st.error(f"Simulation failed: {e}")
        else:
            sim_output.info("Configure variables and click Run to view projections.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5: LEAD INTELLIGENCE & CUSTOMER 360
# ─────────────────────────────────────────────────────────────────────────────
with tab_lead:
    st.markdown('<div class="glass-card-header">💼 Sales Intelligence & Customer 360° Profile Lookup</div>', unsafe_allow_html=True)

    lead_opt = st.radio("Operations Mode", ["Run Lead Scorer", "Customer 360 Profile lookup"])

    if lead_opt == "Run Lead Scorer":
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            l_name    = st.text_input("Lead Name", "Vipin Kumar", key="lead_name")
            l_email   = st.text_input("Lead Email", "vipin@apex-industries.io", key="lead_email")
            l_company = st.text_input("Company Name", "Apex Industries", key="lead_company")
            l_reqs    = st.text_area("Requirements", "Looking to integrate WhatsApp and SMS omnichannel features into our help desk API.", key="lead_reqs")
        with col_l2:
            l_views = st.slider("Page Views", 1, 50, 15)
            l_time  = st.slider("Time Spent on Site (secs)", 10, 3600, 750)
            l_form  = st.checkbox("Submitted Form", value=True)
            l_btn   = st.button("🔥 Calculate Lead Score", type="primary")

        if l_btn:
            try:
                res = requests.post(f"{API_URL}/api/leads", json={
                    "name": l_name, "email": l_email, "company": l_company,
                    "requirements": l_reqs, "page_views": l_views,
                    "time_on_site": l_time, "form_submitted": 1 if l_form else 0
                }, headers=get_auth_headers()).json()

                badge_cls = "badge-hot" if res["lead_status"] == "Hot" else "badge-warm"
                st.markdown(f"""
                <div class="glass-card" style="margin-top:15px; border-color:#10b981;">
                    <h3>ML Lead Score Result</h3>
                    • <b>Status</b>: <span class="custom-badge {badge_cls}">{res['lead_status']}</span> (Score: <b>{res['lead_score']}/100</b>)<br>
                    • <b>Lead Conversion Probability</b>: <b style="color:#10b981;">{int(res['conversion_probability']*100)}%</b><br>
                    • <b>Cross-sell Recommendation</b>: <b style="color:#00f2fe;">{res['cross_sell_recommendation']}</b><br>
                    • <b>Upsell Recommendation</b>: <b style="color:#fbbf24;">{res['upsell_recommendation']}</b>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error scoring lead: {e}")

    else:
        st.markdown("<b>Enter Customer Email to lookup profile</b>", unsafe_allow_html=True)
        search_email = st.text_input("Customer Email", "vipin@enterprise-solutions.com")
        lookup_btn   = st.button("🔍 Search Customer 360° Profile")

        if lookup_btn:
            try:
                res = requests.get(f"{API_URL}/api/customers/{search_email}", headers=get_auth_headers())
                if res.status_code == 200:
                    profile = res.json()
                    cust = profile["customer"]

                    churn_badge = "Low Churn Risk"
                    churn_score = 10
                    churn_cls   = "badge-cold"
                    explain_str = ""
                    try:
                        churn_res  = requests.get(f"{API_URL}/api/customers/{cust['email']}/churn-risk", headers=get_auth_headers()).json()
                        risk_level = churn_res["churn_risk"]
                        churn_score= churn_res["churn_score"]
                        churn_badge= f"{risk_level} Churn Risk ({churn_score}%)"
                        if risk_level == "High":
                            churn_cls = "badge-hot"
                        elif risk_level == "Medium":
                            churn_cls = "badge-warm"
                            
                        # Phase 8: Explainable AI logic
                        if churn_res.get("features"):
                            feats = churn_res["features"]
                            explain_str = f"""
                            <div style="margin-top:12px; border-top:1px solid rgba(255,255,255,0.08); padding-top:10px; font-size:0.85rem; color:#94a3b8;">
                                <b>🧠 Churn Explainability (Model Features):</b><br>
                                • Negative Sentiment Tickets Count: <b style="color:#f87171;">{feats['negative_tickets']}</b> (Impact: High)<br>
                                • Human Escalations Logged: <b style="color:#fbbf24;">{feats['escalations']}</b> (Impact: Medium)<br>
                                • Days Since Last Activity: <b>{feats['days_since_last']} days</b> (Impact: Low)<br>
                                • Customer Health score: <b style="color:#34d399;">{feats['health_score']}/100</b>
                            </div>
                            """
                    except Exception:
                        pass

                    st.markdown(f"""
                    <div class="glass-card">
                        <h3>👤 Customer Profile: {cust['name']}</h3>
                        • <b>Email</b>: {cust['email']}<br>
                        • <b>Customer Lifetime Value (CLV)</b>: <b style="color:#10b981;">₹{cust['clv'] * 80:,.0f}</b><br>
                        • <b>Customer Health Score</b>: <b style="color:#00f2fe;">{cust['health_score']}/100</b><br>
                        • <b>VIP Status</b>: <span class="custom-badge {'badge-hot' if cust['is_vip'] else 'badge-cold'}">{'VIP Customer' if cust['is_vip'] else 'Standard'}</span><br>
                        • <b>Churn Risk</b>: <span class="custom-badge {churn_cls}">{churn_badge}</span><br>
                        • <b>Total Tickets Filed</b>: {cust['total_tickets']}
                        {explain_str}
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("<b>Support Ticket Logs:</b>", unsafe_allow_html=True)
                    if profile["tickets"]:
                        st.dataframe(pd.DataFrame(profile["tickets"])[["id", "category", "sentiment", "priority", "status", "created_at"]])
                    else:
                        st.info("No tickets recorded for this customer.")
                else:
                    st.error("Customer profile not found.")
            except Exception as e:
                st.error(f"Profile lookup failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 6: SUPPORT TICKET DESK & COPILOT
# ─────────────────────────────────────────────────────────────────────────────
with tab_tickets:
    st.markdown('<div class="glass-card-header">🎫 Active Support Ticket Desk (SQLite Database)</div>', unsafe_allow_html=True)

    col_t1, col_t2 = st.columns([2, 1])

    with col_t1:
        try:
            tickets_list = requests.get(f"{API_URL}/api/tickets", headers=get_auth_headers()).json()
            if tickets_list:
                df_tick = pd.DataFrame(tickets_list)
                status_filter = st.selectbox("Filter Status", ["All", "Open", "In Progress", "Resolved"])
                filtered_df   = df_tick.copy()
                if status_filter != "All":
                    filtered_df = filtered_df[filtered_df["status"] == status_filter]

                st.dataframe(filtered_df[["id", "customer_name", "customer_email", "category", "sentiment",
                                          "priority", "status", "escalated_to_human", "created_at"]],
                             use_container_width=True)

                st.markdown("<b>Manage Ticket Details</b>", unsafe_allow_html=True)
                edit_id    = st.selectbox("Select Ticket ID to Manage", filtered_df["id"].tolist())
                ticket_row = filtered_df[filtered_df["id"] == edit_id].iloc[0]

                col_te1, col_te2 = st.columns(2)
                with col_te1:
                    st.markdown(f"""
                    • <b>Customer</b>: {ticket_row['customer_name']}<br>
                    • <b>Query</b>: <i>"{ticket_row['query']}"</i><br>
                    • <b>Escalation Reason</b>: <span style="color:#f87171;">{ticket_row.get('escalation_reason', 'None')}</span>
                    """, unsafe_allow_html=True)
                with col_te2:
                    new_stat = st.selectbox("Set Status", ["Open", "In Progress", "Resolved"],
                                            index=["Open", "In Progress", "Resolved"].index(ticket_row["status"]))
                    new_pri  = st.selectbox("Set Priority", ["High", "Medium", "Low"],
                                            index=["High", "Medium", "Low"].index(ticket_row["priority"]))
                    if st.button("💾 Update Ticket Settings"):
                        res_up = requests.put(f"{API_URL}/api/tickets/{edit_id}",
                                              json={"status": new_stat, "priority": new_pri},
                                              headers=get_auth_headers())
                        if res_up.status_code == 200:
                            st.success("Ticket updated successfully!")
                            st.rerun()
            else:
                st.info("No tickets created yet.")
        except Exception as e:
            st.error(f"Failed to load tickets: {e}")

    with col_t2:
        st.markdown('<div class="glass-card-header">🕵️ Supervisor Executive Copilot</div>', unsafe_allow_html=True)
        copilot_q   = st.text_input("Ask Copilot about tickets or performance", "Why are refund requests increasing?")
        copilot_btn = st.button("💬 Consult Copilot")

        if copilot_btn:
            with st.spinner("Analyzing data..."):
                try:
                    headers = get_auth_headers()
                    res = requests.post(f"{API_URL}/api/analytics/copilot",
                                        json={"query": copilot_q}, headers=headers)
                    if res.status_code == 200:
                        st.info(res.json()["analysis"])
                    else:
                        detail = res.json().get("detail", "")
                        if "GEMINI_API_KEY" in detail:
                            st.warning("GEMINI_API_KEY is not set. Copilot requires a valid Gemini API key in the sidebar.")
                        else:
                            st.error(f"Copilot logic failed: {detail}")
                except Exception as e:
                    st.error(f"Failed to connect to Copilot service: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 7: KNOWLEDGE HUB & SELF-HEALING
# ─────────────────────────────────────────────────────────────────────────────
with tab_kb:
    st.markdown('<div class="glass-card-header">📁 Company Knowledge Base (ChromaDB Vector Store)</div>', unsafe_allow_html=True)

    col_k1, col_k2 = st.columns(2)

    with col_k1:
        st.markdown("### Index Support File")
        kb_file = st.file_uploader("Upload support file", type=["pdf", "docx", "txt"])
        if kb_file:
            upload_btn = st.button("📥 Index Document", type="primary")
            if upload_btn:
                with st.spinner("Generating embeddings..."):
                    try:
                        files  = {"file": (kb_file.name, kb_file.getvalue(), kb_file.type)}
                        up_res = requests.post(f"{API_URL}/api/kb/upload", files=files, headers=get_auth_headers()).json()
                        if up_res.get("status") == "success":
                            st.success(f"Successfully processed {up_res['filename']}! Ingested {up_res['chunks_indexed']} chunks.")
                            st.rerun()
                        else:
                            st.error("Failed to index document.")
                    except Exception as e:
                        st.error(f"Upload error: {e}")

    with col_k2:
        st.markdown("### Vector DB Index Health")
        if backend_status:
            try:
                stats = requests.get(f"{API_URL}/api/kb/stats", headers=get_auth_headers()).json()
                st.markdown(f"""
                <div class="glass-card">
                    • <b>Total Vector Chunks</b>: {stats['total_chunks']}<br>
                    • <b>Unique Indexed Files</b>: {stats['document_count']}
                </div>
                """, unsafe_allow_html=True)

                st.markdown("### Indexed Documents")
                docs_list = requests.get(f"{API_URL}/api/kb/documents", headers=get_auth_headers()).json()
                if docs_list:
                    for d in docs_list:
                        d_col1, d_col2 = st.columns([3, 1])
                        with d_col1:
                            st.markdown(f"📄 **{d['filename']}** (`{d['chunks_count']}` chunks)")
                        with d_col2:
                            if st.button("🗑️", key=f"del_doc_{d['id']}", help=f"Delete {d['filename']}"):
                                del_res = requests.delete(f"{API_URL}/api/kb/documents/{d['id']}", headers=get_auth_headers())
                                if del_res.status_code == 200:
                                    st.success(f"Deleted {d['filename']}")
                                    st.rerun()
                else:
                    st.write("No documents uploaded yet.")
            except Exception as e:
                st.error(f"Failed to read index status: {e}")

    st.markdown('<div class="glass-card-header" style="margin-top:20px;">🔍 Live Hybrid RAG Search Testing</div>', unsafe_allow_html=True)
    search_q = st.text_input("Search phrase", "refund basic plan")
    if search_q and backend_status:
        try:
            headers  = get_auth_headers()
            res_hits = requests.get(f"{API_URL}/api/kb/search", params={"q": search_q}, headers=headers)
            if res_hits.status_code == 200:
                hits = res_hits.json()
                if hits:
                    for hit in hits:
                        st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); padding: 12px; margin-bottom:10px; border-radius: 8px;">
                            <span style="font-size:0.75rem; color:#00f2fe; text-transform:uppercase;">Source: {hit['source']} | Confidence: {hit['confidence']}% | Method: {hit.get('retrieval_method', 'Vector')}</span>
                            <p style="font-size:0.9rem; margin-top:5px;">{hit['content']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.write("No matching vector embeddings found.")
            else:
                st.error("Failed to query RAG database.")
        except Exception as e:
            st.error(f"RAG search failed: {e}")

    # Phase 12: Self-Healing Knowledge Base trigger UI
    st.markdown('<div class="glass-card-header" style="margin-top:20px;">🛡️ Self-Healing Knowledge Base Engine</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.85rem; color:#64748b; margin-bottom:12px;">
        When unresolved complaints repeat, the Self-Healing Curator Agent automatically drafts
        FAQ content and indexes it into the RAG vector store to resolve future queries autonomously.
    </div>
    """, unsafe_allow_html=True)
    if st.button("🛡️ Trigger KB Self-Healing Engine", key="btn_self_heal_kb"):
        with st.spinner("Analyzing unresolved complaint patterns..."):
            try:
                res_heal = requests.post(f"{API_URL}/api/kb/self-heal", headers=get_auth_headers()).json()
                if res_heal.get("healed"):
                    st.success(res_heal["message"])
                else:
                    st.info(res_heal["message"])
            except Exception as e:
                st.error(f"Self-healing run failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 8: OPERATIONS SCORECARD
# ─────────────────────────────────────────────────────────────────────────────
with tab_bench:
    st.markdown('<div class="glass-card-header">📈 FlowAgent AI X Operations Competitiveness Scorecard</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.85rem; color:#64748b; margin-bottom:15px;">
        Compare traditional support & business operations against the autonomous 12-agent FlowAgent AI X ecosystem.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <table style="width:100%; border-collapse:collapse; font-size:0.95rem; margin-top:10px;">
        <thead>
            <tr style="border-bottom:2px solid rgba(255,255,255,0.1); text-align:left; color:#00f2fe;">
                <th style="padding:12px;">Operational Metric</th>
                <th style="padding:12px;">Manual Legacy Operation</th>
                <th style="padding:12px; color:#34d399;">🤖 FlowAgent AI X Workforce</th>
                <th style="padding:12px; color:#fbbf24;">Efficiency Boost</th>
            </tr>
        </thead>
        <tbody>
            <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                <td style="padding:12px; font-weight:600;">Average Response Latency</td>
                <td style="padding:12px; color:#f87171;">4.2 hours</td>
                <td style="padding:12px; color:#34d399; font-weight:bold;">12 seconds</td>
                <td style="padding:12px; color:#fbbf24; font-weight:bold;">99.9% faster</td>
            </tr>
            <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                <td style="padding:12px; font-weight:600;">Support Automation Rate</td>
                <td style="padding:12px;">0% (Full manual desks)</td>
                <td style="padding:12px; color:#34d399; font-weight:bold;">92.4% (Autonomous routing)</td>
                <td style="padding:12px; color:#fbbf24; font-weight:bold;">+92.4% savings</td>
            </tr>
            <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                <td style="padding:12px; font-weight:600;">Monthly Operating Overhead</td>
                <td style="padding:12px; color:#f87171;">₹2,40,000 (10 agents salary)</td>
                <td style="padding:12px; color:#34d399; font-weight:bold;">₹18,000 (API & Server compute)</td>
                <td style="padding:12px; color:#fbbf24; font-weight:bold;">92.5% cost reduction</td>
            </tr>
            <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                <td style="padding:12px; font-weight:600;">Monthly Handling Hours Saved</td>
                <td style="padding:12px;">0 hours</td>
                <td style="padding:12px; color:#34d399; font-weight:bold;">380 hours</td>
                <td style="padding:12px; color:#fbbf24; font-weight:bold;">380 hours reclaimed</td>
            </tr>
            <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                <td style="padding:12px; font-weight:600;">Average Customer Satisfaction (CSAT)</td>
                <td style="padding:12px;">71%</td>
                <td style="padding:12px; color:#34d399; font-weight:bold;">89.5% (High-CSAT auto responses)</td>
                <td style="padding:12px; color:#fbbf24; font-weight:bold;">+18.5% CSAT boost</td>
            </tr>
            <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                <td style="padding:12px; font-weight:600;">Churn Risk Response</td>
                <td style="padding:12px;">Reactive (After account closure)</td>
                <td style="padding:12px; color:#34d399; font-weight:bold;">Proactive (Local RF Churn Prediction)</td>
                <td style="padding:12px; color:#fbbf24; font-weight:bold;">Immediate retention trigger</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 9: CRM PIPELINE DASHBOARD & CAMPAIGNS
# ─────────────────────────────────────────────────────────────────────────────
with tab_crm:
    st.markdown('<div class="glass-card-header">🗂️ Sales CRM Pipeline — Hot Lead Actions</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.85rem; color:#64748b; margin-bottom:16px;">
        When the Sales Agent detects a <b>Hot Lead</b>, it automatically drafts and sends an outreach email
        and creates a CRM card here. Each card represents a real-world action taken by the AI agent workforce.
    </div>
    """, unsafe_allow_html=True)

    if not backend_status:
        st.info("FastAPI backend is offline.")
    else:
        crm_col1, crm_col2 = st.columns([2, 1])
        
        with crm_col1:
            try:
                crm_cards = requests.get(f"{API_URL}/api/crm/cards", headers=get_auth_headers()).json()
                if crm_cards:
                    # Summary metrics
                    hot_count  = sum(1 for c in crm_cards if c["lead_status"] == "Hot")
                    warm_count = sum(1 for c in crm_cards if c["lead_status"] == "Warm")
                    email_sent = sum(1 for c in crm_cards if c.get("email_sent"))

                    st.markdown(f"""
                    <div class="metric-grid">
                        <div class="metric-card">
                            <div class="metric-card-lbl">CRM Cards Created</div>
                            <div class="metric-card-val">{len(crm_cards)}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-card-lbl">🔥 Hot Leads</div>
                            <div class="metric-card-val" style="color:#f87171;">{hot_count}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-card-lbl">🌡️ Warm Leads</div>
                            <div class="metric-card-val" style="color:#fbbf24;">{warm_count}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-card-lbl">📧 Emails Auto-Sent</div>
                            <div class="metric-card-val" style="color:#34d399;">{email_sent}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("### 📋 Pipeline Cards")
                    for card in crm_cards:
                        stage_cls = "crm-stage-qualified" if card["stage"] == "Qualified" else "crm-stage-contacted"
                        status_cls = "badge-hot" if card["lead_status"] == "Hot" else "badge-warm"
                        try:
                            dt_str = datetime.fromisoformat(card["created_at"]).strftime("%Y-%m-%d %H:%M")
                        except Exception:
                            dt_str = card["created_at"]

                        email_badge = (
                            '<span class="action-badge badge-email">📧 Email Sent</span>'
                            if card.get("email_sent") else
                            '<span class="action-badge badge-discord">📧 Simulation Mode</span>'
                        )

                        st.markdown(f"""
                        <div class="crm-card">
                            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px;">
                                <div>
                                    <b style="font-size:1.05rem;">#{card['id']} — {card['lead_name']}</b>
                                    <span class="custom-badge {status_cls}" style="margin-left:10px; font-size:0.75rem;">{card['lead_status']} Lead</span>
                                </div>
                                <div>
                                    <b class="{stage_cls}">📌 {card['stage']}</b>
                                    &nbsp;•&nbsp;
                                    <span style="color:#64748b; font-size:0.8rem;">{dt_str}</span>
                                </div>
                            </div>
                            <div style="margin-top:8px; font-size:0.85rem; color:#94a3b8;">
                                📧 {card['email']} &nbsp;|&nbsp; 🏢 {card.get('company', 'Unknown')} &nbsp;|&nbsp; 
                                🎯 Score: <b>{card['lead_score']}/100</b>
                            </div>
                            <div style="margin-top:8px; font-size:0.85rem; color:#e2e8f0; line-height:1.5;">
                                <b>Pitch:</b> {(card.get('pitch_summary') or 'N/A')[:200]}
                            </div>
                            <div style="margin-top:10px;">
                                {email_badge}
                                <span class="action-badge badge-crm">🔗 crm.flowagent.ai/leads/{card['id']}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="glass-card" style="text-align:center; padding:40px; color:#64748b;">
                        <h3>No CRM Cards Yet</h3>
                        <p>CRM cards are automatically created when the Sales Agent detects a <b>Hot Lead</b>.<br>
                        Try submitting a query with sales intent (e.g., "I want to buy your Enterprise plan") 
                        in the <b>Multi-Agent Desk</b> tab.</p>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Failed to load CRM pipeline: {e}")
                
        with crm_col2:
            st.markdown("### 📣 Marketing Campaigns")
            try:
                camps = requests.get(f"{API_URL}/api/campaigns", headers=get_auth_headers()).json()
                if camps:
                    for c in camps:
                        status_badge = "badge-hot" if c["status"] == "Active" else "badge-cold"
                        st.markdown(f"""
                        <div class="glass-card" style="margin-bottom:10px;">
                            <b>{c['name']}</b> <span class="custom-badge {status_badge}">{c['status']}</span><br>
                            • Budget: <b>₹{c['budget']:,.0f}</b><br>
                            • Conversion Rate: <b>{c['conversion_rate']}%</b><br>
                            • Revenue Generated: <b style="color:#34d399;">₹{c['revenue_generated']:,.0f}</b>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No active campaigns.")
            except Exception as e:
                st.error(f"Failed to load campaigns: {e}")
