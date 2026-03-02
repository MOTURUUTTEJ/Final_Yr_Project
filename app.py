"""
Brain Stroke Risk Prediction Flask Application
Main application file with routes for authentication and prediction
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import pickle
import numpy as np
import os
from datetime import datetime
from functools import wraps

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stroke_prediction.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Load trained model and scaler
try:
    model = joblib.load('models/stroke_model.pkl')
    scaler = joblib.load('models/scaler.pkl')
    with open('models/feature_names.pkl', 'rb') as f:
        feature_names = pickle.load(f)
    print("✓ Model loaded successfully!")
except Exception as e:
    print(f"Warning: Could not load model - {e}")
    model = None
    scaler = None
    feature_names = None


# Database Model for Users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'


# Database Model for Predictions
class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    age = db.Column(db.Integer)
    avg_glucose_level = db.Column(db.Float)
    bmi = db.Column(db.Float)
    risk_score = db.Column(db.Float)
    prediction = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Prediction {self.id}>'


# Decorator to check if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Routes

@app.route('/')
def index():
    """Home page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not email or not password:
            return render_template('register.html', error='All fields are required!')
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match!')
        
        if len(password) < 6:
            return render_template('register.html', error='Password must be at least 6 characters!')
        
        # Check if user exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error='Username already exists!')
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return render_template('register.html', error='Email already registered!')
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login', success='Registration successful! Please log in.'))
        except Exception as e:
            db.session.rollback()
            return render_template('register.html', error=f'Error during registration: {str(e)}')
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    success = request.args.get('success')
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('login.html', error='Username and password are required!')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password!')
    
    return render_template('login.html', success=success)


@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    user_id = session.get('user_id')
    username = session.get('username')
    
    # Get user's predictions
    predictions = Prediction.query.filter_by(user_id=user_id).all()
    
    return render_template('dashboard.html', username=username, predictions=predictions)


@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    """Stroke risk prediction page"""
    user_id = session.get('user_id')
    username = session.get('username')
    prediction_result = None
    risk_level = None
    error = None
    
    if request.method == 'POST':
        try:
            # Get form data
            age = int(request.form.get('age', 0))
            gender = request.form.get('gender', 'Male')
            hypertension = int(request.form.get('hypertension', 0))
            heart_disease = int(request.form.get('heart_disease', 0))
            ever_married = request.form.get('ever_married', 'Yes')
            work_type = request.form.get('work_type', 'Private')
            residence_type = request.form.get('residence_type', 'Urban')
            avg_glucose_level = float(request.form.get('avg_glucose_level', 0))
            bmi = float(request.form.get('bmi', 0))
            smoking_status = request.form.get('smoking_status', 'never')
            
            # Validate input
            if age < 0 or age > 120:
                error = "Age must be between 0 and 120!"
                return render_template('predict.html', username=username, error=error)
            
            if avg_glucose_level < 0 or avg_glucose_level > 500:
                error = "Glucose level must be between 0 and 500!"
                return render_template('predict.html', username=username, error=error)
            
            if bmi < 0 or bmi > 100:
                error = "BMI must be between 0 and 100!"
                return render_template('predict.html', username=username, error=error)
            
            # Encode categorical variables
            gender_encoded = 1 if gender == 'Male' else 0
            ever_married_encoded = 1 if ever_married == 'Yes' else 0
            residence_encoded = 1 if residence_type == 'Urban' else 0
            
            # Map work_type
            work_type_map = {'Private': 0, 'Self-employed': 1, 'Govt_job': 2, 'Never_worked': 3}
            work_type_encoded = work_type_map.get(work_type, 0)
            
            # Map smoking_status (matches actual CSV values)
            smoking_map = {'never': 0, 'formerly': 1, 'smokes': 2, 'Unknown': 3}
            smoking_encoded = smoking_map.get(smoking_status, 3)
            
            # Feature engineering
            age_group = int(np.digitize(age, bins=[30, 50, 70]))  # 0=<30, 1=30-50, 2=50-70, 3=70+
            high_glucose = 1 if avg_glucose_level > 125 else 0
            high_bmi = 1 if bmi > 30 else 0
            health_risk = hypertension + heart_disease
            
            # Create feature vector in correct order
            input_data = np.array([[
                age, gender_encoded, hypertension, heart_disease, 
                ever_married_encoded, work_type_encoded, residence_encoded,
                avg_glucose_level, bmi, smoking_encoded,
                age_group, high_glucose, high_bmi, health_risk
            ]])
            
            # Scale input
            input_scaled = scaler.transform(input_data)
            
            # Make prediction
            risk_score = model.predict_proba(input_scaled)[0][1]
            prediction = model.predict(input_scaled)[0]
            
            # Determine risk level
            # Thresholds are calibrated to the model's actual output range:
            # stroke prevalence ~5%, so 40%+ = ~8x elevated risk = High Risk
            if risk_score < 0.15:
                risk_level = "Low Risk"
                risk_color = "success"
            elif risk_score < 0.40:
                risk_level = "Medium Risk"
                risk_color = "warning"
            else:
                risk_level = "High Risk"
                risk_color = "danger"
            
            prediction_result = {
                'risk_score': round(risk_score * 100, 2),
                'risk_level': risk_level,
                'risk_color': risk_color,
                'prediction': int(prediction)
            }
            
            # Save prediction to database
            new_prediction = Prediction(
                user_id=user_id,
                age=age,
                avg_glucose_level=avg_glucose_level,
                bmi=bmi,
                risk_score=risk_score,
                prediction=int(prediction)
            )
            db.session.add(new_prediction)
            db.session.commit()
            
        except Exception as e:
            error = f"Prediction error: {str(e)}"
    
    return render_template('predict.html', username=username, 
                         prediction=prediction_result, error=error)


@app.route('/history')
@login_required
def history():
    """View prediction history"""
    user_id = session.get('user_id')
    username = session.get('username')
    
    # Get user's predictions
    predictions = Prediction.query.filter_by(user_id=user_id).order_by(Prediction.created_at.desc()).all()
    
    return render_template('history.html', username=username, predictions=predictions)


@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    user_id = session.get('user_id')
    username = session.get('username')
    
    user = User.query.get(user_id)
    prediction_count = Prediction.query.filter_by(user_id=user_id).count()
    
    return render_template('profile.html', username=username, user=user, 
                         prediction_count=prediction_count)


@app.route('/api/user-stats')
@login_required
def user_stats():
    """API endpoint for user statistics"""
    user_id = session.get('user_id')
    
    predictions = Prediction.query.filter_by(user_id=user_id).all()
    
    if not predictions:
        return jsonify({
            'total_predictions': 0,
            'high_risk_count': 0,
            'avg_risk_score': 0
        })
    
    total = len(predictions)
    high_risk = sum(1 for p in predictions if p.risk_score > 0.40)
    avg_risk = sum(p.risk_score for p in predictions) / total
    
    return jsonify({
        'total_predictions': total,
        'high_risk_count': high_risk,
        'avg_risk_score': round(avg_risk * 100, 2)
    })


@app.errorhandler(404)
def page_not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('500.html'), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
