# Quick Start Guide - Brain Stroke Risk Prediction

## 🚀 Get Running in 5 Minutes

### Step 1: Install Python Dependencies (1 min)
```bash
pip install -r requirements.txt
```

### Step 2: Generate ML Models (2 min)
Run the Jupyter notebook to train and save the models:
```bash
jupyter notebook Stroke_Risk_Prediction.ipynb
```
- Open the notebook
- Click "Cell" → "Run All"
- Wait for all cells to complete
- Models will be saved in `models/` folder

### Step 3: Run Flask App (1 min)
```bash
python app.py
```

### Step 4: Open in Browser (1 min)
Navigate to: `http://localhost:5000`

---

## 📝 First Time User Guide

### Create Your Account
1. Click "Register here" on the login page
2. Enter:
   - **Username**: Your desired username
   - **Email**: Your email address
   - **Password**: At least 6 characters
3. Click "Create Account"

### Make Your First Prediction
1. Login with your credentials
2. Click "Make Prediction"
3. Fill in your medical information:
   - Age, Gender, Marital Status, Work Type, Residence
   - Glucose Level, BMI, Hypertension, Heart Disease, Smoking
4. Click "Calculate Risk"
5. View your stroke risk assessment and recommendations

### View Your History
- Click "History" to see all your previous predictions
- Click "Dashboard" for statistics overview
- Click "Profile" to view your account details

---

## 📊 Understanding Your Results

### Risk Levels
- **Green (0-30%)**: Low Risk - Maintain healthy habits
- **Yellow (30-70%)**: Medium Risk - Monitor and consult doctor
- **Red (70-100%)**: High Risk - Consult healthcare provider immediately

### Key Factors
The model considers:
- Your age (older = higher risk)
- Blood pressure control (hypertension)
- Heart health (heart disease history)
- Glucose levels (diabetes risk)
- Weight management (BMI)
- Smoking status

---

## 🔧 Troubleshooting

### Problem: "Models not found" error
**Solution**: Run the Jupyter notebook to generate models first
```bash
jupyter notebook Stroke_Risk_Prediction.ipynb
# Run all cells
```

### Problem: Port 5000 already in use
**Solution**: Change port in `app.py`
```python
app.run(debug=True, port=5001)  # Use 5001 instead
```

### Problem: Database locked
**Solution**: Delete `stroke_prediction.db` and restart

### Problem: Can't install packages
**Solution**: Create virtual environment first
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# or
source venv/bin/activate  # On Mac/Linux
pip install -r requirements.txt
```

---

## 💡 Tips

1. **Accurate Predictions**: Provide accurate medical data for better risk assessment
2. **Regular Check-ups**: Track your risk scores over time
3. **Medical Advice**: Always consult healthcare providers for medical decisions
4. **Data Privacy**: Your data is stored securely in the local SQLite database

---

## 📚 Need Help?

1. Check the README.md for detailed documentation
2. Review the Jupyter notebook for ML implementation details
3. Check app.py comments for code explanation
4. Visit the UI tooltips and info sections

---

## 🎓 Educational Purpose

This application is designed for educational purposes. It demonstrates:
- Machine Learning model development
- Flask web application development
- User authentication and database management
- Data visualization and prediction

**Not a medical device** - Always consult with healthcare professionals for actual medical decisions.

---

**Happy predicting!** 💙
