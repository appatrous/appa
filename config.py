"""
Application configuration module.
Provides environment-specific settings and secure defaults.
"""
import os
from datetime import timedelta
from pathlib import Path


class Config:
    """Base configuration with secure defaults."""

    # Base directory
    BASE_DIR = Path(__file__).parent.absolute()

    # Flask Core
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{BASE_DIR}/config_history.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 86400))
    )
    JWT_ALGORITHM = 'HS256'

    # Security
    WTF_CSRF_ENABLED = os.environ.get('CSRF_ENABLED', 'True') == 'True'
    WTF_CSRF_TIME_LIMIT = None
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Rate Limiting
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'True') == 'True'
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_DEFAULT = "100/hour"

    # File Upload
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    UPLOAD_FOLDER = BASE_DIR / os.environ.get('UPLOAD_FOLDER', 'uploads')

    # Application Settings
    HISTORY_RETENTION_DAYS = int(os.environ.get('HISTORY_RETENTION_DAYS', 90))
    SUPPORTED_PLATFORMS = ['ios', 'nxos', 'asa', 'iosxr']
    OUTPUT_FORMATS = ['cli', 'json', 'yaml']

    # Template Directories
    TEMPLATE_DIR = BASE_DIR / 'templates'
    CONFIG_TEMPLATE_DIR = BASE_DIR / 'config_templates'

    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False

    @classmethod
    def init_app(cls, app):
        """Production-specific initialization."""
        Config.init_app(app)

        # Log to syslog or external logging service
        import logging
        from logging.handlers import RotatingFileHandler

        if not app.debug and not app.testing:
            # Create logs directory
            log_dir = cls.BASE_DIR / 'logs'
            os.makedirs(log_dir, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_dir / 'cisco_config_generator.log',
                maxBytes=10485760,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Cisco Config Generator startup')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
