import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import os
# ------------------------
# CONFIG
# ------------------------
st.set_page_config(page_title="SOC IoT Monitor", layout="wide")
st_autorefresh(interval=3000, key="refresh")

# ------------------------
# CUSTOM CSS (SOC polish)
# ------------------------
st.markdown("""
<style>
    .stApp { background-color: #0b0f1a; color: white; }
    h1, h2, h3 { color: #58a6ff !important; }
    .stMetric {
        background-color: #111827;
        padding: 15px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🛡 SOC - IoT Security Monitoring Dashboard")

# ------------------------
# LOAD DATA
# ------------------------
try:
    df = pd.read_csv("traffic_log.csv", names=["Time","PacketRate","Status","IP"])
    latest_traffic = df.iloc[-1]
except:
    df = None

try:
    sensor_df = pd.read_csv("sensor_data.csv")
    sensor_df.columns = sensor_df.columns.str.strip().str.lower()
except:
    sensor_df = None

# ------------------------
# SAFE SENSOR VALUES (NO NaN)
# ------------------------
def get_latest_valid(col):
    try:
        return sensor_df[col].dropna().iloc[-1]
    except:
        return "N/A"

# ------------------------
# 1. SENSOR METRICS
# ------------------------
st.subheader("🌡 Environment Status")
m1, m2, m3 = st.columns(3)

if sensor_df is not None:
    temp = get_latest_valid("temperature")
    pressure = get_latest_valid("pressure")
    light = get_latest_valid("light")

    m1.metric("Temperature", f"{temp} °C")
    m2.metric("Pressure", f"{pressure} hPa")
    m3.metric("Light Status", str(light).upper())
else:
    st.warning("Waiting for sensor_data.csv...")

st.divider()

# ------------------------
# 2. NETWORK STATUS
# ------------------------
st.subheader("🌐 Network Security Status")
n1, n2, n3 = st.columns(3)

if df is not None:
    n1.metric("📡 Packet Rate", f"{round(latest_traffic['PacketRate'], 2)} pkts/s")
    n2.metric("📍 Source IP", latest_traffic["IP"])
    n3.metric("🚨 Status", latest_traffic["Status"])

    # 🔥 Improved alert banner
    if latest_traffic["Status"] == "ATTACK":
        st.markdown(
            f"""
            <div style='background-color:#3b0d0d;padding:15px;border-radius:10px'>
            🚨 <b>CRITICAL ALERT:</b> Intrusion detected from {latest_traffic["IP"]}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.success("✅ NETWORK TRAFFIC NORMAL")

st.divider()

# ------------------------
# 3. ANALYTICS
# ------------------------
st.subheader("📈 Real-time Analytics")
g1, g2, g3 = st.columns(3)

graph_style = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="white",
    height=300
)

with g1:
    if sensor_df is not None:

        temp_df = sensor_df.copy()
        temp_df["temperature"] = pd.to_numeric(temp_df["temperature"], errors="coerce")
        temp_df = temp_df.dropna(subset=["temperature"])

        if not temp_df.empty:

            fig_temp = px.line(
                temp_df,   # 🔴 FULL DATA (not tail)
                x="time",
                y="temperature",
                title="Temperature Trend",
                color_discrete_sequence=['#ff4b4b']
            )

            fig_temp.update_layout(
                **graph_style,
                xaxis=dict(rangeslider=dict(visible=True)),  # ✅ SCROLL BAR
                yaxis=dict(autorange=True)
            )

            st.plotly_chart(fig_temp, use_container_width=True)

with g2:
    if sensor_df is not None:

        pres_df = sensor_df.copy()
        pres_df["pressure"] = pd.to_numeric(pres_df["pressure"], errors="coerce")
        pres_df = pres_df.dropna(subset=["pressure"])

        if not pres_df.empty:

            fig_pres = px.line(
                pres_df,
                x="time",
                y="pressure",
                title="Pressure Trend",
                color_discrete_sequence=['#00d4ff']
            )

            fig_pres.update_layout(
                **graph_style,
                xaxis=dict(rangeslider=dict(visible=True)),  # ✅ SCROLL
                yaxis=dict(autorange=True)
            )

            st.plotly_chart(fig_pres, use_container_width=True)
with g3:
    if df is not None:
        fig_traffic = px.area(
            df.tail(50),
            x="Time",
            y="PacketRate",
            title="Traffic Load",
            color_discrete_sequence=['#79fe00']
        )
        fig_traffic.update_layout(**graph_style)
        st.plotly_chart(fig_traffic, use_container_width=True)

# ------------------------
# 4. ATTACK TABLE (ONLY ATTACKS)
# ------------------------
st.divider()
st.subheader("⚠️ Recent Attack Events")

if df is not None:
    attack_df = df[df["Status"] == "ATTACK"]
    st.dataframe(attack_df.tail(10), use_container_width=True)

# ------------------------
# 5. FIREWALL CONTROL
# ------------------------
st.divider()
st.subheader("🚫 Firewall Control Panel")

if df is not None:

    attack_ips = df[df["Status"] == "ATTACK"]["IP"].unique()

    if len(attack_ips) > 0:
        selected_ip = st.selectbox("Select IP to Unblock", attack_ips)

        if st.button("Unblock Selected IP"):

            os.system(f'netsh advfirewall firewall delete rule name="Block_IN_{selected_ip}"')
            os.system(f'netsh advfirewall firewall delete rule name="Block_OUT_{selected_ip}"')

            st.success(f"✅ {selected_ip} unblocked")
    else:
        st.info("No blocked IPs yet")