from sklearn.ensemble import IsolationForest
import pandas as pd

def detect_anomalies(df):
    model = IsolationForest(contamination=0.05)
    df['anomaly'] = model.fit_predict(df[['lat', 'lon', 'altitude', 'speed']])
    return df