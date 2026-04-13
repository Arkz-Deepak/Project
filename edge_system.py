import paho.mqtt.client as mqtt
import json
import time
import random
import joblib 
import numpy as np
from datetime import datetime

# --- LOAD ML MODEL ---
try:
    model = joblib.load('relay_model.pkl')
    print("🧠 ML Model Loaded Successfully")
except:
    print("⚠️ Run train_model.py first!")
    model = None

# --- CONFIGURATION ---
BROKER = "broker.emqx.io"
TOPIC = "luminous_ml/complete_telemetry" # Unique topic for full map

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, 1883, 60)

ticks = 0
switch_cycles = 0

print("🚀 Full-Stack Edge Brain Active: Mapping All 17 Registers...")

while True:
    # 1. GENERATE FULL MODBUS REGISTER DATA 
    # Primary Metrics
    temp = round(45.0 + (ticks * 0.1) + random.uniform(-2, 2), 2)  # 3019
    inv_current = round(random.uniform(5.0, 35.0), 2)              # 3054
    mains_voltage = int(random.normalvariate(230, 15))            # 3004
    grid_freq = round(random.normalvariate(50.0, 0.4), 2)         # 3058
    
    # Current & Voltage Variations [cite: 35, 40]
    inv_voltage = 230 if random.random() > 0.05 else 0            # 3053
    grid_ct_current = round(inv_current * 0.9, 2)                 # 3052
    dis_current = inv_current if random.random() > 0.5 else 0.0   # 3002
    chg_current = 15.0 if dis_current == 0 else 0.0               # 3003

    # State Flags & Indicators 
    mains_ok = 1 if (190 < mains_voltage < 260) else 0            # 3012
    high_chg_mode = 1 if chg_current > 10 else 0                  # 3023
    led_state = 1 if mains_ok else 2                              # 3050 (1=Green, 2=Blinking)
    
    # System States (Simulating internal logic codes) 
    sys_state = 1 if mains_ok else 4                              # 3020
    inv_state = 1 if inv_voltage > 0 else 0                       # 3045
    chg_state = 1 if chg_current > 0 else 0                       # 3046
    
    # Critical Events
    overload = 1 if inv_current > 32.0 else 0                     # 3059
    trip_code = 1 if random.random() < 0.02 else 0                # 3007
    
    # Relay Tracking
    if not mains_ok or trip_code: switch_cycles += 1              # 3011 (Switch event)

    # 2. ML PREDICTION
    if model:
        features = np.array([[temp, inv_current, switch_cycles, mains_voltage]])
        ml_predicted_rul = model.predict(features)[0]
        ml_predicted_rul = max(0, round(ml_predicted_rul, 2))
    else:
        ml_predicted_rul = 99.0

    # 3. PREPARE FULL PAYLOAD [cite: 27, 40]
    payload = {
        "timestamp": datetime.now().strftime("%H:%M:%S"), 
        "rul": ml_predicted_rul,
        "ttf_cycles": round(ml_predicted_rul * 100),
        "status": "CRITICAL" if ml_predicted_rul < 20 else "HEALTHY",
        
        # Mapping exactly to the Luminous Modbus Table 
        "3002": dis_current,
        "3003": chg_current,
        "3004": mains_voltage,
        "3007": trip_code,
        "3011": switch_cycles,
        "3012": mains_ok,
        "3019_temp": temp, # kept label for dashboard consistency
        "3020": sys_state,
        "3023": high_chg_mode,
        "3045": inv_state,
        "3046": chg_state,
        "3050": led_state,
        "3052": grid_ct_current,
        "3053": inv_voltage,
        "3054_inv_cur": inv_current, 
        "3058_grid_hz": grid_freq,
        "3059": overload
    }
    
    client.publish(TOPIC, json.dumps(payload))
    print(f"Full Telemetry Sent. RUL: {ml_predicted_rul}% | Mains: {mains_voltage}V | Switch: {switch_cycles}")
    
    ticks += 1
    time.sleep(2)