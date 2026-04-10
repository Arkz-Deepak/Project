import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

BROKER = "broker.emqx.io"
TOPIC = "hackathon/luminous_final_v1/health"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, 1883, 60)

print("🚀 Ultimate Edge Brain Active: Processing Full Modbus Map...")

# --- System State Variables ---
ticks = 0
switch_cycles = 0
accumulated_damage = 0.0

while True:
    # 1. SIMULATE FULL MODBUS TELEMETRY
    # Thermal & Load
    temp = round(45.0 + (ticks * 0.15) + random.uniform(-1, 1), 2)
    inv_current = round(random.uniform(5.0, 35.0), 2)
    discharge_current = inv_current if random.random() > 0.5 else 0.0
    charge_current = 15.0 if discharge_current == 0 else 0.0
    
    # Power Quality (Voltage & Frequency)
    mains_voltage = int(random.normalvariate(230, 10)) # Usually around 230V
    grid_frequency = round(random.normalvariate(50.0, 0.5), 2) # Usually around 50Hz
    
    # Events & Anomalies
    overload_flag = 1 if inv_current > 32.0 else 0
    trip_code = 1 if random.random() < 0.01 else 0 # 1% chance of a trip event
    
    # Switching Logic
    switch_event = 0
    if mains_voltage < 180 or mains_voltage > 260 or trip_code == 1:
        switch_event = 1
        switch_cycles += 1

    # 2. COMPREHENSIVE RUL ALGORITHM
    # Calculate fractional damage for this cycle based on stress vectors
    
    # A. Thermal Stress (Exponential damage above 50C)
    dmg_thermal = ((temp - 50) ** 1.2) * 0.005 if temp > 50 else 0
    
    # B. Power Quality Stress (Grid fluctuations strain the filters/relays)
    dmg_pq = 0
    if abs(mains_voltage - 230) > 20: dmg_pq += 0.05
    if abs(grid_frequency - 50.0) > 2.0: dmg_pq += 0.05
        
    # C. Mechanical & Arcing Stress (Switching under high load is devastating)
    dmg_arcing = 0
    if switch_event == 1:
        dmg_arcing = 0.2 + (inv_current * 0.02) # Base wear + arcing wear
        
    # D. Battery Load Stress
    dmg_load = (discharge_current * 0.001) + (charge_current * 0.001)
    
    # E. Critical Faults
    dmg_critical = (overload_flag * 1.5) + (trip_code * 3.0)

    # 3. UPDATE HEALTH METRICS
    total_tick_damage = dmg_thermal + dmg_pq + dmg_arcing + dmg_load + dmg_critical
    accumulated_damage += total_tick_damage
    rul = max(0.0, round(100.0 - accumulated_damage, 2))
    
    # Determine Status
    if rul < 20: status = "CRITICAL: END OF LIFE"
    elif trip_code == 1: status = "ERROR: SYSTEM TRIP"
    elif overload_flag == 1: status = "WARNING: OVERLOAD"
    elif dmg_pq > 0: status = "WARNING: POOR POWER QUALITY"
    else: status = "OK: HEALTHY"

    # 4. PREPARE & SEND CLOUD PAYLOAD
    payload = {
        "timestamp": datetime.now().strftime("%H:%M:%S"), 
        "status": status,
        "rul": rul, 
        "3019_temp": temp, 
        "3054_inv_cur": inv_current,
        "3002_dis_cur": discharge_current,
        "3003_chg_cur": charge_current,
        "3004_mains_v": mains_voltage,
        "3058_grid_hz": grid_frequency,
        "3011_cycles": switch_cycles,
        "3059_overload": overload_flag,
        "3007_trip": trip_code
    }
    
    client.publish(TOPIC, json.dumps(payload))
    print(f"RUL: {rul}% | Status: {status} | V: {mains_voltage} | Hz: {grid_frequency} | Cur: {inv_current}")
    
    ticks += 1
    time.sleep(2)