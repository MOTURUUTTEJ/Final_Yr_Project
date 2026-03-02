"""
Retrain Brain Stroke Risk Prediction Model
Fixes class imbalance using SMOTE to enable High Risk predictions
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import joblib
import pickle
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("  Brain Stroke Risk Model - Retraining with SMOTE Fix")
print("=" * 60)

# ── 1. Load Data ──────────────────────────────────────────────
print("\n[1/6] Loading dataset...")
df = pd.read_csv('data/stroke_data.csv')

# Drop 'id' column if present
if 'id' in df.columns:
    df = df.drop('id', axis=1)

print(f"    Dataset shape: {df.shape}")
print(f"    Stroke cases (1): {df['stroke'].sum()} ({df['stroke'].mean()*100:.1f}%)")
print(f"    Non-stroke (0): {(df['stroke']==0).sum()} ({(df['stroke']==0).mean()*100:.1f}%)")

# ── 2. Preprocessing ──────────────────────────────────────────
print("\n[2/6] Preprocessing data...")

# Handle missing BMI values
df['bmi'] = pd.to_numeric(df['bmi'], errors='coerce')
df['bmi'].fillna(df['bmi'].median(), inplace=True)

# Drop unknown gender rows
df = df[df['gender'] != 'Other']

# Encode categorical variables
df['gender_encoded'] = (df['gender'] == 'Male').astype(int)
df['ever_married_encoded'] = (df['ever_married'] == 'Yes').astype(int)
df['residence_encoded'] = (df['Residence_type'] == 'Urban').astype(int) if 'Residence_type' in df.columns else (df['residence_type'] == 'Urban').astype(int)

work_type_map = {'Private': 0, 'Self-employed': 1, 'Govt_job': 2, 'Never_worked': 3, 'children': 4}
df['work_type_encoded'] = df['work_type'].map(work_type_map).fillna(0).astype(int)

smoking_map = {'never': 0, 'formerly': 1, 'smokes': 2, 'Unknown': 3}
df['smoking_encoded'] = df['smoking_status'].map(smoking_map).fillna(3).astype(int)

# Feature engineering
df['age'] = pd.to_numeric(df['age'], errors='coerce').fillna(0)
df['age_group'] = np.digitize(df['age'], bins=[30, 50, 70]).astype(int)  # 0=<30, 1=30-50, 2=50-70, 3=70+
df['high_glucose'] = (df['avg_glucose_level'] > 125).astype(int)
df['high_bmi'] = (df['bmi'] > 30).astype(int)
df['health_risk'] = df['hypertension'] + df['heart_disease']

features = [
    'age', 'gender_encoded', 'hypertension', 'heart_disease',
    'ever_married_encoded', 'work_type_encoded', 'residence_encoded',
    'avg_glucose_level', 'bmi', 'smoking_encoded',
    'age_group', 'high_glucose', 'high_bmi', 'health_risk'
]

X = df[features]
y = df['stroke']

print(f"    Features: {features}")
print(f"    Class distribution: {dict(y.value_counts())}")

# ── 3. Apply SMOTE to fix class imbalance ─────────────────────
print("\n[3/6] Applying SMOTE to balance classes...")
try:
    from imblearn.over_sampling import SMOTE
    smote = SMOTE(random_state=42, k_neighbors=5)
    X_resampled, y_resampled = smote.fit_resample(X, y)
    print(f"    Before SMOTE - Class 0: {(y==0).sum()}, Class 1: {(y==1).sum()}")
    print(f"    After  SMOTE - Class 0: {(y_resampled==0).sum()}, Class 1: {(y_resampled==1).sum()}")
except Exception as e:
    print(f"    SMOTE unavailable ({type(e).__name__}), using manual oversampling...")
    # Manually oversample the minority (stroke) class 15x
    stroke_X = X[y == 1]
    stroke_y = y[y == 1]
    no_stroke_X = X[y == 0]
    no_stroke_y = y[y == 0]
    oversampled_X = pd.concat([stroke_X] * 15, ignore_index=True)
    oversampled_y = pd.concat([stroke_y] * 15, ignore_index=True)
    X_resampled = pd.concat([no_stroke_X, oversampled_X], ignore_index=True)
    y_resampled = pd.concat([no_stroke_y, oversampled_y], ignore_index=True)
    print(f"    After oversampling - Class 0: {(y_resampled==0).sum()}, Class 1: {(y_resampled==1).sum()}")

# ── 4. Train/Test Split & Scale ───────────────────────────────
print("\n[4/6] Splitting and scaling data...")
X_train, X_test, y_train, y_test = train_test_split(
    X_resampled, y_resampled, test_size=0.2, random_state=42, stratify=y_resampled
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
print(f"    Train: {X_train_scaled.shape}, Test: {X_test_scaled.shape}")

# ── 5. Train Model ────────────────────────────────────────────
print("\n[5/6] Training Gradient Boosting model...")
model = GradientBoostingClassifier(
    n_estimators=200,
    learning_rate=0.1,
    max_depth=5,
    min_samples_split=10,
    random_state=42
)
model.fit(X_train_scaled, y_train)

y_pred = model.predict(X_test_scaled)
y_proba = model.predict_proba(X_test_scaled)[:, 1]
roc = roc_auc_score(y_test, y_proba)

print(f"\n    ✅ Model Metrics:")
print(f"    ROC-AUC Score: {roc:.4f}")
print(f"\n    Classification Report:")
print(classification_report(y_test, y_pred, target_names=['No Stroke', 'Stroke']))

# Test with High Risk Sample
print("\n    Testing High Risk Sample:")
test_high = np.array([[78, 1, 1, 1, 1, 0, 1, 228.69, 36.6, 1, 3, 1, 1, 2]])
test_scaled = scaler.transform(test_high)
high_risk_score = model.predict_proba(test_scaled)[0][1]
print(f"    High Risk Patient Score: {high_risk_score*100:.1f}%")
if high_risk_score >= 0.6:
    print("    ✅ HIGH RISK correctly identified!")
else:
    print(f"    Score: {high_risk_score*100:.1f}% (Medium/Low)")

# ── 6. Save Model ─────────────────────────────────────────────
print("\n[6/6] Saving model files...")
joblib.dump(model, 'models/stroke_model.pkl')
joblib.dump(scaler, 'models/scaler.pkl')
with open('models/feature_names.pkl', 'wb') as f:
    pickle.dump(features, f)

print("    ✅ models/stroke_model.pkl saved")
print("    ✅ models/scaler.pkl saved")
print("    ✅ models/feature_names.pkl saved")

print("\n" + "=" * 60)
print("  ✅ Retraining Complete! Restart app.py to apply changes.")
print("=" * 60)
