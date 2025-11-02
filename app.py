"""
Cisco Configuration Generator - Main Flask Application
Enterprise-grade configuration generator for Cisco IOS, NX-OS, ASA, and IOS-XR devices.
"""
import os
from flask import Flask, render_template, jsonify
from flask_migrate import Migrate
from dotenv import load_dotenv
from pathlib import Path

from config import config
from models import db
from utils.validators import ValidationError
from utils.auth import AuthError
from utils.renderer import RenderError


# Load environment variables
load_dotenv()

# Initialize Flask-Migrate
migrate = Migrate()


def create_app(config_name=None):
    """
    Flask application factory.

    Args:
        config_name: Configuration name (development, testing, production)

    Returns:
        Flask: Configured Flask application
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from extensions.api import api_bp
    from extensions.history import history_bp
    from extensions.auth_routes import auth_bp
    from extensions.ccie_api import ccie_api_bp

    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(ccie_api_bp, url_prefix='/api/v1')
    app.register_blueprint(history_bp, url_prefix='/history')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Register error handlers
    register_error_handlers(app)

    # Register main routes
    register_routes(app)

    # Create database tables
    with app.app_context():
        db.create_all()
        create_default_user()

    return app


def create_default_user():
    """Create default admin user if none exists."""
    from models import User

    if User.query.count() == 0:
        admin = User(
            username='admin',
            email='admin@localhost',
            is_admin=True
        )
        admin.set_password('admin')  # Change this in production!

        db.session.add(admin)
        db.session.commit()

        print("\n" + "=" * 60)
        print("DEFAULT ADMIN USER CREATED")
        print("=" * 60)
        print("Username: admin")
        print("Password: admin")
        print("\n⚠️  IMPORTANT: Change this password immediately!")
        print("=" * 60 + "\n")


def register_routes(app):
    """Register main application routes."""

    @app.route('/')
    def index():
        """Main page with configuration generator UI."""
        return render_template('index.html',
                               platforms=app.config['SUPPORTED_PLATFORMS'],
                               formats=app.config['OUTPUT_FORMATS'])

    @app.route('/health')
    def health():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'service': 'Cisco Configuration Generator',
            'version': '1.0.0'
        })

    @app.route('/api')
    def api_info():
        """API information endpoint."""
        return jsonify({
            'name': 'Cisco Configuration Generator API',
            'version': '1.0.0',
            'endpoints': {
                'authentication': '/auth',
                'generate_config': '/api/v1/generate',
                'history': '/history',
                'health': '/health'
            },
            'supported_platforms': app.config['SUPPORTED_PLATFORMS'],
            'output_formats': app.config['OUTPUT_FORMATS']
        })


def register_error_handlers(app):
    """Register error handlers."""

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle validation errors."""
        return jsonify({
            'error': 'Validation Error',
            'message': str(error)
        }), 400

    @app.errorhandler(AuthError)
    def handle_auth_error(error):
        """Handle authentication errors."""
        return jsonify({
            'error': 'Authentication Error',
            'message': error.message
        }), error.status_code

    @app.errorhandler(RenderError)
    def handle_render_error(error):
        """Handle rendering errors."""
        return jsonify({
            'error': 'Rendering Error',
            'message': str(error)
        }), 500

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        db.session.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500

    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle file too large errors."""
        return jsonify({
            'error': 'Payload Too Large',
            'message': 'Request payload exceeds maximum allowed size'
        }), 413


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
