# TCR Attendance Deployment Guide
## Ubuntu 22.04 On-Premise Server (Internal Use)

---

## Prerequisites
- Ubuntu 22.04 LTS server
- Root or sudo access
- Project files (from your Mac)
- Server IP accessible on internal network

---

## Step 1: Update System & Install Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv nginx -y
```

---

## Step 2: Create Application User

```bash
sudo useradd -m -s /bin/bash attendance
sudo passwd attendance  # Set a password
```

---

## Step 3: Transfer Project Files

**On your Mac**, zip and transfer:
```bash
# On Mac - create archive (exclude venv and db)
cd /Users/yadhumanikandan/Developer
zip -r att.zip att -x "att/venv/*" -x "att/__pycache__/*" -x "att/*/__pycache__/*"

# Transfer to server (replace IP)
scp att.zip username@SERVER_IP:/tmp/
```

**On the server:**
```bash
sudo mkdir -p /var/www/attendance
sudo unzip /tmp/att.zip -d /var/www/
sudo mv /var/www/att/* /var/www/attendance/
sudo chown -R attendance:attendance /var/www/attendance
```

---

## Step 4: Setup Python Virtual Environment

```bash
sudo -u attendance bash
cd /var/www/attendance
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server
```

---

## Step 5: Configure Django for Production

Edit [attendance_project/settings.py](file:///Users/yadhumanikandan/Developer/att/attendance_project/settings.py):

```python
# SECURITY: Set these for production
DEBUG = False
ALLOWED_HOSTS = ['your-server-ip', 'attendance.local', 'localhost']

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/attendance/staticfiles/'
```

Collect static files:
```bash
python manage.py collectstatic --noinput
```

---

## Step 6: Run Migrations & Create Superuser

```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## Step 7: Test Gunicorn

```bash
cd /var/www/attendance
gunicorn --bind 0.0.0.0:8000 attendance_project.wsgi:application
```

Visit `http://SERVER_IP:8000` to test. Press `Ctrl+C` to stop.

---

## Step 8: Create Gunicorn Systemd Service

```bash
sudo nano /etc/systemd/system/attendance.service
```

Paste this content:
```ini
[Unit]
Description=TCR Attendance Gunicorn Daemon
After=network.target

[Service]
User=attendance
Group=attendance
WorkingDirectory=/var/www/attendance
ExecStart=/var/www/attendance/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/attendance/attendance.sock \
    attendance_project.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl start attendance
sudo systemctl enable attendance
sudo systemctl status attendance  # Check if running
```

---

## Step 9: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/attendance
```

Paste this content:
```nginx
server {
    listen 80;
    server_name YOUR_SERVER_IP attendance.local;

    location /static/ {
        alias /var/www/attendance/staticfiles/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/attendance/attendance.sock;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/attendance /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

---

## Step 10: Configure Firewall

```bash
sudo ufw allow 'Nginx HTTP'
sudo ufw allow ssh
sudo ufw enable
sudo ufw status
```

---

## Step 11: Access the Application

Your app is now live at:
- **http://YOUR_SERVER_IP/**
- **http://YOUR_SERVER_IP/admin/**
- **http://YOUR_SERVER_IP/report/**

---

## Maintenance Commands

```bash
# View logs
sudo journalctl -u attendance -f

# Restart application after code changes
sudo systemctl restart attendance

# Restart Nginx
sudo systemctl restart nginx

# Backup database
sudo cp /var/www/attendance/db.sqlite3 /backup/db_$(date +%Y%m%d).sqlite3
```

---

## Optional: Setup Automatic Daily Backup

```bash
sudo nano /etc/cron.daily/attendance-backup
```

```bash
#!/bin/bash
cp /var/www/attendance/db.sqlite3 /backup/attendance_db_$(date +%Y%m%d).sqlite3
find /backup -name "attendance_db_*.sqlite3" -mtime +30 -delete
```

```bash
sudo chmod +x /etc/cron.daily/attendance-backup
sudo mkdir -p /backup
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 502 Bad Gateway | Check if gunicorn is running: `sudo systemctl status attendance` |
| Static files not loading | Run `python manage.py collectstatic` |
| Permission denied | Check ownership: `sudo chown -R attendance:attendance /var/www/attendance` |
| Can't connect | Check firewall: `sudo ufw status` |
