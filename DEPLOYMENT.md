# Ubuntu 24.04 Deployment Guide - Attendance System

Deploy the Attendance System on Ubuntu 24.04 with MySQL.

---

## Step 1: Install System Packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    mysql-server libmysqlclient-dev pkg-config git
```

---

## Step 2: Setup MySQL Database

```bash
# Start MySQL
sudo systemctl start mysql
sudo systemctl enable mysql

# Login to MySQL
sudo mysql
```

**Run these SQL commands:**
```sql
CREATE DATABASE attendance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'attendance_user'@'localhost' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON attendance_db.* TO 'attendance_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## Step 3: Clone & Setup Application

```bash
# Create directory and clone
sudo mkdir -p /var/www/attendance
sudo chown $USER:$USER /var/www/attendance
cd /var/www/attendance
git clone https://github.com/yadhumanikandan/attendance_system.git .

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 4: Configure Settings

Edit the production settings file:
```bash
nano attendance_project/settings_production.py
```

**Change these 3 values:**
```python
SECRET_KEY = 'paste-a-random-50-character-string-here'
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.1.100']  # Your server IP
DB_PASSWORD = 'your_password_here'  # Same password from Step 2
```

**Generate a secret key:**
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

---

## Step 5: Initialize Database

```bash
cd /var/www/attendance
source venv/bin/activate

# Run migrations
DJANGO_SETTINGS_MODULE=attendance_project.settings_production python manage.py migrate

# Create admin user
DJANGO_SETTINGS_MODULE=attendance_project.settings_production python manage.py createsuperuser

# Collect static files
DJANGO_SETTINGS_MODULE=attendance_project.settings_production python manage.py collectstatic --noinput
```

---

## Step 6: Test the Application

```bash
DJANGO_SETTINGS_MODULE=attendance_project.settings_production gunicorn --bind 0.0.0.0:8000 attendance_project.wsgi:application
```

Open browser: `http://YOUR_SERVER_IP:8000`

Press `Ctrl+C` to stop.

---

## Step 7: Setup as System Service

```bash
# Edit service file with your password
sudo nano /var/www/attendance/deployment/attendance.service
```

**Update the DB_PASSWORD line**, then:

```bash
# Install and start service
sudo cp deployment/attendance.service /etc/systemd/system/
sudo chown -R www-data:www-data /var/www/attendance
sudo systemctl daemon-reload
sudo systemctl enable attendance
sudo systemctl start attendance

# Check status
sudo systemctl status attendance
```

---

## Step 8: Allow Firewall Access

```bash
sudo ufw allow 8000/tcp
```

---

## Done!

Access your app at: `http://YOUR_SERVER_IP:8000`

---

## Useful Commands

```bash
# View logs
sudo journalctl -u attendance -f

# Restart app
sudo systemctl restart attendance

# Update app
cd /var/www/attendance && source venv/bin/activate
git pull
DJANGO_SETTINGS_MODULE=attendance_project.settings_production python manage.py migrate
sudo systemctl restart attendance
```
