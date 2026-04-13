import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="PdM Command Center", layout="wide")
st.markdown("<h1 style='text-align: center;'>⚡ Luminous Predictive Maintenance Command Center</h1>", unsafe_allow_html=True)
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
            if len(data_store) > 100: 
                data_store.pop(0)
        except Exception as e:
            pass
    client.on_message = on_message
    client.connect("broker.emqx.io", 1883, 60)
    client.subscribe("luminous_ml/complete_telemetry")
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
                st.error(f"🚨 {latest['status']} - DISPATCH ENGINEER IMMEDIATELY")
            elif "WARNING" in latest['status']:
                st.warning(f"⚠️ {latest['status']} - Monitor closely.")
            else:
                st.success(f"✅ {latest['status']}")
                
            # --- 2. UNIFIED SYSTEM METRICS ---
            st.markdown("### 📊 AI-Driven System Health & Core Metrics")

            # Creating 4 columns for the most important data
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)

            # Column 1: The ML Prediction
            kpi1.metric("ML Predicted RUL", f"{latest['rul']}%")

            # Column 2: The Estimated Time to Failure (TTF)
            kpi2.metric("Est. Cycles Left", f"{latest['ttf_cycles']}")

            # Column 3: The Primary Stress Factor (Synced Key)
            kpi3.metric("Current Temp (3019)", f"{latest['3019_temp']} °C")

            # Column 4: The Mechanical Wear count (Synced Key)
            kpi4.metric("Switch Cycles (3011)", f"{latest['3011']}")

            st.divider()

            # --- 3. EARLY WARNING SYSTEM ---
            if latest['ttf_cycles'] < 500:
                st.warning(f"🚨 ML ALERT: Component failure predicted within {latest['ttf_cycles']} switching operations. Notify Service Engineer.")
            elif latest['rul'] < 20:
                st.error("🚨 CRITICAL: Remaining Useful Life below 20%. Immediate replacement advised.")
                
            # --- 4. TABBED DASHBOARD FOR DEEP DIVES ---
            tab1, tab2, tab3 = st.tabs(["📉 Degradation Trend", "⚡ Power Quality", "🔋 Load & Temp Dynamics"])
            
            with tab1:
                st.subheader("Remaining Useful Life (RUL) Trajectory")
                st.line_chart(df.set_index('timestamp')['rul'], color="#FF0000")
                
            with tab2:
                st.subheader("Grid Stability (Voltage & Frequency)")
                colA, colB = st.columns(2)
                with colA:
                    st.line_chart(df.set_index('timestamp')['3004'], color="#0000FF")
                with colB:
                    st.line_chart(df.set_index('timestamp')['3058_grid_hz'], color="#00FF00")
                    
            with tab3:
                st.subheader("Inverter Load vs. Operating Temperature")
                colC, colD = st.columns(2)
                with colC:
                    st.line_chart(df.set_index('timestamp')['3054_inv_cur'], color="#FFA500")
                with colD:
                    st.line_chart(df.set_index('timestamp')['3019_temp'], color="#FF4500")

            # --- 5. FAULT LOG ---
            if latest['3059'] == 1 or latest['3007'] == 1:
                st.toast("Fault Detected in Telemetry Stream!", icon="🔥")

            # --- 6. RAW MODBUS AUDIT LOG ---
            st.divider()
            with st.expander("🔍 Full Modbus Register Audit Log (All 17 Registers)"):
                st.dataframe(df.tail(10), use_container_width=True)

        else:
            st.info("📡 Connecting to Luminous Edge Device... Waiting for Modbus sync.")
            
    time.sleep(2)