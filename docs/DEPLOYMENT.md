# Deployment Guide

## Overview

This guide covers deploying the Cisco Configuration Generator in various environments.

## Prerequisites

- Python 3.11 or higher
- Git
- Docker (for containerized deployment)
- 2GB RAM minimum
- 10GB disk space

## Deployment Options

### 1. Native Deployment (Production)

#### Step 1: Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.11 python3.11-venv python3-pip nginx -y

# Create application user
sudo useradd -m -s /bin/bash ciscoapp
sudo su - ciscoapp
```

#### Step 2: Application Setup

```bash
# Clone repository
git clone https://github.com/appatrous/appa.git
cd appa

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 3: Configuration

```bash
# Create production environment file
cp .env.example .env

# Generate secure secrets
python3 << EOF
import secrets
print(f"SECRET_KEY={secrets.token_urlsafe(32)}")
print(f"JWT_SECRET_KEY={secrets.token_urlsafe(32)}")
EOF

# Edit .env with generated secrets
nano .env
```

Set these variables:
```env
FLASK_ENV=production
SECRET_KEY=<generated-secret>
JWT_SECRET_KEY=<generated-secret>
DATABASE_URL=sqlite:////home/ciscoapp/appa/instance/config_history.db
SESSION_COOKIE_SECURE=True
HISTORY_RETENTION_DAYS=90
```

#### Step 4: Download Bootstrap (Offline)

```bash
cd static/css
curl -O https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css

cd ../js
curl -O https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js
cd ../..
```

#### Step 5: Initialize Database

```bash
# Create instance directory
mkdir -p instance

# Initialize database
python << EOF
from app import create_app
from models import db

app = create_app('production')
with app.app_context():
    db.create_all()
    print("Database initialized successfully")
EOF
```

#### Step 6: Test Application

```bash
# Test run
python app.py

# In another terminal
curl http://localhost:5000/health
```

#### Step 7: Systemd Service

Create `/etc/systemd/system/ciscoapp.service`:

```ini
[Unit]
Description=Cisco Configuration Generator
After=network.target

[Service]
Type=notify
User=ciscoapp
Group=ciscoapp
WorkingDirectory=/home/ciscoapp/appa
Environment="PATH=/home/ciscoapp/appa/venv/bin"
ExecStart=/home/ciscoapp/appa/venv/bin/gunicorn \
    --bind 127.0.0.1:5000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile /home/ciscoapp/appa/logs/access.log \
    --error-logfile /home/ciscoapp/appa/logs/error.log \
    --log-level info \
    "app:create_app('production')"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ciscoapp
sudo systemctl start ciscoapp
sudo systemctl status ciscoapp
```

#### Step 8: Nginx Reverse Proxy

Create `/etc/nginx/sites-available/ciscoapp`:

```nginx
server {
    listen 80;
    server_name ciscoapp.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ciscoapp.example.com;

    # SSL Configuration (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/ciscoapp.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ciscoapp.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/ciscoapp_access.log;
    error_log /var/log/nginx/ciscoapp_error.log;

    # Client body size
    client_max_body_size 16M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Static files caching
    location /static/ {
        alias /home/ciscoapp/appa/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable and test:

```bash
sudo ln -s /etc/nginx/sites-available/ciscoapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 2. Docker Deployment

#### Simple Deployment

```bash
# Clone repository
git clone https://github.com/appatrous/appa.git
cd appa

# Build image
docker build -t cisco-config-generator .

# Run container
docker run -d \
  --name ciscoapp \
  -p 5000:5000 \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/logs:/app/logs \
  -e SECRET_KEY=your-secret-key \
  -e JWT_SECRET_KEY=your-jwt-secret \
  cisco-config-generator
```

#### Docker Compose Deployment

```bash
# Create environment file
cat > .env << EOF
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
EOF

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Air-Gapped Deployment

For completely offline environments:

#### Step 1: Package Application

On internet-connected machine:

```bash
# Download all dependencies
pip download -r requirements.txt -d packages/

# Download Bootstrap
mkdir -p offline-assets
cd offline-assets
curl -O https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css
curl -O https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js
cd ..

# Create deployment archive
tar czf ciscoapp-deploy.tar.gz \
  app.py config.py models.py requirements.txt \
  extensions/ utils/ templates/ static/ tests/ docs/ \
  packages/ offline-assets/ \
  .env.example Dockerfile docker-compose.yml
```

#### Step 2: Deploy to Air-Gapped System

```bash
# Transfer and extract
scp ciscoapp-deploy.tar.gz user@airgapped-server:~/
ssh user@airgapped-server
tar xzf ciscoapp-deploy.tar.gz
cd appa

# Install from local packages
python3 -m venv venv
source venv/bin/activate
pip install --no-index --find-links=packages/ -r requirements.txt

# Copy Bootstrap assets
cp offline-assets/bootstrap.min.css static/css/
cp offline-assets/bootstrap.bundle.min.js static/js/

# Configure and run
cp .env.example .env
# Edit .env...
python app.py
```

## Database Management

### Backup

```bash
# SQLite backup
cp instance/config_history.db instance/config_history.db.backup.$(date +%Y%m%d)

# Automated daily backup (crontab)
0 2 * * * cd /home/ciscoapp/appa && cp instance/config_history.db instance/backups/config_history.db.$(date +\%Y\%m\%d)
```

### Restore

```bash
cp instance/config_history.db.backup.20240101 instance/config_history.db
sudo systemctl restart ciscoapp
```

### Migration

```bash
# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade

# Rollback
flask db downgrade
```

## Monitoring

### Application Logs

```bash
# View logs
tail -f logs/cisco_config_generator.log

# Search for errors
grep ERROR logs/cisco_config_generator.log

# Access logs (if using gunicorn)
tail -f logs/access.log
```

### System Monitoring

```bash
# Check service status
sudo systemctl status ciscoapp

# View resource usage
htop

# Check disk space
df -h

# Database size
du -h instance/config_history.db
```

### Health Checks

```bash
# Application health
curl http://localhost:5000/health

# API check
curl -X POST http://localhost:5000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"platform": "ios", "hostname": "test"}'
```

## Scaling

### Horizontal Scaling

Use load balancer (HAProxy/Nginx) with multiple application instances:

```nginx
upstream ciscoapp_backend {
    least_conn;
    server 192.168.1.10:5000;
    server 192.168.1.11:5000;
    server 192.168.1.12:5000;
}

server {
    listen 443 ssl;
    server_name ciscoapp.example.com;

    location / {
        proxy_pass http://ciscoapp_backend;
        # ... proxy settings ...
    }
}
```

### Database Scaling

For high-traffic environments, migrate from SQLite to PostgreSQL:

1. Update `requirements.txt`:
```
psycopg2-binary==2.9.9
```

2. Update `.env`:
```
DATABASE_URL=postgresql://user:pass@localhost/ciscoapp
```

3. Migrate data using `pgloader` or custom script

## Troubleshooting

### Application Won't Start

```bash
# Check logs
sudo journalctl -u ciscoapp -n 50

# Test configuration
python -c "from app import create_app; app = create_app('production'); print('OK')"

# Check permissions
ls -la instance/
```

### Database Errors

```bash
# Verify database
sqlite3 instance/config_history.db "PRAGMA integrity_check;"

# Reset database (CAUTION: destroys data)
rm instance/config_history.db
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Performance Issues

- Increase gunicorn workers
- Add Redis for rate limiting
- Optimize database queries
- Enable caching

## Maintenance

### Updates

```bash
# Pull latest code
cd /home/ciscoapp/appa
git pull

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Run migrations
flask db upgrade

# Restart service
sudo systemctl restart ciscoapp
```

### Cleanup

```bash
# Clean old history (90+ days)
python << EOF
from app import create_app
from models import db, ConfigHistory
from datetime import datetime, timedelta

app = create_app('production')
with app.app_context():
    cutoff = datetime.utcnow() - timedelta(days=90)
    deleted = ConfigHistory.query.filter(
        ConfigHistory.created_at < cutoff
    ).delete()
    db.session.commit()
    print(f"Deleted {deleted} old records")
EOF
```

## Security Hardening

1. **Firewall**: Only allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS)
2. **Fail2ban**: Install to prevent brute-force attacks
3. **Updates**: Keep system packages updated
4. **Backups**: Regular automated backups
5. **SSL**: Use valid SSL certificates (Let's Encrypt)
6. **Secrets**: Rotate secrets regularly
7. **Access**: Restrict SSH to key-based authentication

## Support

For deployment issues:
- Check logs: `logs/cisco_config_generator.log`
- Review documentation: `docs/`
- GitHub Issues: https://github.com/appatrous/appa/issues
