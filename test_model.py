import joblib

model = joblib.load("student_score_model.pkl")
print("Model Loaded Successfully")

scaler = joblib.load("scaler.pkl")
print("Scaler Loaded Successfully")