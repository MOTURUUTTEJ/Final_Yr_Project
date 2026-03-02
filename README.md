# Brain Stroke Risk Prediction using Machine Learning

A comprehensive web application that predicts stroke risk using machine learning models trained on medical demographic data. The application includes user authentication, prediction history tracking, and a beautiful, responsive UI.

## 📋 Features

### Machine Learning
- **Multiple Models**: Logistic Regression, Random Forest, Gradient Boosting, SVM
- **Data Preprocessing**: Handling missing values, encoding categorical variables, feature scaling
- **Feature Engineering**: Age groups, glucose levels, BMI categories, health risk scores
- **Hyperparameter Tuning**: GridSearchCV optimization for best model selection
- **Comprehensive Evaluation**: Accuracy, Precision, Recall, F1-score, ROC-AUC metrics

### Web Application
- **User Authentication**: Secure registration and login with password hashing
- **User Dashboard**: Overview of predictions and health statistics
- **Risk Prediction**: Interactive form for stroke risk assessment
- **Prediction History**: Track all previous predictions with detailed metrics
- **User Profile**: View account information and statistics
- **Beautiful UI**: Bootstrap 5 responsive design with modern styling
- **Database**: SQLite for user and prediction data persistence

## 🛠️ Tech Stack

### Backend
- Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- scikit-learn 1.3.2
- joblib 1.3.2
- Werkzeug (password hashing)

### Frontend
- Bootstrap 4.5.2
- Font Awesome Icons
- jQuery

### Machine Learning
- pandas 2.0.3
- numpy 1.24.3
- scikit-learn 1.3.2
- matplotlib & seaborn (visualization)

### Database
- SQLite 3

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd "Brain Stroke risk Prediction using ML on"
```

### Step 2: Create a Virtual Environment
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Jupyter Notebook (Optional)
The `Stroke_Risk_Prediction.ipynb` notebook contains the complete ML pipeline:

```bash
# Install Jupyter
pip install jupyter notebook

# Start Jupyter
jupyter notebook

# Open and run Stroke_Risk_Prediction.ipynb
```

This will:
- Create sample medical demographic data
- Preprocess and engineer features
- Train multiple ML models
- Evaluate model performance
- Save the trained model and scaler to `models/` directory

### Step 5: Run the Flask Application
```bash
python app.py
```

The application will be available at: `http://localhost:5000`

## 🚀 Getting Started

### Access the Application

1. **Open your browser** and navigate to: `http://localhost:5000`
2. **Register** a new account with:
   - Username
   - Email
   - Password (minimum 6 characters)
3. **Login** with your credentials
4. **Make a Prediction**:
   - Fill in your medical and demographic information
   - Click "Calculate Risk"
   - View your stroke risk assessment with recommendations

### Database Initialization

The SQLite database (`stroke_prediction.db`) is automatically created on first run with the following tables:

**Users Table**
```
id (Integer, Primary Key)
username (String, Unique)
email (String, Unique)
password (String, hashed)
created_at (DateTime)
```

**Predictions Table**
```
id (Integer, Primary Key)
user_id (Integer, Foreign Key)
age (Integer)
avg_glucose_level (Float)
bmi (Float)
risk_score (Float)
prediction (Integer)
created_at (DateTime)
```

## 📊 Models & Performance

### Model Comparison
The notebook trains and compares:
1. **Logistic Regression** - Interpretable, fast
2. **Random Forest** - Ensemble, high accuracy (typically best)
3. **Gradient Boosting** - Powerful, complex
4. **Support Vector Machine** - Nonlinear separation

### Performance Metrics
- **Accuracy**: Overall correctness of predictions
- **Precision**: False positive rate control
- **Recall**: True positive rate (sensitivity)
- **F1-Score**: Balanced metric
- **ROC-AUC**: Model discrimination ability

### Default Model
The application uses the **tuned Random Forest** model which typically achieves:
- Accuracy: ~85-90%
- ROC-AUC: ~0.88-0.92

## 🔐 Security Features

- **Password Hashing**: Uses Werkzeug's `generate_password_hash()` and `check_password_hash()`
- **Session Management**: Secure session cookies with user authentication
- **CSRF Protection**: Built-in Flask security
- **Input Validation**: Form validation and range checks
- **SQL Injection Prevention**: SQLAlchemy ORM usage

## 📝 API Endpoints

### Authentication Routes
- `GET/POST /register` - User registration
- `GET/POST /login` - User login
- `GET /logout` - User logout

### Application Routes
- `GET /` - Home (redirects to login/dashboard)
- `GET /dashboard` - User dashboard
- `GET/POST /predict` - Stroke risk prediction
- `GET /history` - Prediction history
- `GET /profile` - User profile
- `GET /api/user-stats` - User statistics (JSON)

## 📄 File Structure

```
Brain Stroke risk Prediction using ML on/
│
├── Stroke_Risk_Prediction.ipynb      # ML model training notebook
├── app.py                             # Flask application
├── requirements.txt                   # Python dependencies
│
├── models/                            # Trained ML models
│   ├── stroke_model.pkl              # Trained Random Forest model
│   ├── scaler.pkl                    # Feature scaler
│   └── feature_names.pkl             # Feature names list
│
├── templates/                         # HTML templates
│   ├── login.html                    # Login page
│   ├── register.html                 # Registration page
│   ├── dashboard.html                # User dashboard
│   ├── predict.html                  # Prediction form
│   ├── history.html                  # Prediction history
│   ├── profile.html                  # User profile
│   ├── 404.html                      # 404 error page
│   └── 500.html                      # 500 error page
│
├── stroke_prediction.db              # SQLite database (auto-created)
└── README.md                         # This file
```

## 🔍 Prediction Features

The application collects the following medical and demographic information:

### Demographic Information
- **Age**: 0-120 years
- **Gender**: Male/Female
- **Marital Status**: Ever Married (Yes/No)
- **Work Type**: Private, Self-employed, Government Job, Never Worked
- **Residence**: Urban/Rural

### Health Metrics
- **Average Glucose Level**: 0-500 mg/dL
- **BMI**: 0-100
- **Hypertension**: Yes/No
- **Heart Disease**: Yes/No

### Lifestyle
- **Smoking Status**: Never, Formerly, Smokes, Unknown

## 📈 Risk Assessment

The model returns a risk score (0-100%) categorized as:

- **Low Risk** (0-30%): Continue healthy lifestyle habits
- **Medium Risk** (30-70%): Monitor health metrics, consult healthcare provider
- **High Risk** (70-100%): Consult healthcare provider immediately, take preventive measures

## ⚙️ Configuration

### Change Secret Key (Production)
In `app.py`, update the secret key:
```python
app.config['SECRET_KEY'] = 'your-production-secret-key'
```

### Change Database Location
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////path/to/database.db'
```

### Change Server Port
In the last line of `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8000)  # Change port here
```

## 🐛 Troubleshooting

### Model Files Not Found
**Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'models/stroke_model.pkl'`

**Solution**: Run the Jupyter notebook first to generate model files:
```bash
jupyter notebook Stroke_Risk_Prediction.ipynb
# Run all cells
```

### Database Locked
**Error**: `database is locked`

**Solution**: Delete `stroke_prediction.db` and restart the app to recreate it.

### Port Already in Use
**Error**: `Address already in use`

**Solution**: Change the port in `app.py`:
```python
app.run(debug=True, port=5001)  # Use different port
```

## 📚 Usage Examples

### Example 1: Low Risk Individual
```
Age: 30
Gender: Female
Hypertension: No
Heart Disease: No
Glucose Level: 95
BMI: 22
Smoking: Never

Result: Low Risk (15%)
```

### Example 2: High Risk Individual
```
Age: 75
Gender: Male
Hypertension: Yes
Heart Disease: Yes
Glucose Level: 180
BMI: 32
Smoking: Smokes

Result: High Risk (82%)
```

## 📞 Support & Contribution

### Reporting Issues
If you encounter any issues, please provide:
1. Error message
2. Steps to reproduce
3. Your environment (OS, Python version)

### Contributing
Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🎓 References

### Medical Background
- Stroke Risk Factors: https://www.stroke.org/
- Medical Data Analysis: American Heart Association guidelines

### ML Libraries
- scikit-learn: https://scikit-learn.org/
- pandas: https://pandas.pydata.org/
- Flask: https://flask.palletsprojects.com/

## 👨‍💻 Author

Created for educational and healthcare informatics purposes.

---

**Disclaimer**: This application is for educational purposes and should not be used as a substitute for professional medical advice. Always consult with a healthcare provider for medical diagnosis and treatment.

**Last Updated**: February 2026
**Version**: 1.0.0
