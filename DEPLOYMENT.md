# Ubuntu 24.04 Deployment Guide - Attendance System

This guide walks you through deploying the Attendance System on Ubuntu 24.04 with MySQL and Gunicorn.

## Prerequisites

- Ubuntu 24.04 LTS server
- Root or sudo access
- Server IP accessible on your internal network

---

## Step 1: Update System & Install Required Packages

```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    mysql-server libmysqlclient-dev pkg-config \
    git nginx
```

---

## Step 2: Configure MySQL

```bash
# Start MySQL service
sudo systemctl start mysql
sudo systemctl enable mysql

# Secure MySQL installation (optional but recommended)
sudo mysql_secure_installation

# Login to MySQL as root
sudo mysql -u root -p
```

**Inside MySQL, run these commands:**

```sql
-- Create database
CREATE DATABASE attendance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (replace 'your_secure_password' with a strong password)
CREATE USER 'attendance_user'@'localhost' IDENTIFIED BY 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON attendance_db.* TO 'attendance_user'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;

-- Exit MySQL
EXIT;
```

---

## Step 3: Clone and Setup the Application

```bash
# Create application directory
sudo mkdir -p /var/www/attendance
sudo chown $USER:$USER /var/www/attendance

# Clone the repository
cd /var/www/attendance
git clone https://github.com/yadhumanikandan/attendance_system.git .

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 4: Configure Environment Variables

Create an environment file to store sensitive settings:

```bash
sudo nano /var/www/attendance/.env
```

Add the following content (update values as needed):

```bash
DJANGO_SECRET_KEY=your-very-long-random-secret-key-here
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,YOUR_SERVER_IP
DB_NAME=attendance_db
DB_USER=attendance_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=3306
```

**Generate a secure secret key:**
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

---

## Step 5: Modify Settings to Use Environment File

Edit the production settings file to load from `.env`:

```bash
nano /var/www/attendance/attendance_project/settings_production.py
```

Or simply export variables before running commands:

```bash
source /var/www/attendance/.env
export DJANGO_SECRET_KEY DJANGO_ALLOWED_HOSTS DB_NAME DB_USER DB_PASSWORD DB_HOST DB_PORT
```

---

## Step 6: Initialize the Database

```bash
cd /var/www/attendance
source venv/bin/activate

# Set Django settings module
export DJANGO_SETTINGS_MODULE=attendance_project.settings_production

# Export environment variables
export DJANGO_SECRET_KEY='your-secret-key'
export DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1,YOUR_SERVER_IP'
export DB_NAME='attendance_db'
export DB_USER='attendance_user'
export DB_PASSWORD='your_secure_password'
export DB_HOST='localhost'
export DB_PORT='3306'

# Run migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

---

## Step 7: Test the Application Manually

```bash
# Test with Gunicorn
gunicorn --bind 0.0.0.0:8000 attendance_project.wsgi:application
```

Open a browser and visit: `http://YOUR_SERVER_IP:8000`

Press `Ctrl+C` to stop the test server.

---

## Step 8: Setup Systemd Service

```bash
# Copy the service file
sudo cp /var/www/attendance/deployment/attendance.service /etc/systemd/system/

# Edit the service file with your actual values
sudo nano /etc/systemd/system/attendance.service
```

**Update these lines in the service file:**
- `Environment="DJANGO_SECRET_KEY=your-actual-secret-key"`
- `Environment="DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,YOUR_SERVER_IP"`
- `Environment="DB_PASSWORD=your_actual_db_password"`

```bash
# Change ownership of the application directory
sudo chown -R www-data:www-data /var/www/attendance

# Reload systemd
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable attendance

# Start the service
sudo systemctl start attendance

# Check status
sudo systemctl status attendance
```

---

## Step 9: Configure Nginx (Optional - Recommended)

Nginx acts as a reverse proxy, handling client requests efficiently.

```bash
sudo nano /etc/nginx/sites-available/attendance
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name YOUR_SERVER_IP;

    location /static/ {
        alias /var/www/attendance/staticfiles/;
    }

    location /media/ {
        alias /var/www/attendance/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/attendance /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

---

## Step 10: Configure Firewall

```bash
# Allow HTTP traffic
sudo ufw allow 80/tcp

# If not using Nginx, allow port 8000 directly
sudo ufw allow 8000/tcp

# Enable firewall (if not already enabled)
sudo ufw enable
```

---

## Step 11: Verify Deployment

1. Open a browser on any computer in your network
2. Navigate to: `http://YOUR_SERVER_IP` (port 80 with Nginx) or `http://YOUR_SERVER_IP:8000` (direct Gunicorn)
3. Login with the superuser account you created

---

## Maintenance Commands

```bash
# View application logs
sudo journalctl -u attendance -f

# Restart application
sudo systemctl restart attendance

# Stop application
sudo systemctl stop attendance

# Update application
cd /var/www/attendance
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart attendance
```

---

## Troubleshooting

### Application won't start
```bash
# Check logs
sudo journalctl -u attendance -n 50

# Check if MySQL is running
sudo systemctl status mysql
```

### Database connection errors
```bash
# Test MySQL connection
mysql -u attendance_user -p -h localhost attendance_db
```

### Static files not loading
```bash
# Re-collect static files
cd /var/www/attendance
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=attendance_project.settings_production
python manage.py collectstatic --noinput

# Check permissions
sudo chown -R www-data:www-data /var/www/attendance/staticfiles
```

---

## Quick Reference

| Item | Value |
|------|-------|
| Application Directory | `/var/www/attendance` |
| Virtual Environment | `/var/www/attendance/venv` |
| Systemd Service | `attendance.service` |
| MySQL Database | `attendance_db` |
| MySQL User | `attendance_user` |
| Default Port | 8000 (Gunicorn) / 80 (Nginx) |
