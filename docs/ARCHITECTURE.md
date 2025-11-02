# Architecture Overview

## System Design

The Cisco Configuration Generator follows a modular, enterprise-grade architecture designed for maintainability, security, and offline operation.

## Design Principles

1. **Separation of Concerns**: Clear boundaries between presentation, business logic, and data layers
2. **Modularity**: Blueprint-based organization for easy extension
3. **Offline-First**: No external dependencies or CDN requirements
4. **Security by Default**: Authentication, validation, and rate limiting built-in
5. **Testability**: Comprehensive test coverage with pytest

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  ┌─────────────────┐              ┌─────────────────┐       │
│  │   Web Browser   │              │   API Client    │       │
│  │  (Bootstrap 5)  │              │  (curl/Python)  │       │
│  └─────────────────┘              └─────────────────┘       │
└────────────────┬─────────────────────────┬──────────────────┘
                 │                         │
                 ▼                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐        │
│  │ Web Routes  │  │  API v1     │  │ Auth Routes  │        │
│  │ (index.html)│  │ (REST API)  │  │   (JWT)      │        │
│  └─────────────┘  └─────────────┘  └──────────────┘        │
└────────────────┬─────────────────────────┬──────────────────┘
                 │                         │
                 ▼                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Validators  │  │   Renderer   │  │ Auth Manager │      │
│  │ (IP, VLAN,   │  │  (Jinja2)    │  │ (JWT, Keys)  │      │
│  │  Routes)     │  └──────────────┘  └──────────────┘      │
│  └──────────────┘                                           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                        Data Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Models    │  │   Database   │  │  Templates   │      │
│  │ (SQLAlchemy) │  │  (SQLite)    │  │  (Jinja2)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Flask Application Factory (`app.py`)

**Purpose**: Initialize and configure the Flask application

**Key Features**:
- Environment-based configuration
- Blueprint registration
- Error handler registration
- Database initialization
- Default user creation

**Pattern**: Factory Pattern

```python
def create_app(config_name=None):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(history_bp)

    return app
```

### 2. Configuration Management (`config.py`)

**Purpose**: Manage environment-specific settings

**Environments**:
- Development: Debug enabled, verbose logging
- Testing: In-memory database, CSRF disabled
- Production: Secure defaults, file logging

### 3. Database Models (`models.py`)

**Purpose**: Define data structures

**Models**:
- `User`: Authentication and authorization
- `ConfigHistory`: Configuration tracking
- `APIKey`: Programmatic access

**ORM**: SQLAlchemy

### 4. Blueprints (`extensions/`)

#### API Blueprint (`api.py`)
- Configuration generation
- Validation
- Schema documentation

#### Authentication Blueprint (`auth_routes.py`)
- User registration/login
- JWT token management
- API key CRUD
- User management (admin)

#### History Blueprint (`history.py`)
- Configuration history listing
- Configuration retrieval
- Download functionality
- Statistics and comparison

### 5. Utilities (`utils/`)

#### Validators (`validators.py`)
- Network parameter validation
- IP address validation
- VLAN ID validation
- Hostname validation
- OSPF parameter validation

#### Authentication (`auth.py`)
- JWT token generation/validation
- API key management
- Decorators: `@token_required`, `@api_key_required`, `@admin_required`

#### Renderer (`renderer.py`)
- Jinja2 template rendering
- Multi-format output (CLI, JSON, YAML)
- Template management

### 6. Templates (`templates/`)

#### Platform Templates
- `ios_config.j2`: Cisco IOS
- `nxos_config.j2`: Cisco NX-OS
- `asa_config.j2`: Cisco ASA
- `iosxr_config.j2`: Cisco IOS-XR

#### Web Template
- `index.html`: Bootstrap 5 SPA

## Data Flow

### Configuration Generation Flow

```
1. User Request
   ↓
2. Authentication Middleware
   ↓
3. Input Validation (Marshmallow)
   ↓
4. Custom Validation (validators.py)
   ↓
5. Template Rendering (renderer.py)
   ↓
6. History Storage (models.py)
   ↓
7. Response to User
```

### Authentication Flow

```
1. Login Request
   ↓
2. User Lookup (database)
   ↓
3. Password Verification
   ↓
4. JWT Token Generation
   ↓
5. Token Return to Client
   ↓
6. Client Stores Token
   ↓
7. Subsequent Requests Include Token
   ↓
8. Token Validation Middleware
```

## Security Architecture

### Authentication Layers

1. **JWT Tokens**: Short-lived access tokens (1 hour default)
2. **Refresh Tokens**: Long-lived refresh tokens (24 hours default)
3. **API Keys**: Permanent keys for programmatic access

### Authorization

- Role-based access control (admin vs. regular user)
- Decorator-based enforcement
- Resource ownership validation

### Input Validation

1. **Schema Validation**: Marshmallow schemas
2. **Network Validation**: Custom validators for network parameters
3. **SQL Injection Protection**: SQLAlchemy parameterized queries
4. **XSS Protection**: Jinja2 auto-escaping

### Rate Limiting

- IP-based rate limiting
- Configurable limits per endpoint
- Memory or Redis backend

## Template System

### Jinja2 Features Used

- **Template Inheritance**: Base templates for code reuse
- **Macros**: Reusable configuration blocks
- **Filters**: Custom filters for formatting
- **Control Structures**: Conditionals and loops

### Template Organization

```
templates/
├── base.j2              # Base layout
├── index.html           # Web interface
├── ios_config.j2        # IOS template
├── nxos_config.j2       # NX-OS template
├── asa_config.j2        # ASA template
└── iosxr_config.j2      # IOS-XR template
```

## Database Schema

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);

-- Config history table
CREATE TABLE config_history (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    platform VARCHAR(20) NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    config_data TEXT NOT NULL,
    generated_config TEXT NOT NULL,
    output_format VARCHAR(20) DEFAULT 'cli',
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    version VARCHAR(20),
    tags VARCHAR(255)
);

-- API keys table
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used DATETIME,
    expires_at DATETIME
);
```

## Deployment Architecture

### Native Deployment

```
┌─────────────────┐
│   Nginx/Apache  │ ← Reverse Proxy
│   (Optional)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Gunicorn      │ ← WSGI Server
│   4 Workers     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Flask App     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   SQLite DB     │
└─────────────────┘
```

### Docker Deployment

```
┌─────────────────────────────────┐
│      Docker Container           │
│  ┌──────────────────────────┐   │
│  │   Gunicorn + Flask       │   │
│  └──────────┬───────────────┘   │
│             │                   │
│             ▼                   │
│  ┌──────────────────────────┐   │
│  │  Volume: /app/instance   │   │
│  │  (SQLite DB)             │   │
│  └──────────────────────────┘   │
└─────────────────────────────────┘
```

## Extension Points

### Adding New Platforms

1. Create template: `templates/newplatform_config.j2`
2. Update `SUPPORTED_PLATFORMS` in config
3. Add platform-specific validation if needed
4. Add tests

### Adding New Features

1. Create new blueprint in `extensions/`
2. Register blueprint in `app.py`
3. Add models if needed
4. Write tests
5. Update documentation

### Custom Validators

1. Add validator to `utils/validators.py`
2. Integrate into `validate_config_data()`
3. Add unit tests

## Performance Considerations

- **Template Caching**: Jinja2 templates are compiled and cached
- **Database Indexing**: Key columns indexed for fast queries
- **Connection Pooling**: SQLAlchemy connection pool
- **Static Asset Caching**: Browser caching headers

## Monitoring and Logging

- Application logs: `logs/cisco_config_generator.log`
- Rotation: 10MB per file, 10 backups
- Levels: INFO (production), DEBUG (development)
- Structured logging for easier parsing
