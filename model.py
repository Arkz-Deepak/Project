import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib

# 1. Generate Synthetic Training Data (Physics-based failure patterns)
data_size = 1000
temp = np.random.uniform(30, 110, data_size)
current = np.random.uniform(5, 40, data_size)
cycles = np.random.uniform(0, 10000, data_size)
mains_v = np.random.uniform(180, 260, data_size)

# The "Ground Truth" RUL formula the ML will try to learn
# Note: Arcing damage is modeled as Current * Cycles
target_rul = 100 - ( (temp * 0.3) + (current * 0.4) + (cycles * 0.005) + (abs(mains_v - 230) * 0.1) )
target_rul = np.clip(target_rul, 0, 100)

# 2. Create DataFrame
df = pd.DataFrame({
    'temp': temp,
    'current': current,
    'cycles': cycles,
    'mains_v': mains_v,
    'rul': target_rul
})

# 3. Train the Model
X = df[['temp', 'current', 'cycles', 'mains_v']]
y = df['rul']

model = RandomForestRegressor(n_estimators=100)
model.fit(X, y)

# 4. Save the "Brain"
joblib.dump(model, 'relay_model.pkl')
print("✅ ML Model Trained and Saved as 'relay_model.pkl'")