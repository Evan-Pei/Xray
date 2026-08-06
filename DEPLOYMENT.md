# Xray Deployment Guide

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Linux Systemd Deployment](#linux-systemd-deployment)
4. [OAuth Configuration](#oauth-configuration)

---

## Local Development

### Prerequisites
- Python 3.8+
- pip
- SQLite (included with Python)

### Setup

1. **Clone and navigate to the project:**
   ```bash
   git clone https://github.com/Evan-Pei/Xray.git
   cd Xray
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```
   
   Access at `http://localhost:5000`

---

## Docker Deployment

### Quick Start with Docker Compose

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Evan-Pei/Xray.git
   cd Xray
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit docker-compose.yml and .env with your settings
   ```

3. **Start services:**
   ```bash
   docker-compose up -d
   ```

4. **Access the application:**
   - Web: `http://localhost:5000`
   - Database: `localhost:5432`

5. **Manage services:**
   ```bash
   # View logs
   docker-compose logs -f web
   
   # Stop services
   docker-compose down
   
   # Rebuild image
   docker-compose build --no-cache
   ```

### Production Deployment with Docker

1. **Build image:**
   ```bash
   docker build -t xray:latest .
   ```

2. **Run container:**
   ```bash
   docker run -d \
     --name xray \
     -p 5000:5000 \
     -e DATABASE_URL="postgresql://user:pass@db-host:5432/xray" \
     -e SECRET_KEY="your-production-secret-key" \
     -e ADMIN_USERNAME="admin" \
     -e ADMIN_PASSWORD="your-secure-password" \
     -e OAUTH_ENABLED="true" \
     -e OAUTH_CLIENT_ID="your-client-id" \
     -e OAUTH_CLIENT_SECRET="your-client-secret" \
     -e OAUTH_AUTHORIZE_URL="https://auth.provider.com/authorize" \
     -e OAUTH_TOKEN_URL="https://auth.provider.com/token" \
     -e OAUTH_USERINFO_URL="https://auth.provider.com/userinfo" \
     -e OAUTH_REDIRECT_URI="https://xray.example.com/auth/oauth/callback" \
     xray:latest
   ```

---

## Linux Systemd Deployment

### Prerequisites
- Ubuntu/Debian or other systemd-based Linux
- Python 3.8+
- PostgreSQL (optional, for production)

### Setup

1. **Create application directory:**
   ```bash
   sudo mkdir -p /opt/xray
   cd /opt/xray
   ```

2. **Clone repository:**
   ```bash
   sudo git clone https://github.com/Evan-Pei/Xray.git .
   ```

3. **Create virtual environment:**
   ```bash
   sudo python3 -m venv venv
   ```

4. **Install dependencies:**
   ```bash
   sudo venv/bin/pip install -r requirements.txt
   ```

5. **Configure environment:**
   ```bash
   sudo cp .env.example .env
   sudo nano .env  # Edit with your configuration
   ```

6. **Set ownership:**
   ```bash
   sudo chown -R www-data:www-data /opt/xray
   ```

### Create Systemd Service

Create `/etc/systemd/system/xray.service`:

```ini
[Unit]
Description=Xray Machine Booking Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/xray
Environment="PATH=/opt/xray/venv/bin"
EnvironmentFile=/opt/xray/.env
ExecStart=/opt/xray/venv/bin/gunicorn \
    --workers 4 \
    --timeout 120 \
    --bind 0.0.0.0:5000 \
    app:app

Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable xray

# Start the service
sudo systemctl start xray

# Check status
sudo systemctl status xray

# View logs
sudo journalctl -u xray -f
```

### Nginx Reverse Proxy Configuration

Create `/etc/nginx/sites-available/xray`:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name xray.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name xray.example.com;

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/xray.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/xray.example.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy settings
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Enable and test:
```bash
sudo ln -s /etc/nginx/sites-available/xray /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## OAuth Configuration

### Prerequisites
- OAuth provider (Frore, Google Workspace, Microsoft Azure, etc.)
- Registered application with OAuth provider
- Client ID and Client Secret

### Environment Variables

Add to `.env`:

```env
# Enable OAuth
OAUTH_ENABLED=true

# OAuth Provider (frore, google, microsoft, etc.)
OAUTH_PROVIDER=frore

# OAuth Credentials (from provider)
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret

# OAuth Endpoints (from provider)
OAUTH_AUTHORIZE_URL=https://auth.provider.com/oauth/authorize
OAUTH_TOKEN_URL=https://auth.provider.com/oauth/token
OAUTH_USERINFO_URL=https://auth.provider.com/oauth/userinfo

# Redirect URI (must be registered with OAuth provider)
OAUTH_REDIRECT_URI=https://xray.example.com/auth/oauth/callback

# OAuth Scope (default: openid email profile)
OAUTH_SCOPE=openid email profile
```

### Testing OAuth

1. Start the application
2. Navigate to login page
3. Click "Sign in with [Provider]"
4. Complete authentication with OAuth provider
5. User will be automatically created and logged in

### User Management

- **Local users**: Username + password login
- **OAuth users**: Automatically created on first login
- **Admin approval**: New OAuth users are created with `is_qualified=False` and require admin approval

---

## Database Management

### SQLite (Development)

```bash
# Database file
ls -la xray.db

# Backup
cp xray.db xray.db.backup

# Reset (WARNING: deletes all data)
rm xray.db
python app.py  # Will recreate tables
```

### PostgreSQL (Production)

```bash
# Create database
createdb -U postgres xray

# Backup
pg_dump -U postgres xray > xray.backup.sql

# Restore
psql -U postgres xray < xray.backup.sql
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -h localhost -U xray -d xray

# Check DATABASE_URL format
postgresql://username:password@host:port/database
```

### OAuth Login Not Working

1. **Check OAuth configuration:**
   ```bash
   grep OAUTH_ .env
   ```

2. **Verify redirect URI matches provider configuration**

3. **Check application logs:**
   ```bash
   # For Systemd
   sudo journalctl -u xray -f
   
   # For Docker
   docker logs xray-web
   ```

4. **Test OAuth endpoints:**
   ```bash
   curl -X GET "https://auth.provider.com/oauth/authorize?client_id=..."
   ```

---

## Security Checklist

- [ ] Change `SECRET_KEY` in `.env`
- [ ] Use strong `ADMIN_PASSWORD`
- [ ] Enable HTTPS with SSL/TLS
- [ ] Use PostgreSQL in production (not SQLite)
- [ ] Restrict database access
- [ ] Set `FLASK_DEBUG=0` in production
- [ ] Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- [ ] Regularly backup database
- [ ] Monitor logs for suspicious activity

---

## Support

For issues or questions:
1. Check [GitHub Issues](https://github.com/Evan-Pei/Xray/issues)
2. Review logs for error messages
3. Verify environment configuration
4. Test OAuth provider credentials
