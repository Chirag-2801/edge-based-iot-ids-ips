import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

print("📊 Loading dataset...")

# Load data
df = pd.read_csv("normal_traffic.csv")

# Features
X = df[["temperature", "pressure"]]

print("Scaling data...")

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print("Training model...")

model = IsolationForest(
    contamination=0.02,   # small anomalies
    random_state=42
)

model.fit(X_scaled)

# Save model
joblib.dump(model, "model.pkl")
joblib.dump(scaler, "scaler.pkl")

print("✅ Model trained and saved!")