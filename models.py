"""
Database models for configuration history and user management.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)

    # Relationships
    configurations = db.relationship('ConfigHistory', backref='user', lazy='dynamic',
                                     cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against hash."""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    def __repr__(self):
        return f'<User {self.username}>'


class ConfigHistory(db.Model):
    """Configuration history model."""
    __tablename__ = 'config_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    platform = db.Column(db.String(20), nullable=False, index=True)
    hostname = db.Column(db.String(255), nullable=False)
    config_data = db.Column(db.Text, nullable=False)  # JSON string
    generated_config = db.Column(db.Text, nullable=False)
    output_format = db.Column(db.String(20), default='cli', nullable=False)
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Metadata
    version = db.Column(db.String(20))
    tags = db.Column(db.String(255))  # Comma-separated tags

    def get_config_data(self):
        """Parse JSON config data."""
        try:
            return json.loads(self.config_data)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_config_data(self, data):
        """Set config data as JSON string."""
        self.config_data = json.dumps(data)

    def to_dict(self, include_config=False):
        """Convert to dictionary."""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'anonymous',
            'platform': self.platform,
            'hostname': self.hostname,
            'output_format': self.output_format,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'version': self.version,
            'tags': self.tags.split(',') if self.tags else []
        }

        if include_config:
            result['config_data'] = self.get_config_data()
            result['generated_config'] = self.generated_config

        return result

    def __repr__(self):
        return f'<ConfigHistory {self.id} - {self.platform} - {self.hostname}>'


class APIKey(db.Model):
    """API Key model for programmatic access."""
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    key_hash = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)

    # Relationships
    user = db.relationship('User', backref=db.backref('api_keys', lazy='dynamic'))

    def set_key(self, key):
        """Hash and set API key."""
        self.key_hash = generate_password_hash(key)

    def check_key(self, key):
        """Verify API key against hash."""
        return check_password_hash(self.key_hash, key)

    def update_last_used(self):
        """Update last used timestamp."""
        self.last_used = datetime.utcnow()
        db.session.commit()

    def is_expired(self):
        """Check if API key is expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

    def __repr__(self):
        return f'<APIKey {self.name}>'


class AuditLog(db.Model):
    """Audit log model for security and compliance tracking."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False, index=True)  # login, logout, create, update, delete, etc.
    resource_type = db.Column(db.String(50))  # user, config, api_key, etc.
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON string with additional details
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(255))
    status = db.Column(db.String(20))  # success, failure, error
    severity = db.Column(db.String(20), default='info')  # info, warning, error, critical

    # Relationships
    user = db.relationship('User', backref=db.backref('audit_logs', lazy='dynamic'))

    def get_details(self):
        """Parse JSON details."""
        try:
            return json.loads(self.details) if self.details else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_details(self, data):
        """Set details as JSON string."""
        self.details = json.dumps(data) if data else None

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'anonymous',
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.get_details(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status': self.status,
            'severity': self.severity
        }

    def __repr__(self):
        return f'<AuditLog {self.id} - {self.action} - {self.status}>'
