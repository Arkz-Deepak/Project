import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Luminous PdM Command Center", layout="wide")
st.title("⚡ Luminous Predictive Maintenance Command Center")
st.markdown("Monitoring Power Quality, Thermal Dynamics, and Component Degradation.")

# --- MEMORY SETUP ---
@st.cache_resource
def get_data_store():
    return []

data_store = get_data_store()

# --- MQTT SETUP ---
@st.cache_resource
def init_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    def on_message(client, userdata, message):
        try:
            data = json.loads(message.payload.decode())
            data_store.append(data)
            if len(data_store) > 100: # Keep 100 points for smooth charts
                data_store.pop(0)
        except Exception as e:
            pass
    client.on_message = on_message
    client.connect("broker.emqx.io", 1883, 60)
    client.subscribe("hackathon/luminous_final_v1/health")
    client.loop_start()
    return client

client = init_mqtt()

# --- UI RENDERING ---
placeholder = st.empty()

while True:
    with placeholder.container():
        if len(data_store) > 0:
            df = pd.DataFrame(list(data_store))
            latest = df.iloc[-1]
            
            # 1. DYNAMIC ALERT BANNER
            if "CRITICAL" in latest['status'] or "ERROR" in latest['status']:
                st.error(f"🚨 {latest['status']} - DisPATCH ENGINEER IMMEDIATELY")
            elif "WARNING" in latest['status']:
                st.warning(f"⚠️ {latest['status']} - Monitor closely.")
            else:
                st.success(f"✅ {latest['status']}")

            # 2. KEY PERFORMANCE INDICATORS (KPIs)
            st.markdown("### 📊 System Health & Core Metrics")
            kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
            kpi1.metric("Remaining Life (RUL)", f"{latest['rul']}%")
            kpi2.metric("Inverter Temp", f"{latest['3019_temp']} °C")
            kpi3.metric("Mains Voltage", f"{latest['3004_mains_v']} V")
            kpi4.metric("Grid Freq", f"{latest['3058_grid_hz']} Hz")
            kpi5.metric("Switch Cycles", f"{latest['3011_cycles']}")

            st.divider()

            # 3. TABBED DASHBOARD FOR DEEP DIVES
            tab1, tab2, tab3 = st.tabs(["📉 Degradation Trend", "⚡ Power Quality", "🔋 Load & Temp Dynamics"])
            
            with tab1:
                st.subheader("Remaining Useful Life (RUL) Trajectory")
                st.line_chart(df.set_index('timestamp')['rul'], color="#FF0000")
                
            with tab2:
                st.subheader("Grid Stability (Voltage & Frequency)")
                colA, colB = st.columns(2)
                with colA:
                    st.line_chart(df.set_index('timestamp')['3004_mains_v'], color="#0000FF")
                with colB:
                    st.line_chart(df.set_index('timestamp')['3058_grid_hz'], color="#00FF00")
                    
            with tab3:
                st.subheader("Inverter Load vs. Operating Temperature")
                colC, colD = st.columns(2)
                with colC:
                    st.line_chart(df.set_index('timestamp')['3054_inv_cur'], color="#FFA500")
                with colD:
                    st.line_chart(df.set_index('timestamp')['3019_temp'], color="#FF4500")

            # 4. FAULT LOG
            if latest['3059_overload'] == 1 or latest['3007_trip'] == 1:
                st.toast("Fault Detected in Telemetry Stream!", icon="🔥")

        else:
            st.info("📡 Connecting to Luminous Edge Device... Waiting for Modbus sync.")
            
    time.sleep(2)