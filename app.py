"""
Elite Personal Finance Chatbot - Colorful Trendy UI

Run:
1. pip install streamlit pandas numpy plotly python-dateutil
2. streamlit run app_trendy_full.py
"""

import os, time
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil import parser
import plotly.express as px
import textwrap

# -----------------------
# Helper Functions
# -----------------------
def load_sample_transactions():
    data = [
        {"date": "2025-08-01", "category": "Food", "amount": 250, "description": "Lunch"},
        {"date": "2025-08-02", "category": "Transport", "amount": 120, "description": "Metro"},
        {"date": "2025-08-03", "category": "Groceries", "amount": 1500, "description": "Weekly groceries"},
        {"date": "2025-08-05", "category": "Entertainment", "amount": 600, "description": "Movie + snacks"},
        {"date": "2025-08-07", "category": "Subscriptions", "amount": 299, "description": "Music"},
        {"date": "2025-08-10", "category": "Bills", "amount": 2200, "description": "Electricity"},
        {"date": "2025-08-15", "category": "Savings", "amount": -5000, "description": "Monthly saving transfer"},
        {"date": "2025-08-20", "category": "Investment", "amount": -2000, "description": "SIP"},
    ]
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    return df

def parse_transactions(uploaded_file):
    df = pd.read_csv(uploaded_file)
    required = {'date','category','amount'}
    if not required.issubset(df.columns):
        raise ValueError(f"CSV must contain at least columns: {required}")
    df['date'] = pd.to_datetime(df['date'])
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    return df.dropna(subset=['amount','date'])

def summarize_budget(transactions):
    if transactions.empty: return "No transactions to summarize."
    tx = transactions.copy()
    recent = tx[tx['date']>= tx['date'].max() - pd.Timedelta(days=30)]
    if recent.empty: recent = tx
    total_spent = recent[recent['amount']>0]['amount'].sum()
    total_saved = -recent[recent['amount']<0]['amount'].sum()
    by_cat = recent.groupby('category')['amount'].sum().sort_values(ascending=False)
    lines = [
        f"**Period:** {recent['date'].min().date()} → {recent['date'].max().date()}",
        f"**Total Spending:** ₹{total_spent:,.2f}",
        f"**Total Savings/Investments:** ₹{total_saved:,.2f}",
        "**Top Expense Categories:**"
    ]
    for cat, amt in by_cat[by_cat>0].head(5).items():
        lines.append(f"- {cat}: ₹{amt:,.2f}")
    avg_daily = total_spent / max(1,(recent['date'].max()-recent['date'].min()).days)
    lines.append(f"**Avg Daily Spend:** ₹{avg_daily:,.2f}")
    suggested_monthly = total_spent * 30 / max(1,(recent['date'].max()-recent['date'].min()).days) * 0.9
    lines.append(f"**Suggested Monthly Budget:** ₹{suggested_monthly:,.0f} (~10% reduction)")
    return "\n".join(lines)

def generate_spending_insights(transactions, profile):
    if transactions.empty: return "No transactions to analyze."
    by_cat = transactions.groupby('category')['amount'].sum().abs().sort_values(ascending=False)
    top = by_cat.head(3)
    total = transactions['amount'].abs().sum()
    top_pct = (top/total*100).round(1)
    suggestions = ["**Top Spending Categories:**"]
    for i,(cat,amt) in enumerate(top.items(),1):
        suggestions.append(f"{i}. {cat} — ₹{amt:,.0f} (~{top_pct.iloc[i-1]}%)")
    if 'Subscriptions' in by_cat.index and by_cat['Subscriptions']>500:
        suggestions.append("- Consider reviewing unused subscriptions.")
    if 'Food' in by_cat.index and by_cat['Food']>2000:
        suggestions.append("- Set weekly limits for dining out.")
    if 'Transport' in by_cat.index and by_cat['Transport']>1000:
        suggestions.append("- Explore travel cards or carpooling.")
    if profile.get('user_type')=='Student':
        suggestions.append("- Build emergency buffer (₹2k–₹10k).")
    else:
        suggestions.append("- Automate savings and tax-saving investments.")
    return "\n".join(suggestions)

def generate_tax_guidance(profile):
    base = ["**Tax Guidance (general educational):**"]
    if profile.get('user_type')=='Student':
        base += ["- Check filing threshold for part-time income.","- Keep educational expense receipts."]
    else:
        base += ["- Track salary components & use standard deductions.",
                 "- Save proofs for investments (PPF, ELSS, insurance)."]
    base.append("- Consult a tax professional for accuracy.")
    return "\n".join(base)

def format_response_for_tone(text, profile, complexity="Auto"):
    user_type = profile.get('user_type','Student')
    if complexity=="Auto": complexity = "Simple" if user_type=="Student" else "Detailed"
    prefix = "Hey! Here's a simple version:\n\n" if complexity=="Simple" else "Hello — advisory:\n\n"
    return prefix + textwrap.fill(text, width=80)

def local_ai_response(msg, profile, transactions, complexity):
    m = msg.lower()
    if "budget" in m: return summarize_budget(transactions)
    if any(k in m for k in ["spend","insights","save"]): return generate_spending_insights(transactions, profile)
    if "tax" in m: return generate_tax_guidance(profile)
    if any(k in m for k in ["invest","sip"]): return ("General investment advice:\n- Emergency fund\n- Diversified equity/index funds\n- Short-term: liquid funds or FDs")
    return "I can assist with budget, spending insights, tax basics, or investment tips."

# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="💬 Personal Finance Chatbot", layout="wide")

# Gradient & button styling
st.markdown("""
<style>
body {background: linear-gradient(to right,#f8f8f8,#fff);}
div[data-testid="stSidebar"] {background: linear-gradient(to bottom,#6a1b9a,#8e24aa); color:white;}
h1,h2,h3 {color:#4a148c;}
.stButton>button {background: linear-gradient(to right,#6a1b9a,#ab47bc); color:white; border-radius:12px; height:3em; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

st.title("💬 Personal Finance Chatbot (Trendy UI)")

# Sidebar Profile
with st.sidebar:
    st.header("👤 Profile")
    name = st.text_input("Name", value="Alex")
    user_type = st.selectbox("User type", ['Student','Professional'])
    age = st.number_input("Age", 15,80, value=23 if user_type=="Student" else 30)
    monthly_income = st.number_input("Monthly income (₹)", 0,1000000, value=30000)
    complexity = st.selectbox("Response complexity", ["Auto","Simple","Detailed"])
    st.markdown("---")
    uploaded = st.file_uploader("Upload transactions CSV", type=['csv'])
    use_sample = st.checkbox("Use sample transactions", True)

# Transactions
if 'transactions' not in st.session_state:
    if uploaded:
        try: st.session_state['transactions']=parse_transactions(uploaded)
        except: st.session_state['transactions']=load_sample_transactions()
    else:
        st.session_state['transactions']=load_sample_transactions() if use_sample else pd.DataFrame(columns=['date','category','amount','description'])
transactions = st.session_state['transactions']

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["💰 Budget","📊 Insights","🧾 Tax","➕ Add Tx"])

# -----------------------
# Budget Tab
# -----------------------
with tab1:
    st.subheader("📋 Budget Summary")
    summary = summarize_budget(transactions)
    st.markdown(summary)

# -----------------------
# Insights Tab
# -----------------------
with tab2:
    st.subheader("📊 Spending Insights")
    profile = {"name": name, "user_type": user_type, "age": age, "monthly_income": monthly_income}
    insights = generate_spending_insights(transactions, profile)
    st.markdown(insights)
    
    # Plotly bar chart for categories
    if not transactions.empty:
        agg = transactions.groupby('category')['amount'].sum().abs().sort_values(ascending=False)
        fig = px.bar(agg.head(8), x=agg.head(8).index, y=agg.head(8).values, labels={'x':'Category','y':'Amount (₹)'},
                     title="Top Expense Categories", color=agg.head(8).values, color_continuous_scale='Agsunset')
        st.plotly_chart(fig, use_container_width=True)

# -----------------------
# Tax Tab
# -----------------------
with tab3:
    st.subheader("🧾 Tax Guidance")
    guidance = generate_tax_guidance(profile)
    st.markdown(guidance)

# -----------------------
# Add Transaction Tab
# -----------------------
with tab4:
    st.subheader("➕ Add Transaction")
    with st.form("add_tx"):
        d = st.date_input("Date", value=datetime.today())
        cat = st.text_input("Category", value="Misc")
        amt = st.number_input("Amount (+expense, -saving)", value=0)
        desc = st.text_input("Description", value="")
        add_sub = st.form_submit_button("Add Transaction")
        if add_sub:
            new = {"date": pd.to_datetime(d), "category": cat, "amount": float(amt), "description": desc}
            st.session_state['transactions'] = pd.concat([st.session_state['transactions'], pd.DataFrame([new])], ignore_index=True)
            st.success("Transaction added.")
            st.experimental_rerun()

# -----------------------
# Chat Interface
# -----------------------
st.markdown("---")
st.subheader("💬 Chat with your Finance Assistant")
if 'messages' not in st.session_state:
    st.session_state['messages'] = [{"role":"assistant","text":"Hi! I'm your Personal Finance Assistant. Ask me about budget, spending, tax, or investment tips."}]

# Display chat
for msg in st.session_state['messages']:
    if msg['role']=="assistant": st.markdown(f"<div style='background:linear-gradient(90deg,#ab47bc,#6a1b9a);padding:10px;border-radius:12px;margin:5px;color:white;'>{msg['text']}</div>", unsafe_allow_html=True)
    else: st.markdown(f"<div style='background:#f1f0f0;padding:10px;border-radius:12px;margin:5px;color:black;'>You: {msg['text']}</div>", unsafe_allow_html=True)

# Chat input
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Type your message here...")
    submitted = st.form_submit_button("Send")
    if submitted and user_input:
        st.session_state['messages'].append({"role":"user","text":user_input})
        resp_text = local_ai_response(user_input, profile, transactions, complexity)
        resp_text = format_response_for_tone(resp_text, profile, complexity)
        st.session_state['messages'].append({"role":"assistant","text":resp_text})
        st.experimental_rerun()
# End of app.py