import pandas as pd
import paho.mqtt.client as mqtt
import json
import time
import random
import joblib 
import numpy as np
from datetime import datetime
import blynklib

# --- BLYNK SETUP ---
BLYNK_AUTH = 'kN30TSZRvW1SgWnxnYKrKgZogR4-xPoD' 
blynk = blynklib.Blynk(BLYNK_AUTH, server="blr1.blynk.cloud") 
blynk.connect() 
print("📱 Blynk Mobile Link Established")

# --- LOAD ML MODEL ---
try:
    model = joblib.load('relay_model.pkl')
    print("🧠 ML Model Loaded Successfully")
except:
    print("⚠️ Run train_model.py first!")
    model = None

# --- CONFIGURATION ---
BROKER = "broker.emqx.io"
TOPIC = "luminous_ml/complete_telemetry" 

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, 1883, 60)
client.loop_start()

ticks = 0
switch_cycles = 0

print("🚀 Full-Stack Edge Brain Active: Mapping All 17 Registers...")

# THE FIX: Setup a timer variable before the loop
last_update_time = time.time()

while True:
    # 1. BLYNK HEARTBEAT (Runs continuously, never sleeps!)
    try:
        blynk.run()
    except:
        pass # Ignore minor connection hiccups

    # 2. THE 2-SECOND DATA CYCLE
    current_time = time.time()
    
    # Only generate data if 2 seconds have passed
    if current_time - last_update_time >= 2.0:
        
        # --- GENERATE FULL MODBUS REGISTER DATA ---
        temp = round(45.0 + (ticks * 0.1) + random.uniform(-2, 2), 2)  
        inv_current = round(random.uniform(5.0, 35.0), 2)              
        mains_voltage = int(random.normalvariate(230, 15))            
        grid_freq = round(random.normalvariate(50.0, 0.4), 2)         
        
        inv_voltage = 230 if random.random() > 0.05 else 0            
        grid_ct_current = round(inv_current * 0.9, 2)                 
        dis_current = inv_current if random.random() > 0.5 else 0.0   
        chg_current = 15.0 if dis_current == 0 else 0.0               

        mains_ok = 1 if (190 < mains_voltage < 260) else 0            
        high_chg_mode = 1 if chg_current > 10 else 0                  
        led_state = 1 if mains_ok else 2                              
        
        sys_state = 1 if mains_ok else 4                              
        inv_state = 1 if inv_voltage > 0 else 0                       
        chg_state = 1 if chg_current > 0 else 0                       
        
        overload = 1 if inv_current > 32.0 else 0                     
        trip_code = 1 if random.random() < 0.02 else 0                
        
        if not mains_ok or trip_code: switch_cycles += 1              

        # --- ML PREDICTION ---
        if model:
            features = pd.DataFrame(
                [[temp, inv_current, switch_cycles, mains_voltage]], 
                columns=['temp', 'current', 'cycles', 'mains_v']
            )
            ml_predicted_rul = model.predict(features)[0]
            ml_predicted_rul = max(0, round(ml_predicted_rul, 2))
        else:
            ml_predicted_rul = 99.0
            
        ttf_cycle = round(ml_predicted_rul * 100)
        
        # --- PREPARE FULL PAYLOAD ---
        payload = {
            "timestamp": datetime.now().strftime("%H:%M:%S"), 
            "rul": ml_predicted_rul,
            "ttf_cycles": ttf_cycle,
            "status": "CRITICAL" if ml_predicted_rul < 20 else "HEALTHY",
            "3002": dis_current,
            "3003": chg_current,
            "3004": mains_voltage,
            "3007": trip_code,
            "3011": switch_cycles,
            "3012": mains_ok,
            "3019_temp": temp, 
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
        
        # --- BLYNK MOBILE SYNC ---
        try:
            blynk.virtual_write(0, ml_predicted_rul)      
            blynk.virtual_write(1, ttf_cycle) 
            
            # Trigger Mobile Push Notification if Critical
            if ml_predicted_rul < 20:
                blynk.log_event("criticalalert", f"CRITICAL: Relay RUL at {ml_predicted_rul}%. Replace immediately.")
        except Exception as e:
            print(f"Blynk Sync Error: {e}")
            
        print(f"Full Telemetry Sent. RUL: {ml_predicted_rul}% | Mains: {mains_voltage}V | Switch: {switch_cycles}")
        
        # Reset the timer and increment ticks
        last_update_time = current_time
        ticks += 1