import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model.pkl')
SCALER_PATH = os.path.join(BASE_DIR, 'scaler.pkl')

def generate_synthetic_data(n=5000):
    np.random.seed(42)
    area = np.random.uniform(50, 5000, n)
    population = np.random.randint(100, 10_000_000, n)
    forest_pct = np.random.uniform(5, 80, n)
    wetland_pct = np.random.uniform(0, 30, n)
    agri_pct = np.random.uniform(5, 70, n)

    epv = (0.05 * area + 0.2 * population / 1e6 + 0.3 * agri_pct) * 1e6 + np.random.normal(0, 5e6, n)
    erv = (0.08 * area + 0.15 * forest_pct + 0.25 * wetland_pct) * 1e6 + np.random.normal(0, 8e6, n)
    ecv = (0.02 * area + 0.1 * population / 1e6 + 0.2 * forest_pct) * 1e6 + np.random.normal(0, 3e6, n)

    epv = np.maximum(epv, 0)
    erv = np.maximum(erv, 0)
    ecv = np.maximum(ecv, 0)

    df = pd.DataFrame({
        'area_km2': area,
        'population': population,
        'forest_pct': forest_pct,
        'wetland_pct': wetland_pct,
        'agri_pct': agri_pct,
        'epv': epv,
        'erv': erv,
        'ecv': ecv
    })
    return df

def train_and_save_model():
    df = generate_synthetic_data()
    X = df[['area_km2', 'population', 'forest_pct', 'wetland_pct', 'agri_pct']]
    y = df[['epv', 'erv', 'ecv']]

    X_np = X.values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_np)

    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_scaled, y.values)

    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"✅ Model trained and saved to {MODEL_PATH}")

def load_model():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        train_and_save_model()
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    return model, scaler

def predict_gep(area_km2, population, forest_pct, wetland_pct, agri_pct):
    try:
        model, scaler = load_model()
        features = np.array([[area_km2, population, forest_pct, wetland_pct, agri_pct]])
        features_scaled = scaler.transform(features)
        pred = model.predict(features_scaled)[0]
        return {
            'epv': float(max(pred[0], 0)),
            'erv': float(max(pred[1], 0)),
            'ecv': float(max(pred[2], 0))
        }
    except Exception as e:
        print(f"Prediction error: {e}")
        raise