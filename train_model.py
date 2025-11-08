
import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

BASE = os.path.dirname(__file__)

data_path = os.path.join(BASE, "data", "toy_symptom_dataset.csv")
feature_order_path = os.path.join(BASE, "data", "feature_order.json")
model_path = os.path.join(BASE, "model.joblib")
report_path = os.path.join(BASE, "training_report.txt")

df = pd.read_csv(data_path)
with open(feature_order_path) as f:
    features = json.load(f)

X = df[features].values
y = df["label"].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Simple multinomial logistic regression
pipe = Pipeline([
    ("scaler", StandardScaler(with_mean=False)),
    ("clf", LogisticRegression(max_iter=1000, multi_class="auto"))
])
pipe.fit(X_train, y_train)

y_pred = pipe.predict(X_test)
acc = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred)

joblib.dump({"model": pipe, "features": features, "labels": sorted(df["label"].unique().tolist())}, model_path)

with open(report_path, "w") as f:
    f.write(f"Accuracy: {acc:.3f}\n\n")
    f.write(report)

print(f"Saved model to {model_path}")
print(f"Accuracy: {acc:.3f}")
print(report)
