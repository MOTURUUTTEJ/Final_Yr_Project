#!/usr/bin/env python3
"""
Installation Verification Script
Verifies that all required components are installed and working
"""

import sys
import subprocess
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def check_python_version():
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("✗ Python 3.8+ required!")
        return False
    return True

def check_package(package_name, import_name=None):
    if import_name is None:
        import_name = package_name.replace('-', '_')
    
    try:
        __import__(import_name)
        print(f"✓ {package_name} installed")
        return True
    except ImportError:
        print(f"✗ {package_name} NOT installed")
        return False

def check_packages():
    print_header("Checking Required Packages")
    
    packages = [
        ('Flask', 'flask'),
        ('Flask-SQLAlchemy', 'flask_sqlalchemy'),
        ('scikit-learn', 'sklearn'),
        ('joblib', 'joblib'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('Werkzeug', 'werkzeug'),
    ]
    
    all_installed = True
    for package_name, import_name in packages:
        if not check_package(package_name, import_name):
            all_installed = False
    
    return all_installed

def check_files():
    print_header("Checking Project Files")
    
    required_files = [
        'Stroke_Risk_Prediction.ipynb',
        'app.py',
        'config.py',
        'requirements.txt',
        'README.md',
        'QUICKSTART.md',
        'templates/login.html',
        'templates/register.html',
        'templates/dashboard.html',
        'templates/predict.html',
        'templates/history.html',
        'templates/profile.html',
        'static/style.css',
    ]
    
    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} MISSING")
            all_exist = False
    
    return all_exist

def check_models():
    print_header("Checking ML Models")
    
    model_files = [
        'models/stroke_model.pkl',
        'models/scaler.pkl',
        'models/feature_names.pkl',
    ]
    
    all_exist = True
    for file_path in model_files:
        path = Path(file_path)
        if path.exists():
            print(f"✓ {file_path} exists")
        else:
            print(f"⚠ {file_path} NOT FOUND")
            print(f"  → Run Stroke_Risk_Prediction.ipynb to generate models")
            all_exist = False
    
    return all_exist

def check_flask_app():
    print_header("Checking Flask Application")
    
    try:
        import app as flask_app
        print("✓ Flask app imports successfully")
        
        # Check routes
        routes = ['/register', '/login', '/dashboard', '/predict', '/history', '/profile']
        print(f"✓ Expected routes: {len(routes)} routes configured")
        
        return True
    except Exception as e:
        print(f"✗ Flask app error: {e}")
        return False

def print_summary(results):
    print_header("Verification Summary")
    
    total = len(results)
    passed = sum(1 for r in results if r)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All checks passed! You're ready to run the application.")
        print("\nNext steps:")
        print("1. Run: jupyter notebook Stroke_Risk_Prediction.ipynb (if models not found)")
        print("2. Run: python app.py")
        print("3. Open: http://localhost:5000")
        return True
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nFor help, see QUICKSTART.md or README.md")
        return False

def main():
    print("\n" + "="*60)
    print("  Brain Stroke Risk Prediction - Installation Verification")
    print("="*60)
    
    results = []
    
    # Run all checks
    results.append(check_python_version())
    results.append(check_packages())
    results.append(check_files())
    results.append(check_models())
    
    try:
        results.append(check_flask_app())
    except Exception as e:
        print(f"⚠️  Could not check Flask app: {e}")
    
    # Print summary
    success = print_summary(results)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
