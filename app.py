from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import pickle
import numpy as np
import pandas as pd
import os
import csv
from io import StringIO
from datetime import datetime
from functools import wraps

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stroke_prediction.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Dataset path
DATASET_PATH = os.path.join(os.path.dirname(__file__), 'data', 'stroke_data.csv')

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


# ─────────────────────────── MODELS ────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'


class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    hypertension = db.Column(db.Integer)
    heart_disease = db.Column(db.Integer)
    ever_married = db.Column(db.String(5))
    work_type = db.Column(db.String(50))
    residence_type = db.Column(db.String(10))
    avg_glucose_level = db.Column(db.Float)
    bmi = db.Column(db.Float)
    smoking_status = db.Column(db.String(20))
    risk_score = db.Column(db.Float)
    prediction = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Prediction {self.id}>'


# ─────────────────────────── HELPERS ───────────────────────────

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def append_to_dataset(row_data: dict):
    """Append a new prediction row to the CSV dataset so it grows over time."""
    try:
        df = pd.read_csv(DATASET_PATH)
        new_id = int(df['id'].max()) + 1 if not df.empty else 1

        new_row = {
            'id': new_id,
            'age': row_data['age'],
            'gender': row_data['gender'],
            'hypertension': row_data['hypertension'],
            'heart_disease': row_data['heart_disease'],
            'ever_married': row_data['ever_married'],
            'work_type': row_data['work_type'],
            'residence_type': row_data['residence_type'],
            'avg_glucose_level': row_data['avg_glucose_level'],
            'bmi': row_data['bmi'],
            'smoking_status': row_data['smoking_status'],
            'stroke': row_data['prediction'],  # model's predicted stroke label
        }

        new_df = pd.DataFrame([new_row])
        new_df.to_csv(DATASET_PATH, mode='a', header=False, index=False)
        return True, new_id
    except Exception as e:
        print(f"[Dataset] Failed to append row: {e}")
        return False, None


def get_risk_level(score):
    if score < 0.15:
        return "Low Risk", "success"
    elif score < 0.40:
        return "Medium Risk", "warning"
    return "High Risk", "danger"


# ─────────────────────────── ROUTES ────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


# ── Auth ──

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not email or not password:
            return render_template('register.html', error='All fields are required!')
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match!')
        if len(password) < 6:
            return render_template('register.html', error='Password must be at least 6 characters!')
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists!')
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Email already registered!')

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            return render_template('register.html', error=f'Error during registration: {str(e)}')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    success = request.args.get('success')

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            return render_template('login.html', error='Username and password are required!')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome back, {user.username}! 👋', 'success')
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password!')

    return render_template('login.html', success=success)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


# ── Dashboard ──

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session.get('user_id')
    username = session.get('username')
    predictions = Prediction.query.filter_by(user_id=user_id)\
        .order_by(Prediction.created_at.desc()).all()
    flash_msgs = session.pop('_flashes', [])
    return render_template('dashboard.html', username=username, predictions=predictions)


# ── Predict ──

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    user_id = session.get('user_id')
    username = session.get('username')
    prediction_result = None
    error = None

    if request.method == 'POST':
        try:
            # Collect form data
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

            # Validate
            if not (0 < age <= 120):
                error = "Age must be between 1 and 120!"
                return render_template('predict.html', username=username, error=error)
            if not (0 < avg_glucose_level <= 500):
                error = "Glucose level must be between 1 and 500!"
                return render_template('predict.html', username=username, error=error)
            if not (0 < bmi <= 100):
                error = "BMI must be between 1 and 100!"
                return render_template('predict.html', username=username, error=error)

            # Encode categoricals
            gender_encoded = 1 if gender == 'Male' else 0
            ever_married_encoded = 1 if ever_married == 'Yes' else 0
            residence_encoded = 1 if residence_type == 'Urban' else 0
            work_type_map = {'Private': 0, 'Self-employed': 1, 'Govt_job': 2, 'Never_worked': 3}
            work_type_encoded = work_type_map.get(work_type, 0)
            smoking_map = {'never': 0, 'formerly': 1, 'smokes': 2, 'Unknown': 3}
            smoking_encoded = smoking_map.get(smoking_status, 3)

            # Feature engineering
            age_group = int(np.digitize(age, bins=[30, 50, 70]))
            high_glucose = 1 if avg_glucose_level > 125 else 0
            high_bmi = 1 if bmi > 30 else 0
            health_risk = hypertension + heart_disease

            input_data = np.array([[
                age, gender_encoded, hypertension, heart_disease,
                ever_married_encoded, work_type_encoded, residence_encoded,
                avg_glucose_level, bmi, smoking_encoded,
                age_group, high_glucose, high_bmi, health_risk
            ]])

            input_scaled = scaler.transform(input_data)
            risk_score = model.predict_proba(input_scaled)[0][1]
            prediction = model.predict(input_scaled)[0]

            risk_level, risk_color = get_risk_level(risk_score)

            # ── Compare with population average by age group ──
            if age < 30:
                pop_avg = 2.1; age_label = "Under 30"
            elif age < 50:
                pop_avg = 5.8; age_label = "30–50"
            elif age < 65:
                pop_avg = 12.4; age_label = "50–65"
            else:
                pop_avg = 24.7; age_label = "65+"

            your_score_pct = round(risk_score * 100, 2)
            diff = round(your_score_pct - pop_avg, 1)
            compare = {
                'your_score': your_score_pct,
                'pop_avg': pop_avg,
                'age_label': age_label,
                'diff': diff,
                'higher': diff > 0,
            }

            prediction_result = {
                'risk_score': your_score_pct,
                'risk_level': risk_level,
                'risk_color': risk_color,
                'prediction': int(prediction),
                'compare': compare,
            }

            # ── Save to database ──
            new_prediction = Prediction(
                user_id=user_id,
                age=age,
                gender=gender,
                hypertension=hypertension,
                heart_disease=heart_disease,
                ever_married=ever_married,
                work_type=work_type,
                residence_type=residence_type,
                avg_glucose_level=avg_glucose_level,
                bmi=bmi,
                smoking_status=smoking_status,
                risk_score=risk_score,
                prediction=int(prediction),
            )
            db.session.add(new_prediction)
            db.session.commit()

            # ── Append to dataset CSV ──
            saved_ok, new_id = append_to_dataset({
                'age': age, 'gender': gender,
                'hypertension': hypertension, 'heart_disease': heart_disease,
                'ever_married': ever_married, 'work_type': work_type,
                'residence_type': residence_type,
                'avg_glucose_level': avg_glucose_level,
                'bmi': bmi, 'smoking_status': smoking_status,
                'prediction': int(prediction),
            })

            if saved_ok:
                flash(f'✅ Prediction saved! Your data was also added to the training dataset (Row #{new_id}).', 'success')
            else:
                flash('✅ Prediction saved!', 'success')

        except Exception as e:
            error = f"Prediction error: {str(e)}"

    return render_template('predict.html', username=username,
                           prediction=prediction_result, error=error)


# ── History ──

@app.route('/history')
@login_required
def history():
    user_id = session.get('user_id')
    username = session.get('username')
    predictions = Prediction.query.filter_by(user_id=user_id)\
        .order_by(Prediction.created_at.desc()).all()
    return render_template('history.html', username=username, predictions=predictions)


# ── Profile + Change Password ──

@app.route('/profile')
@login_required
def profile():
    user_id = session.get('user_id')
    username = session.get('username')
    user = db.session.get(User, user_id)
    prediction_count = Prediction.query.filter_by(user_id=user_id).count()
    return render_template('profile.html', username=username, user=user,
                           prediction_count=prediction_count)


@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    user_id = session.get('user_id')
    user = db.session.get(User, user_id)

    old_pw = request.form.get('old_password', '')
    new_pw = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_new_password', '')

    if not check_password_hash(user.password, old_pw):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('profile'))
    if len(new_pw) < 6:
        flash('New password must be at least 6 characters.', 'error')
        return redirect(url_for('profile'))
    if new_pw != confirm_pw:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('profile'))

    user.password = generate_password_hash(new_pw)
    db.session.commit()
    flash('🔒 Password changed successfully!', 'success')
    return redirect(url_for('profile'))


# ── Analytics ──

@app.route('/analytics')
@login_required
def analytics():
    user_id = session.get('user_id')
    username = session.get('username')
    predictions = Prediction.query.filter_by(user_id=user_id)\
        .order_by(Prediction.created_at.asc()).all()
    return render_template('analytics.html', username=username, predictions=predictions)


# ── CSV Export ──

@app.route('/export/csv')
@login_required
def export_csv():
    user_id = session.get('user_id')
    predictions = Prediction.query.filter_by(user_id=user_id)\
        .order_by(Prediction.created_at.desc()).all()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['#', 'Date', 'Age', 'Gender', 'Glucose (mg/dL)', 'BMI',
                     'Hypertension', 'Heart Disease', 'Smoking', 'Risk Score (%)', 'Risk Level'])

    for i, p in enumerate(predictions, 1):
        level = 'Low' if p.risk_score < 0.15 else ('Medium' if p.risk_score < 0.40 else 'High')
        writer.writerow([
            i,
            p.created_at.strftime('%Y-%m-%d %H:%M'),
            p.age,
            getattr(p, 'gender', 'N/A'),
            p.avg_glucose_level,
            p.bmi,
            'Yes' if p.hypertension else 'No',
            'Yes' if p.heart_disease else 'No',
            getattr(p, 'smoking_status', 'N/A'),
            f'{round(p.risk_score * 100, 2)}',
            level,
        ])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=neuroguard_stroke_history.csv"
    output.headers["Content-type"] = "text/csv"
    return output


# ── API Endpoints ──

@app.route('/api/user-stats')
@login_required
def user_stats():
    user_id = session.get('user_id')
    predictions = Prediction.query.filter_by(user_id=user_id).all()

    if not predictions:
        return jsonify({'total_predictions': 0, 'high_risk_count': 0, 'avg_risk_score': 0})

    total = len(predictions)
    high_risk = sum(1 for p in predictions if p.risk_score > 0.40)
    avg_risk = sum(p.risk_score for p in predictions) / total

    return jsonify({
        'total_predictions': total,
        'high_risk_count': high_risk,
        'avg_risk_score': round(avg_risk * 100, 2),
    })


@app.route('/api/risk-trend')
@login_required
def risk_trend():
    """Returns time-series risk data for the trend chart."""
    user_id = session.get('user_id')
    predictions = Prediction.query.filter_by(user_id=user_id)\
        .order_by(Prediction.created_at.asc()).limit(30).all()

    return jsonify({
        'labels': [p.created_at.strftime('%b %d, %Y') for p in predictions],
        'scores': [round(p.risk_score * 100, 1) for p in predictions],
        'levels': [
            'low' if p.risk_score < 0.15 else ('medium' if p.risk_score < 0.40 else 'high')
            for p in predictions
        ],
    })


@app.route('/api/analytics-data')
@login_required
def analytics_data():
    """Returns full analytics data for the analytics page charts."""
    user_id = session.get('user_id')
    predictions = Prediction.query.filter_by(user_id=user_id).all()

    if not predictions:
        return jsonify({'empty': True})

    low = sum(1 for p in predictions if p.risk_score < 0.15)
    medium = sum(1 for p in predictions if 0.15 <= p.risk_score < 0.40)
    high = sum(1 for p in predictions if p.risk_score >= 0.40)

    sorted_preds = sorted(predictions, key=lambda p: p.created_at)

    return jsonify({
        'empty': False,
        'pie': {'low': low, 'medium': medium, 'high': high},
        'trend': {
            'labels': [p.created_at.strftime('%b %d') for p in sorted_preds],
            'scores': [round(p.risk_score * 100, 1) for p in sorted_preds],
        },
        'metrics': {
            'labels': [p.created_at.strftime('%b %d') for p in sorted_preds],
            'bmi': [round(p.bmi, 1) for p in sorted_preds],
            'glucose': [round(p.avg_glucose_level, 1) for p in sorted_preds],
        },
        'summary': {
            'total': len(predictions),
            'best': round(min(p.risk_score for p in predictions) * 100, 1),
            'worst': round(max(p.risk_score for p in predictions) * 100, 1),
            'avg': round(sum(p.risk_score for p in predictions) / len(predictions) * 100, 1),
            'dataset_rows': _get_dataset_size(),
        },
    })


def _get_dataset_size():
    """Return current number of rows in the CSV dataset."""
    try:
        df = pd.read_csv(DATASET_PATH)
        return len(df)
    except Exception:
        return 0


@app.route('/api/dataset-info')
@login_required
def dataset_info():
    """Returns current dataset size."""
    try:
        df = pd.read_csv(DATASET_PATH)
        return jsonify({'rows': len(df), 'cols': len(df.columns)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Error Handlers ──

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
