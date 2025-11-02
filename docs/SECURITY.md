# Security Guide

## Overview

Security is paramount for network configuration tools. This guide covers security features, best practices, and hardening recommendations.

## Authentication & Authorization

### JWT Tokens

**Implementation**:
- HS256 algorithm
- Short-lived access tokens (1 hour default)
- Long-lived refresh tokens (24 hours default)
- Token rotation on refresh

**Best Practices**:
```bash
# Generate strong secrets
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Set in .env
SECRET_KEY=<generated-secret>
JWT_SECRET_KEY=<different-generated-secret>
```

**Token Storage**:
- Client: Store in memory or secure storage (not localStorage for sensitive apps)
- Server: Stateless validation

### API Keys

**Format**: `cck_<32-byte-random-string>`

**Security Features**:
- Bcrypt-hashed storage
- Optional expiration
- Per-key usage tracking
- Easy revocation

**Usage**:
```bash
# Create API key
curl -X POST http://localhost:5000/auth/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API",
    "expires_days": 90
  }'

# Use API key
curl -X POST http://localhost:5000/api/v1/generate \
  -H "X-API-Key: cck_your_key_here" \
  -d '...'
```

### Password Security

**Implementation**:
- Werkzeug password hashing (PBKDF2 + SHA256)
- Minimum 8 characters required
- No password complexity enforcement (rely on length)

**Password Change**:
```bash
curl -X POST http://localhost:5000/auth/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "current",
    "new_password": "newpassword123"
  }'
```

## Input Validation

### Multi-Layer Validation

1. **Schema Validation (Marshmallow)**
   - Type checking
   - Required field enforcement
   - Format validation

2. **Custom Validation**
   - IP address validation
   - VLAN ID ranges
   - Interface name patterns
   - OSPF parameters

3. **SQL Injection Protection**
   - SQLAlchemy parameterized queries
   - No raw SQL execution

### Example Validators

```python
# IP Address
NetworkValidator.validate_ip_address('192.168.1.1')

# VLAN ID (1-4094)
NetworkValidator.validate_vlan_id(10)

# Hostname (1-63 chars, alphanumeric + hyphen/underscore)
NetworkValidator.validate_hostname('router01')
```

## Cross-Site Scripting (XSS) Protection

### Jinja2 Auto-Escaping

All template variables are automatically escaped:

```jinja2
{{ user_input }}  {# Automatically escaped #}
```

### Content Security Policy (CSP)

Recommended Nginx header:

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self';";
```

## Cross-Site Request Forgery (CSRF)

### CSRF Protection

**Enabled by default** for form submissions:

```python
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None
```

**API Endpoints**: JWT/API key authentication provides CSRF protection

## Rate Limiting

### Configuration

```python
# config.py
RATELIMIT_ENABLED = True
RATELIMIT_DEFAULT = "100/hour"
```

### Custom Rate Limits

```python
from flask_limiter import Limiter

@limiter.limit("10/minute")
def expensive_endpoint():
    pass
```

### Storage Backends

**Development**: Memory
**Production**: Redis (recommended)

```python
RATELIMIT_STORAGE_URL = "redis://localhost:6379"
```

## Secure Headers

### Recommended Nginx Configuration

```nginx
# Security headers
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

### Flask Response Headers

```python
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

## SSL/TLS Configuration

### Certificate Setup (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d ciscoapp.example.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Nginx SSL Configuration

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;
```

## Database Security

### SQLite Security

**File Permissions**:
```bash
chmod 600 instance/config_history.db
chown ciscoapp:ciscoapp instance/config_history.db
```

**Backup Encryption**:
```bash
# Encrypt backup
gpg --symmetric --cipher-algo AES256 instance/config_history.db

# Decrypt
gpg --decrypt instance/config_history.db.gpg > config_history.db
```

### Migration to PostgreSQL (Production)

**Connection String**:
```python
DATABASE_URL = "postgresql://user:pass@localhost/ciscoapp?sslmode=require"
```

**SSL Connection**:
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'connect_args': {
        'sslmode': 'require',
        'sslcert': '/path/to/client-cert.pem',
        'sslkey': '/path/to/client-key.pem',
        'sslrootcert': '/path/to/ca-cert.pem'
    }
}
```

## Secrets Management

### Environment Variables

**Never commit** `.env` to version control:

```bash
# .gitignore
.env
.env.local
.env.*
```

### Secret Rotation

**Regular rotation schedule**:
- JWT secrets: Every 90 days
- API keys: On-demand or annually
- Database passwords: Every 90 days

**Rotation procedure**:
```bash
# 1. Generate new secret
NEW_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# 2. Update .env
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env

# 3. Restart application
sudo systemctl restart ciscoapp

# 4. Verify
curl http://localhost:5000/health
```

## Audit Logging

### Configuration History Tracking

Every configuration generation is logged:
- User ID
- IP address
- User agent
- Timestamp
- Platform and hostname
- Full configuration data

### Query Audit Logs

```python
from app import create_app
from models import ConfigHistory

app = create_app()
with app.app_context():
    # Last 24 hours
    from datetime import datetime, timedelta
    yesterday = datetime.utcnow() - timedelta(days=1)

    recent = ConfigHistory.query.filter(
        ConfigHistory.created_at >= yesterday
    ).all()

    for entry in recent:
        print(f"{entry.created_at} - {entry.user.username} - {entry.ip_address}")
```

## Penetration Testing

### Recommended Tests

1. **Authentication Bypass**
   - JWT token tampering
   - API key brute-force
   - Session hijacking

2. **Injection Attacks**
   - SQL injection
   - Template injection
   - Command injection

3. **XSS/CSRF**
   - Reflected XSS
   - Stored XSS
   - CSRF token bypass

4. **Access Control**
   - Horizontal privilege escalation
   - Vertical privilege escalation
   - API endpoint enumeration

### Testing Tools

```bash
# OWASP ZAP
zap-cli --quick-scan --self-contained \
  --start-options '-config api.disablekey=true' \
  http://localhost:5000

# Nikto
nikto -h http://localhost:5000

# SQLMap (should fail)
sqlmap -u "http://localhost:5000/api/v1/generate" \
  --data='{"platform":"ios","hostname":"test"}' \
  --level=5 --risk=3
```

## Incident Response

### Compromise Indicators

Monitor for:
- Multiple failed login attempts
- Unusual API usage patterns
- Configuration downloads from unexpected IPs
- Unauthorized admin actions

### Response Procedure

1. **Isolate**: Disable affected accounts
2. **Investigate**: Check audit logs
3. **Remediate**: Rotate secrets, patch vulnerabilities
4. **Notify**: Inform affected users
5. **Document**: Record incident details

### Log Analysis

```bash
# Failed login attempts
grep "Invalid credentials" logs/cisco_config_generator.log

# Admin actions
grep "admin" logs/cisco_config_generator.log | grep -E "DELETE|CREATE"

# Unusual activity
grep "403\|401" logs/access.log | sort | uniq -c | sort -rn
```

## Compliance

### Data Protection

**GDPR Considerations**:
- User data: Username, email, IP addresses
- Right to erasure: Delete user and associated history
- Data export: JSON export of user data

**Implementation**:
```python
# User data export
@auth_bp.route('/export', methods=['GET'])
@token_required
def export_user_data():
    user = User.query.get(g.current_user['user_id'])
    history = ConfigHistory.query.filter_by(user_id=user.id).all()

    return jsonify({
        'user': user.to_dict(),
        'configurations': [h.to_dict(include_config=True) for h in history]
    })
```

### PCI DSS (if applicable)

Not directly applicable unless processing payment data, but relevant security principles:
- Strong access controls ✓
- Encryption in transit (SSL/TLS) ✓
- Audit logging ✓
- Regular security testing ✓

## Security Checklist

### Deployment

- [ ] Change default admin password
- [ ] Set strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Enable HTTPS with valid certificate
- [ ] Configure firewall (ports 80, 443 only)
- [ ] Set `FLASK_ENV=production`
- [ ] Disable debug mode
- [ ] Enable rate limiting
- [ ] Configure secure session cookies
- [ ] Set up automated backups
- [ ] Enable audit logging
- [ ] Configure intrusion detection (Fail2ban)
- [ ] Implement log rotation
- [ ] Set file permissions correctly
- [ ] Disable directory listing
- [ ] Remove sensitive files from web root

### Ongoing

- [ ] Regular security updates
- [ ] Monthly secret rotation
- [ ] Quarterly penetration testing
- [ ] Review audit logs weekly
- [ ] Backup verification monthly
- [ ] Dependency vulnerability scans
- [ ] User access review
- [ ] SSL certificate renewal

## Reporting Security Issues

**Do NOT** create public GitHub issues for security vulnerabilities.

Contact: security@example.com

Include:
- Description of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if known)

We aim to respond within 48 hours and provide a fix within 30 days for critical issues.

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
