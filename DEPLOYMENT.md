# Ubuntu 24.04 Deployment Guide - Attendance System

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
sudo systemctl start mysql
sudo systemctl enable mysql
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
sudo mkdir -p /var/www/attendance
sudo chown $USER:$USER /var/www/attendance
cd /var/www/attendance
git clone https://github.com/yadhumanikandan/attendance_system.git .

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 4: Create .env File

```bash
cp .env.example .env
nano .env
```

**Edit the 3 values:**
```
SECRET_KEY=paste-a-random-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.100
DB_PASSWORD=your_password_here
```

**Generate secret key:**
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

---

## Step 5: Initialize Database

```bash
source venv/bin/activate
DJANGO_SETTINGS_MODULE=attendance_project.settings_production python manage.py migrate
DJANGO_SETTINGS_MODULE=attendance_project.settings_production python manage.py createsuperuser
DJANGO_SETTINGS_MODULE=attendance_project.settings_production python manage.py collectstatic --noinput
```

---

## Step 6: Test Application

```bash
DJANGO_SETTINGS_MODULE=attendance_project.settings_production gunicorn --bind 0.0.0.0:8000 attendance_project.wsgi:application
```

Open: `http://YOUR_SERVER_IP:8000` | Press `Ctrl+C` to stop.

---

## Step 7: Setup System Service

```bash
sudo cp deployment/attendance.service /etc/systemd/system/
sudo chown -R www-data:www-data /var/www/attendance
sudo systemctl daemon-reload
sudo systemctl enable attendance
sudo systemctl start attendance
```

---

## Step 8: Allow Firewall

```bash
sudo ufw allow 8000/tcp
```

---

## Done! 

Access: `http://YOUR_SERVER_IP:8000`

---

## Quick Commands

```bash
sudo journalctl -u attendance -f          # View logs
sudo systemctl restart attendance         # Restart app
sudo systemctl status attendance          # Check status
```
