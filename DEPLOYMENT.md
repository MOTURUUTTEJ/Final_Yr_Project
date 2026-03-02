# Deployment Guide - Brain Stroke Risk Prediction

## 📦 Production Deployment

This guide covers deploying the Brain Stroke Risk Prediction application to production.

---

## 1. Prepare for Production

### 1.1 Update Configuration
Edit `config.py` and set secure values:

```python
class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = 'your-very-secure-random-key-here'
    SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost/stroke_db'
```

Generate a secure secret key:
```python
import secrets
print(secrets.token_hex(32))
```

### 1.2 Create `.env` File
```bash
cp .env.example .env
```

Update `.env` with production values:
```
FLASK_ENV=production
SECRET_KEY=your-secure-key
DATABASE_URL=postgresql://user:password@localhost/stroke_db
APP_HOST=0.0.0.0
APP_PORT=5000
```

### 1.3 Update `app.py`
Change the configuration at the end:
```python
if __name__ == '__main__':
    config_name = os.environ.get('FLASK_ENV', 'development')
    from config import config
    app.config.from_object(config[config_name])
    app.run(debug=False)  # Never use debug=True in production
```

---

## 2. Choose a Deployment Platform

### Option A: Heroku

#### 2A.1 Create Procfile
```bash
echo "web: gunicorn app:app" > Procfile
```

#### 2A.2 Create requirements.txt
```bash
pip freeze > requirements.txt
# Add gunicorn if not present
echo "gunicorn==21.2.0" >> requirements.txt
```

#### 2A.3 Deploy
```bash
heroku login
heroku create your-app-name
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=your-secret-key
git push heroku main
```

### Option B: AWS

#### 2B.1 Install AWS CLI
```bash
pip install awscli
aws configure
```

#### 2B.2 Deploy with Elastic Beanstalk
```bash
# Install EB CLI
pip install awsebcli

# Initialize EB
eb init

# Create environment
eb create stroke-prediction

# Deploy
eb deploy
```

### Option C: DigitalOcean

#### 2C.1 Create Droplet
- Create Ubuntu 22.04 LTS droplet
- SSH into the server

#### 2C.2 Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and packages
sudo apt install python3-pip python3-venv nginx -y

# Clone repository
git clone <your-repo-url>
cd "Brain Stroke risk Prediction using ML on"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt
pip install gunicorn
```

#### 2C.3 Configure Gunicorn
Create `wsgi.py`:
```python
from app import app

if __name__ == "__main__":
    app.run()
```

Create `/etc/systemd/system/stroke-app.service`:
```ini
[Unit]
Description=Stroke Risk Prediction
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/home/ubuntu/stroke-app
Environment="PATH=/home/ubuntu/stroke-app/venv/bin"
ExecStart=/home/ubuntu/stroke-app/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 wsgi:app

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl start stroke-app
sudo systemctl enable stroke-app
```

#### 2C.4 Configure Nginx
Create `/etc/nginx/sites-available/stroke-app`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /home/ubuntu/stroke-app/static;
    }
}
```

Enable and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/stroke-app /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

---

## 3. Database Setup

### For PostgreSQL (Recommended for Production)

#### 3.1 Install PostgreSQL
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE stroke_db;
CREATE USER stroke_user WITH PASSWORD 'secure_password';
ALTER ROLE stroke_user SET client_encoding TO 'utf8';
ALTER ROLE stroke_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE stroke_user SET default_transaction_deferrable TO on;
ALTER ROLE stroke_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE stroke_db TO stroke_user;
```

#### 3.2 Update Database URL
```python
SQLALCHEMY_DATABASE_URI = 'postgresql://stroke_user:secure_password@localhost/stroke_db'
```

#### 3.3 Initialize Database
```python
from app import app, db
with app.app_context():
    db.create_all()
```

---

## 4. Security Hardening

### 4.1 SSL/TLS Certificate
Use Let's Encrypt for free SSL:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
```

Update Nginx:
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Redirect HTTP to HTTPS
    if ($scheme != "https") {
        return 301 https://$server_name$request_uri;
    }
    
    location / {
        proxy_pass http://127.0.0.1:5000;
    }
}
```

### 4.2 Security Headers
Add to Nginx configuration:
```nginx
add_header X-Frame-Options "SAMEORIGIN";
add_header X-Content-Type-Options "nosniff";
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
```

### 4.3 Rate Limiting
Add to `app.py`:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # Login logic
```

---

## 5. Monitoring & Logging

### 5.1 Application Logging
Update `app.py`:
```python
import logging
from logging.handlers import RotatingFileHandler
import os

if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/stroke_app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Stroke Risk Prediction app startup')
```

### 5.2 Error Tracking
Add Sentry integration:
```bash
pip install sentry-sdk
```

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://your-sentry-dsn@sentry.io/project-id",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

---

## 6. Performance Optimization

### 6.1 Enable Caching
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/dashboard')
@cache.cached(timeout=60)
def dashboard():
    # Dashboard logic
```

### 6.2 Database Connection Pooling
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}
```

### 6.3 Minify Static Assets
```bash
pip install flask-minify
```

---

## 7. Backup & Recovery

### 7.1 Database Backup (PostgreSQL)
```bash
# Daily backup
0 2 * * * /usr/bin/pg_dump -U stroke_user stroke_db > /backups/stroke_db_$(date +\%Y\%m\%d).sql

# Add to crontab
crontab -e
```

### 7.2 Application Backup
```bash
tar -czf stroke_app_backup_$(date +%Y%m%d).tar.gz /home/ubuntu/stroke-app/
```

---

## 8. Troubleshooting

### Database Connection Failed
```bash
psql -U stroke_user -d stroke_db -h localhost
# Test connection
```

### Port Already in Use
```bash
lsof -i :5000  # Find process
kill -9 <PID>  # Kill process
```

### Permission Denied
```bash
sudo chown -R www-data:www-data /home/ubuntu/stroke-app
sudo chmod -R 755 /home/ubuntu/stroke-app
```

### Out of Memory
```bash
free -h  # Check memory
# Increase swap or upgrade instance
```

---

## 9. Monitoring Checklist

- [ ] SSL certificate valid
- [ ] Database backups running
- [ ] Error logs monitored
- [ ] Application uptime tracked
- [ ] Security updates applied
- [ ] Performance metrics collected
- [ ] Firewall rules configured
- [ ] User access logs enabled

---

## 10. Disaster Recovery Plan

1. **Daily**: Automated database backups
2. **Weekly**: Full application backup
3. **Monthly**: Disaster recovery drill
4. **Quarterly**: Security audit

---

**Deployment Complete!** 🚀

Your Brain Stroke Risk Prediction application is now live and ready for users!
