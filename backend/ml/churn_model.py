import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

ML_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(ML_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

def train_churn_model():
    print("Training Churn Risk Model...")
    np.random.seed(42)
    n_samples = 1000

    # Features:
    # negative_tickets: 0 to 5
    # escalations: 0 to 3
    # days_since_last: 0 to 60
    # clv: 0 to 2000
    # health_score: 0 to 100
    negative_tickets = np.random.randint(0, 6, size=n_samples)
    escalations = np.random.randint(0, 4, size=n_samples)
    days_since_last = np.random.randint(0, 61, size=n_samples)
    clv = np.random.uniform(0.0, 2000.0, size=n_samples)
    health_score = np.random.randint(0, 101, size=n_samples)

    # Risk formula to generate labels
    # High health score -> low risk
    # High negative tickets or escalations -> high risk
    # High days since last interaction -> high risk
    risk_score = (
        negative_tickets * 15 +
        escalations * 20 +
        days_since_last * 0.5 +
        (100 - health_score) * 0.5 -
        (clv / 200.0)
    )

    # Normalize to 0-100
    min_r, max_r = risk_score.min(), risk_score.max()
    norm_risk = ((risk_score - min_r) / (max_r - min_r)) * 100

    labels = []
    for r in norm_risk:
        if r >= 65:
            labels.append("High")
        elif r >= 35:
            labels.append("Medium")
        else:
            labels.append("Low")

    df = pd.DataFrame({
        "negative_tickets": negative_tickets,
        "escalations": escalations,
        "days_since_last": days_since_last,
        "clv": clv,
        "health_score": health_score,
        "label": labels
    })

    X = df[["negative_tickets", "escalations", "days_since_last", "clv", "health_score"]]
    y = df["label"]

    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', RandomForestClassifier(n_estimators=50, max_depth=6, random_state=42))
    ])

    pipeline.fit(X, y)
    joblib.dump(pipeline, os.path.join(MODELS_DIR, "churn_model.joblib"))
    print("Churn risk model saved.")

if __name__ == "__main__":
    train_churn_model()
