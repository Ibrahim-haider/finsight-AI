import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinSight AI",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&display=swap');

    .stApp { background-color: #0d0d0d; color: #f0f0f0; }
    .block-container { padding: 2rem 2rem 2rem; }

    .metric-card {
        background: #161616;
        border: 1px solid #2a2a2a;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
    }
    .metric-label { font-size: 0.72rem; color: #888; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 6px; }
    .metric-value { font-size: 1.8rem; font-weight: 900; line-height: 1.1; }
    .metric-sub   { font-size: 0.78rem; color: #888; margin-top: 4px; }

    .ai-box {
        background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
        border: 1px solid #2a3a5c;
        border-radius: 16px;
        padding: 24px;
        margin-top: 8px;
    }
    .ai-badge {
        background: linear-gradient(135deg, #4cc9f0, #a855f7);
        color: white;
        font-size: 0.7rem;
        font-weight: 800;
        padding: 4px 12px;
        border-radius: 100px;
        letter-spacing: 1px;
        display: inline-block;
        margin-bottom: 10px;
    }
    .tip-box {
        background: rgba(255,255,255,0.04);
        border-radius: 10px;
        padding: 12px 14px;
        margin-top: 8px;
        font-size: 0.88rem;
        color: #b0bcc8;
        line-height: 1.6;
    }
    .logo { font-size: 2rem; font-weight: 900; color: #f0f0f0; }
    .logo span { color: #00e599; }

    div[data-testid="stSidebar"] { background-color: #111111 !important; }
    div[data-testid="stSidebar"] .stMarkdown { color: #f0f0f0; }
    .stButton > button {
        background: #00e599 !important;
        color: #000 !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 8px 20px !important;
    }
    .stSelectbox label, .stNumberInput label, .stTextInput label { color: #888 !important; font-size: 0.8rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Data helpers ──────────────────────────────────────────────────────────────
DATA_FILE = "transactions.json"
CATEGORY_COLORS = {
    "Food": "#ff9f43", "Transport": "#4cc9f0", "Shopping": "#ff6b9d",
    "Bills": "#ffd166", "Health": "#00e599", "Entertainment": "#a855f7",
    "Education": "#06d6a0", "Salary": "#00e599", "Other": "#888888"
}
CATEGORY_ICONS = {
    "Food": "🍔", "Transport": "🚗", "Shopping": "🛍️", "Bills": "💡",
    "Health": "💊", "Entertainment": "🎮", "Education": "📚",
    "Salary": "💼", "Other": "📦"
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return [
        {"name": "Salary",      "amount": 50000, "type": "income",  "cat": "Salary",        "date": "2026-04-01"},
        {"name": "Grocery",     "amount": 8000,  "type": "expense", "cat": "Food",          "date": "2026-04-03"},
        {"name": "Uber",        "amount": 1200,  "type": "expense", "cat": "Transport",     "date": "2026-04-05"},
        {"name": "Netflix",     "amount": 1500,  "type": "expense", "cat": "Entertainment", "date": "2026-04-07"},
        {"name": "Electricity", "amount": 3500,  "type": "expense", "cat": "Bills",         "date": "2026-04-10"},
        {"name": "Lunch",       "amount": 600,   "type": "expense", "cat": "Food",          "date": "2026-04-12"},
    ]

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def fmt(n):
    return f"Rs {n:,.0f}"

# ── Session state ─────────────────────────────────────────────────────────────
if "transactions" not in st.session_state:
    st.session_state.transactions = load_data()
if "ai_result" not in st.session_state:
    st.session_state.ai_result = None

txs = st.session_state.transactions
df  = pd.DataFrame(txs) if txs else pd.DataFrame(columns=["name","amount","type","cat","date"])

# ── Computed stats ────────────────────────────────────────────────────────────
income  = df[df["type"]=="income"]["amount"].sum()  if not df.empty else 0
spent   = df[df["type"]=="expense"]["amount"].sum() if not df.empty else 0
savings = income - spent
rate    = round((savings / income * 100)) if income > 0 else 0
expenses_df = df[df["type"]=="expense"] if not df.empty else pd.DataFrame()

# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="logo">Fin<span>Sight</span> AI</div>', unsafe_allow_html=True)
    st.caption("Personal Budget Dashboard")
    st.divider()

    st.subheader("➕ Add Transaction")
    tx_name   = st.text_input("Description", placeholder="e.g. Grocery, Salary")
    tx_amount = st.number_input("Amount (Rs)", min_value=0.0, step=100.0)
    tx_type   = st.selectbox("Type", ["expense", "income"])
    tx_cat    = st.selectbox("Category", list(CATEGORY_ICONS.keys()))

    if st.button("Add Transaction", use_container_width=True):
        if tx_name and tx_amount > 0:
            new_tx = {
                "name":   tx_name,
                "amount": tx_amount,
                "type":   tx_type,
                "cat":    tx_cat,
                "date":   datetime.today().strftime("%Y-%m-%d")
            }
            st.session_state.transactions.insert(0, new_tx)
            save_data(st.session_state.transactions)
            st.success("✅ Transaction added!")
            st.rerun()
        else:
            st.warning("Please fill in name and amount.")

    st.divider()

    # CSV Upload
    st.subheader("📂 Import CSV")
    uploaded = st.file_uploader("Upload bank statement CSV", type=["csv"])
    if uploaded:
        try:
            imp = pd.read_csv(uploaded)
            st.write(imp.head(3))
            st.info("Map your columns below then click Import.")
            name_col   = st.selectbox("Name column",   imp.columns.tolist())
            amount_col = st.selectbox("Amount column", imp.columns.tolist())
            if st.button("Import CSV"):
                for _, row in imp.iterrows():
                    st.session_state.transactions.append({
                        "name":   str(row[name_col]),
                        "amount": abs(float(row[amount_col])),
                        "type":   "expense",
                        "cat":    "Other",
                        "date":   datetime.today().strftime("%Y-%m-%d")
                    })
                save_data(st.session_state.transactions)
                st.success(f"Imported {len(imp)} transactions!")
                st.rerun()
        except Exception as e:
            st.error(f"Error reading CSV: {e}")

    st.divider()
    if st.button("🗑️ Clear All Data", use_container_width=True):
        st.session_state.transactions = []
        save_data([])
        st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ═════════════════════════════════════════════════════════════════════════════
st.markdown(f'<div class="logo" style="margin-bottom:8px">Fin<span>Sight</span> AI</div>', unsafe_allow_html=True)
st.caption(f"📅 {datetime.today().strftime('%B %Y')}  •  {len(txs)} transactions recorded")
st.divider()

# ── Stat cards ────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
cards = [
    (c1, "💰 Total Income",   fmt(income),  "#00e599", f"This month"),
    (c2, "💸 Total Spent",    fmt(spent),   "#ff6b9d", f"This month"),
    (c3, "🏦 Savings",        fmt(savings), "#ffd166", f"{rate}% of income"),
    (c4, "📊 Transactions",   len(txs),     "#4cc9f0", f"Recorded"),
]
for col, label, value, color, sub in cards:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{color}">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── Charts row ────────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Spending by Category")
    if not expenses_df.empty:
        cat_df = expenses_df.groupby("cat")["amount"].sum().reset_index().sort_values("amount", ascending=True)
        fig_bar = px.bar(
            cat_df, x="amount", y="cat", orientation="h",
            color="cat",
            color_discrete_map=CATEGORY_COLORS,
            labels={"amount": "Amount (Rs)", "cat": ""},
            template="plotly_dark"
        )
        fig_bar.update_layout(
            paper_bgcolor="#161616", plot_bgcolor="#161616",
            showlegend=False, margin=dict(l=0,r=0,t=0,b=0), height=280
        )
        fig_bar.update_traces(marker_line_width=0)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Add expenses to see breakdown")

with col_right:
    st.subheader("🍩 Budget Split")
    if not expenses_df.empty:
        cat_df2 = expenses_df.groupby("cat")["amount"].sum().reset_index()
        fig_pie = px.pie(
            cat_df2, values="amount", names="cat",
            color="cat", color_discrete_map=CATEGORY_COLORS,
            hole=0.55, template="plotly_dark"
        )
        fig_pie.update_layout(
            paper_bgcolor="#161616", plot_bgcolor="#161616",
            showlegend=True, margin=dict(l=0,r=0,t=0,b=0), height=280,
            legend=dict(font=dict(color="#888", size=11))
        )
        fig_pie.update_traces(textinfo="percent", textfont_color="white")
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Add expenses to see chart")

st.divider()

# ── Transactions table + Savings gauge ───────────────────────────────────────
col_tx, col_gauge = st.columns(2)

with col_tx:
    st.subheader("🧾 Recent Transactions")
    if not df.empty:
        display_df = df.head(10).copy()
        display_df["icon"]   = display_df["cat"].map(CATEGORY_ICONS)
        display_df["Amount"] = display_df.apply(
            lambda r: f"+{fmt(r['amount'])}" if r["type"]=="income" else f"-{fmt(r['amount'])}", axis=1
        )
        display_df["Name"] = display_df["icon"] + " " + display_df["name"]
        st.dataframe(
            display_df[["Name","cat","Amount","date"]].rename(columns={"cat":"Category","date":"Date"}),
            use_container_width=True, hide_index=True, height=300
        )
    else:
        st.info("No transactions yet")

with col_gauge:
    st.subheader("📈 Savings Health")
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=rate,
        number={"suffix": "%", "font": {"color": "#f0f0f0", "size": 40}},
        delta={"reference": 20, "suffix": "% vs target"},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#888", "tickfont": {"color":"#888"}},
            "bar":  {"color": "#00e599"},
            "bgcolor": "#161616",
            "steps": [
                {"range": [0,  20], "color": "#ff6b9d33"},
                {"range": [20, 50], "color": "#ffd16633"},
                {"range": [50,100], "color": "#00e59933"},
            ],
            "threshold": {"line":{"color":"#4cc9f0","width":3}, "thickness":0.75, "value":20}
        },
        title={"text": "Savings Rate", "font": {"color": "#888", "size": 14}}
    ))
    fig_gauge.update_layout(
        paper_bgcolor="#161616", font_color="#f0f0f0",
        margin=dict(l=20,r=20,t=40,b=20), height=300
    )
    st.plotly_chart(fig_gauge, use_container_width=True)
    if rate < 20:
        st.warning("💡 Aim to save at least 20% of your income")
    elif rate < 50:
        st.success("✅ Good savings rate! Try to push towards 50%")
    else:
        st.success("🌟 Excellent savings rate!")

st.divider()

# ── Spending over time ────────────────────────────────────────────────────────
if not expenses_df.empty and "date" in expenses_df.columns:
    st.subheader("📅 Spending Over Time")
    time_df = expenses_df.copy()
    time_df["date"] = pd.to_datetime(time_df["date"])
    time_df = time_df.groupby("date")["amount"].sum().reset_index()
    fig_line = px.area(
        time_df, x="date", y="amount",
        labels={"amount":"Amount (Rs)", "date":"Date"},
        template="plotly_dark", color_discrete_sequence=["#4cc9f0"]
    )
    fig_line.update_layout(
        paper_bgcolor="#161616", plot_bgcolor="#161616",
        margin=dict(l=0,r=0,t=0,b=0), height=200
    )
    fig_line.update_traces(fill="tozeroy", fillcolor="rgba(76,201,240,0.15)")
    st.plotly_chart(fig_line, use_container_width=True)
    st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# AI INSIGHTS
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="ai-box">', unsafe_allow_html=True)
st.markdown('<span class="ai-badge">✨ AI POWERED</span>', unsafe_allow_html=True)
st.subheader("Smart Financial Insights")

api_key = st.text_input(
    "Enter your Anthropic API Key (get free at console.anthropic.com)",
    type="password",
    placeholder="sk-ant-...",
    help="Your key is never stored. It's only used for this session."
)

if st.button("✨ Analyze My Finances with AI", use_container_width=True):
    if not api_key:
        st.warning("Please enter your Anthropic API key above to use AI insights.")
    elif income == 0 and spent == 0:
        st.warning("Add some transactions first!")
    else:
        cat_summary = ", ".join([f"{c}: Rs {v:,.0f}" for c,v in
            expenses_df.groupby("cat")["amount"].sum().items()]) if not expenses_df.empty else "No expenses"

        prompt = f"""You are a friendly personal finance advisor for a Pakistani student. Analyze:
- Income: Rs {income:,.0f}
- Spent: Rs {spent:,.0f}
- Savings: Rs {savings:,.0f} ({rate}% of income)
- Categories: {cat_summary}
- Transactions: {len(txs)}

Give a 2-sentence summary then exactly 3 specific actionable tips. Use Rs. Be encouraging.
Respond ONLY as JSON: {{"summary":"...","tips":["tip1","tip2","tip3"]}}"""

        with st.spinner("Claude AI is analyzing your spending..."):
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)
                message = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = json.loads(message.content[0].text.strip())
                st.session_state.ai_result = result
            except json.JSONDecodeError:
                st.error("AI returned unexpected format. Try again.")
            except Exception as e:
                st.error(f"Error: {e}")

if st.session_state.ai_result:
    r = st.session_state.ai_result
    st.info(r.get("summary",""))
    tips = r.get("tips", [])
    icons = ["💡", "🎯", "🚀"]
    for i, tip in enumerate(tips):
        st.markdown(f'<div class="tip-box">{icons[i]} {tip}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("Built by Ibrahim · FinSight AI · Powered by Python, Streamlit & Claude AI")
