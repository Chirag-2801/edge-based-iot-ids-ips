import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

def train_model():

    df = pd.read_csv("normal_traffic.csv")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df)

    model = IsolationForest(
        contamination=0.02,
        random_state=42
    )

    model.fit(X_scaled)

    joblib.dump(model,"model.pkl")
    joblib.dump(scaler,"scaler.pkl")

    print("Model trained successfully")


def predict(features):

    model = joblib.load("model.pkl")
    scaler = joblib.load("scaler.pkl")

    X = scaler.transform([features])

    result = model.predict(X)

    if result[0] == -1:
        return "ATTACK"
    else:
        return "NORMAL"