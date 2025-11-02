# Cisco Configuration Generator

**Enterprise-grade, CCIE-level Flask web application** for generating Cisco device configurations supporting **ALL protocols** (IOS, NX-OS, ASA, IOS-XR).

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![CCIE](https://img.shields.io/badge/CCIE-Ready-red.svg)](docs/CCIE_GUIDE.md)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Features

### Core Capabilities
- ✅ **Multi-Platform Support**: IOS, IOS-XE, NX-OS, IOS-XR, ASA, FTD
- ✅ **CCIE-Level Configuration**: Complete protocol coverage
- ✅ **Multiple Output Formats**: CLI, JSON, YAML
- ✅ **Offline-First Architecture**: Zero external dependencies
- ✅ **REST API**: Full RESTful API with versioning
- ✅ **Web Interface**: Modern Bootstrap 5 UI
- ✅ **Validation & Explanation**: Auto-validation with technical explanations

### Enterprise Features
- 🔐 **JWT Authentication**: Secure token-based auth
- 🔑 **API Key Management**: Programmatic access control
- 📊 **Configuration History**: SQLAlchemy-backed tracking
- ✅ **Input Validation**: Comprehensive validation for all network parameters
- 🔒 **Security Hardening**: CSRF protection, secure headers, rate limiting
- 📝 **Schema Validation**: Marshmallow schemas for API requests

### CCIE Protocol Coverage

#### Layer 2 (Switch)
- VLANs, STP/RSTP/MST, EtherChannel (LACP/PAgP), VTP, QinQ, PVLAN
- Port Security, DHCP Snooping, DAI, IGMP Snooping, StackWise/vPC

#### Layer 3 (Router/L3 Switch)
- Static, OSPF (v2/v3), EIGRP, IS-IS, RIP, BGP
- HSRP, VRRP, GLBP, PBR, VRF-Lite, MPLS, Segment Routing, BFD

#### Multicast
- IGMPv1-3, PIM-SM/DM/SSM/BIDIR, MSDP, Auto-RP, Anycast-RP

#### VPN
- IPsec, GRE, DMVPN, FlexVPN, GETVPN, L2TP, SSL VPN (AnyConnect)

#### Security
- ACL, Zone-Based Firewall, CBAC, ASA Policies, IPS/IDS
- TrustSec, 802.1X, Port Security, DAI, uRPF

#### QoS
- LLQ, CBWFQ, Shaping, Policing, WRED, AutoQoS, NBAR2

#### Services
- NAT/PAT, DHCP, DNS, SNMP, Syslog, NTP, PTP, NetFlow/IPFIX, EEM

#### Infrastructure
- NSF/SSO, ISSU, CoPP, Smart Licensing, NETCONF/RESTCONF

## 📁 Architecture

```
appa/
├── app.py                      # Flask application factory
├── config.py                   # Configuration management
├── models.py                   # SQLAlchemy models
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker containerization
├── docker-compose.yml          # Docker Compose setup
│
├── extensions/                 # Flask blueprints
│   ├── api.py                 # REST API v1
│   ├── auth_routes.py         # Authentication endpoints
│   └── history.py             # Configuration history
│
├── utils/                      # Utility modules
│   ├── validators.py          # Input validation
│   ├── auth.py                # JWT & API key management
│   └── renderer.py            # Jinja2 rendering engine
│
├── templates/                  # Jinja2 templates
│   ├── index.html             # Web UI
│   ├── ios_config.j2          # IOS template
│   ├── nxos_config.j2         # NX-OS template
│   ├── asa_config.j2          # ASA template
│   └── iosxr_config.j2        # IOS-XR template
│
├── static/                     # Static assets
│   ├── css/
│   │   ├── bootstrap.min.css  # Bootstrap 5 (offline)
│   │   └── custom.css         # Custom styles
│   └── js/
│       ├── bootstrap.bundle.min.js
│       └── app.js             # Application logic
│
├── tests/                      # Test suite
│   ├── conftest.py            # Pytest fixtures
│   ├── test_api.py            # API tests
│   ├── test_auth.py           # Authentication tests
│   └── test_validators.py    # Validation tests
│
└── docs/                       # Documentation
    ├── API_SPEC.md
    ├── ARCHITECTURE.md
    ├── DEPLOYMENT.md
    └── SECURITY.md
```

## 🚀 Quick Start

### Option 1: Native Python

```bash
# Clone the repository
git clone https://github.com/appatrous/appa.git
cd appa

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your settings

# Download Bootstrap for offline use
cd static/css
curl -O https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css
cd ../js
curl -O https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js
cd ../..

# Initialize database
flask db init
flask db migrate
flask db upgrade

# Run the application
python app.py
```

Access the application at: http://localhost:5000

**Default credentials**: `admin` / `admin` (⚠️ Change immediately!)

### Option 2: Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 📖 Usage

### Web Interface

1. Navigate to http://localhost:5000
2. Select platform (IOS, NX-OS, ASA, IOS-XR)
3. Fill in configuration parameters
4. Click "Generate Configuration"
5. Download or copy the generated config

### REST API

#### Generate Configuration

```bash
curl -X POST http://localhost:5000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "ios",
    "hostname": "router01",
    "domain_name": "example.com",
    "interfaces": [
      {
        "name": "GigabitEthernet0/0",
        "ip_address": "192.168.1.1",
        "subnet_mask": "255.255.255.0",
        "description": "LAN Interface"
      }
    ],
    "vlans": [
      {"id": 10, "name": "DATA"},
      {"id": 20, "name": "VOICE"}
    ],
    "static_routes": [
      {"network": "0.0.0.0/0", "next_hop": "192.168.1.254"}
    ],
    "ntp_servers": ["pool.ntp.org"],
    "output_format": "cli"
  }'
```

#### Authentication

```bash
# Register user
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "engineer",
    "email": "engineer@example.com",
    "password": "securepass123"
  }'

# Login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "engineer",
    "password": "securepass123"
  }'

# Use token
TOKEN="<your-access-token>"
curl -X GET http://localhost:5000/history/list \
  -H "Authorization: Bearer $TOKEN"
```

#### API Keys

```bash
# Create API key (requires authentication)
curl -X POST http://localhost:5000/auth/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CI/CD Pipeline",
    "description": "Automated config generation",
    "expires_days": 90
  }'

# Use API key
curl -X POST http://localhost:5000/api/v1/generate \
  -H "X-API-Key: cck_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"platform": "ios", "hostname": "router01"}'
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::TestAPIGenerate::test_generate_config_success
```

## 📊 API Endpoints

### Configuration Generation
- `POST /api/v1/generate` - Generate basic configuration
- `POST /api/v1/generate-ccie` - **Generate CCIE-level configuration** ⭐
- `POST /api/v1/validate` - Validate configuration data
- `GET /api/v1/platforms` - List supported platforms
- `GET /api/v1/schema` - Get API schema
- `GET /api/v1/ccie-schema` - Get CCIE API schema
- `GET /api/v1/ccie-examples` - Get CCIE configuration examples

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user
- `POST /auth/change-password` - Change password

### API Keys
- `GET /auth/api-keys` - List API keys
- `POST /auth/api-keys` - Create API key
- `DELETE /auth/api-keys/<id>` - Delete API key

### History
- `GET /history/list` - List configuration history
- `GET /history/<id>` - Get specific configuration
- `GET /history/<id>/download` - Download configuration
- `DELETE /history/<id>` - Delete history entry
- `GET /history/stats` - Get statistics
- `POST /history/compare` - Compare two configurations

### Admin
- `GET /auth/users` - List all users (admin only)
- `DELETE /auth/users/<id>` - Delete user (admin only)
- `POST /history/cleanup` - Cleanup old history (admin only)

## 🔒 Security

### Production Checklist

- [ ] Change default admin password
- [ ] Set secure `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Enable rate limiting
- [ ] Set `FLASK_ENV=production`
- [ ] Review and restrict CORS settings
- [ ] Regular security updates
- [ ] Enable audit logging
- [ ] Configure session timeouts

### Environment Variables

```bash
# Required
SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>
JWT_SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>

# Optional
FLASK_ENV=production
DATABASE_URL=sqlite:///config_history.db
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=86400
HISTORY_RETENTION_DAYS=90
```

## 📚 Documentation

- [CCIE Configuration Guide](docs/CCIE_GUIDE.md) - **Complete protocol coverage** ⭐
- [API Specification](docs/API_SPEC.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Security Hardening](docs/SECURITY.md)

## 🛠️ Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run in development mode
export FLASK_ENV=development
python app.py

# Run tests with coverage
pytest --cov=. --cov-report=html

# Code quality checks
flake8 .
black .
pylint app.py models.py
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

- Flask framework and community
- Jinja2 templating engine
- Bootstrap 5 for UI components
- All contributors and users

## 📞 Support

- 📧 Email: support@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/appatrous/appa/issues)
- 📖 Documentation: [docs/](docs/)

---

**Built with ❤️ for Network Engineers**
