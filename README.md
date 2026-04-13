# ⚡ Luminous Predictive Maintenance (PdM) Command Center
### **APOGEE Innovation Challenge | BITS Pilani**

## 📌 Project Overview
Relays and contactors in inverters do not have a fixed expiry date; their lifespan is dictated by switching cycles, electrical load, and thermal stress. This project delivers an **AI-driven, Physics-of-Failure based solution** to estimate the **Remaining Useful Life (RUL)** of these components.

By correlating power quality, thermal dynamics, and load currents, the system provides real-time predictive diagnostics and early warning alerts at both the **Edge** (Inverter level) and the **Cloud** (Command Center dashboard) to prevent unplanned inverter downtime.

## 👥 Developers
* **Deepak R** * **A. Thanigai Malai** 

## 🏗️ System Architecture
This solution is built as a real-time simulation model utilizing a dual-layer IoT architecture:

1. **Machine Learning Model (`model.py`):** A `RandomForestRegressor` trained on historical physics-of-failure patterns to correlate Temperature, Inverter Current, Mains Voltage, and Switching Cycles into a highly accurate RUL percentage and Time-to-Failure (TTF) cycle count.
2. **Edge Intelligence (`edge_system.py`):** Acts as the Inverter’s local processing unit. It simulates the full 17-register Luminous MODBUS map, runs the ML model locally for fast inference, and publishes the telemetry via **MQTT**.
3. **Cloud Command Center (`app.py`):** A **Streamlit** dashboard that acts as the cloud/server UI. It fetches MQTT data to visualize degradation trends, monitor power quality, and trigger critical UI alerts for Service Engineers.

## ✨ Key Features
* **Full Modbus Support:** Maps and transmits all 17 specified Luminous inverter registers.
* **Edge AI Inference:** Performs the heavy ML predictions locally to save cloud bandwidth.
* **Early Warning System:** Triggers predictive alerts (e.g., "Failure predicted within 500 cycles") before hardware breaks.
* **Dynamic Visualization:** Live tracking of Grid Stability (Voltage/Hz), Load vs. Temp dynamics, and RUL trajectories.

## 🛠️ Tech Stack
* **Language:** Python 3.x
* **Machine Learning:** Scikit-Learn (`RandomForestRegressor`), NumPy
* **IoT Protocol:** Paho-MQTT (MODBUS RTU mapped over MQTT)
* **Frontend:** Streamlit
* **Data Processing:** Pandas, JSON

## 🚀 Getting Started

### 1. Prerequisites
Ensure Python is installed, then install the required dependencies:
```bash
pip install paho-mqtt streamlit pandas scikit-learn numpy joblib
```
### 2. Execution
This project requires running the system in split terminal windows to simulate the Edge and the Cloud simultaneously:
#### Terminal 1 (Train the AI - Run Once):
```bash
python model.py
```
(This generates the relay_model.pkl file used by the Edge device).
### Terminal 2 (Start the Edge Brain):
```bash
python edge_system.py
```
### Terminal 3 (Launch the Cloud Dashboard):
```bash
streamlit run app.py
```
## 📋 Modbus Register Telemetry Map
This project successfully simulates and monitors the following data points:
| Register | Name | Impact Category |
| :--- | :--- | :--- |
| **3019** | TEMPERATURE | Thermal Degradation |
| **3011** | SWITCH | Mechanical Wear |
| **3054** | INVERTER CURRENT | Electrical Arcing Stress |
| **3004** | MAINS VOLTAGE | Power Quality / Grid Stress |
| **3058** | GRID FREQUENCY | Power Quality |
| **3059** | LINE CURRENT OVERLOAD | Acute System Shock |
| **3007** | TRIP CODE | Critical Failure Event |
| **3002/3003**| DISCHARGE/CHARGE CURRENT | Battery Load Dynamics |
| **3012** | MAINS OK FLAG | State Indicator |
| **3020/3045**| SYSTEM/INVERTER STATE | State Indicator |

Developed for APOGEE 26
